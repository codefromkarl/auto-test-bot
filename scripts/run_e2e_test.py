#!/usr/bin/env python3
"""
E2E黄金路径测试执行脚本

执行闹海系统完整的端到端测试，验证从剧本创建到视频导出的完整用户旅程。

说明：
- 本脚本是 `scripts/run_workflow_test.py` 的 E2E 专用封装，增加了：
  - 黄金路径工作流的结构完整性校验（7阶段）
  - 覆盖度评估（静态）
  - 统一的 E2E 汇总 JSON 报告
- 支持 `--dry-run`：只做静态校验，不启动浏览器
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 重要：优先插入 src，避免误导入同名第三方包/旧模块
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
root_path = str(PROJECT_ROOT)
if root_path not in sys.path:
    sys.path.insert(1, root_path)

from utils import ConfigLoader, setup_logging
from models import Workflow
from executor import WorkflowExecutor
from browser import BrowserManager
from reporter import DecisionReporter

from e2e.golden_path_validator import (
    evaluate_golden_path_coverage,
    validate_golden_path_workflow,
)


class E2ETestRunner:
    """E2E测试运行器"""

    def __init__(self, config_path: str = "config/config.yaml", report_dir: str = "reports/e2e"):
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.config.setdefault("reporting", {})
        self.config["reporting"]["output_dir"] = str(self.report_dir)
        setup_logging(self.config.get("logging", {}) or {})

    async def run_e2e_test(self, workflow_file: str, *, verbose: bool = False, dry_run: bool = False) -> bool:
        print("🚀 开始E2E黄金路径测试（Golden Path）")
        print(f"📋 工作流文件: {workflow_file}")
        print(f"⚙️ 配置文件: {self.config_loader.config_path}")
        print(f"📁 报告目录: {self.report_dir}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            print(f"❌ 工作流文件不存在: {workflow_file}")
            return False

        workflow = Workflow.from_yaml(workflow_path.read_text(encoding="utf-8"))
        validation_errors = validate_golden_path_workflow(workflow)
        coverage = evaluate_golden_path_coverage(workflow)

        if validation_errors:
            print("❌ 黄金路径工作流结构校验失败：")
            for err in validation_errors:
                print(f"  - {err}")
            self._write_summary_report(
                workflow_path=workflow_path,
                workflow_name=workflow.name,
                validation_errors=validation_errors,
                coverage=coverage,
                execution_result=None,
                dry_run=dry_run,
            )
            return False

        if dry_run:
            print("✅ 干运行校验通过（未启动浏览器）")
            self._write_summary_report(
                workflow_path=workflow_path,
                workflow_name=workflow.name,
                validation_errors=[],
                coverage=coverage,
                execution_result=None,
                dry_run=True,
            )
            return True

        try:
            browser_manager = BrowserManager(self.config)
            ok = await browser_manager.initialize()
            if not ok:
                print("❌ 浏览器初始化失败")
                return False

            executor = WorkflowExecutor(self.config, browser_manager, mcp_observer=None)
            result = await executor.execute_workflow(workflow)

            reporter = DecisionReporter(self.config)
            report = reporter.generate_report(result)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_prefix = f"e2e_golden_path_{timestamp}"
            saved_files = reporter.save_report(report, filename_prefix=filename_prefix)

            self._write_summary_report(
                workflow_path=workflow_path,
                workflow_name=workflow.name,
                validation_errors=[],
                coverage=coverage,
                execution_result=result,
                dry_run=False,
                decision_report_files=saved_files,
            )

            if verbose:
                self._print_detailed_result(result)

            return bool(result.get("overall_success", False))

        except Exception as e:
            print(f"❌ E2E测试执行失败: {str(e)}")
            if verbose:
                import traceback

                traceback.print_exc()
            return False

    def _write_summary_report(
        self,
        *,
        workflow_path: Path,
        workflow_name: str,
        validation_errors: list[str],
        coverage: dict,
        execution_result: dict | None,
        dry_run: bool,
        decision_report_files: dict | None = None,
    ) -> Path:
        report_data: dict = {
            "test_type": "E2E_GoldenPath",
            "workflow_file": str(workflow_path),
            "workflow_name": workflow_name,
            "config_file": str(self.config_loader.config_path),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dry_run": bool(dry_run),
            "validation": {
                "ok": len(validation_errors) == 0,
                "errors": list(validation_errors),
            },
            "coverage": coverage,
            "execution": None,
            "artifacts": {
                "decision_report_files": decision_report_files or {},
            },
        }

        if execution_result is not None:
            final_context = execution_result.get("final_context") or {}
            screenshots = (final_context.get("data") or {}).get("screenshots", [])
            report_data["execution"] = {
                "overall_success": bool(execution_result.get("overall_success", False)),
                "duration_seconds": execution_result.get("duration_seconds"),
                "phase_results": execution_result.get("phase_results", []),
                "error_history": execution_result.get("error_history", []),
                "screenshots": screenshots if isinstance(screenshots, list) else [],
            }

        out_path = self.report_dir / f"golden_path_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"📊 E2E汇总报告已保存: {out_path}")
        return out_path

    def _print_detailed_result(self, result: dict) -> None:
        print("\n📊 详细测试结果:")
        print(f"✅ 总执行时间: {float(result.get('duration_seconds') or 0):.2f}秒")
        phases = result.get("phase_results", []) or []
        print(f"📈 成功阶段: {len([p for p in phases if p.get('success')])}/{len(phases)}")

        for phase_result in phases:
            status = "✅" if phase_result.get("success") else "❌"
            print(f"{status} {phase_result.get('name')}: steps={phase_result.get('steps_executed', [])}")

        if result.get("error_history"):
            print("\n❌ 错误信息:")
            for error in result.get("error_history", []) or []:
                print(f"  - {error.get('phase')}/{error.get('step')}: {error.get('error')}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="执行E2E黄金路径测试")
    parser.add_argument(
        "--workflow",
        default="workflows/e2e/naohai_E2E_GoldenPath.yaml",
        help="E2E工作流文件路径",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--report-dir",
        default="reports/e2e",
        help="报告输出目录（E2E汇总报告 + DecisionReporter 产物）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅做静态校验（不启动浏览器）",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细输出",
    )

    args = parser.parse_args()

    runner = E2ETestRunner(args.config, report_dir=args.report_dir)
    success = await runner.run_e2e_test(args.workflow, verbose=args.verbose, dry_run=args.dry_run)

    if success:
        print("\n🎉 E2E黄金路径测试通过！")
        raise SystemExit(0)
    print("\n❌ E2E黄金路径测试失败！")
    raise SystemExit(1)


if __name__ == "__main__":
    import asyncio

    raise SystemExit(asyncio.run(main()))

