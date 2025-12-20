#!/usr/bin/env python3
"""
工作流测试执行脚本 - 统一的测试执行入口
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import asyncio
import os

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


async def run(args) -> int:
    parser = argparse.ArgumentParser(description='执行NowHi网站工作流测试')
    parser.add_argument('--workflow', required=True, help='工作流配置文件路径')
    parser.add_argument('--config', default='config/config.yaml', help='测试配置文件路径')
    parser.add_argument('--report-dir', default='test_reports', help='测试报告输出目录')
    parser.add_argument('--dry-run', action='store_true', help='仅验证配置，不执行测试')

    if args is None:
        args = parser.parse_args()

    # 验证工作流文件存在
    if not Path(args.workflow).exists():
        print(f"❌ 工作流文件不存在: {args.workflow}")
        return 1

    # 验证配置文件存在
    if not Path(args.config).exists():
        print(f"❌ 配置文件不存在: {args.config}")
        return 1

    # 创建报告目录
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    # 加载配置
    config_loader = ConfigLoader(args.config)
    config = config_loader.load_config()
    config.setdefault('reporting', {})
    config['reporting']['output_dir'] = str(report_dir)
    setup_logging(config.get('logging', {}))

    if not args.dry_run:
        print(f"🚀 执行工作流测试: {Path(args.workflow).stem}")
        print(f"📁 报告将保存到: {report_dir}")
        print(f"⚙️ 工作流文件: {args.workflow}")
        print(f"⚙️ 配置文件: {args.config}")

        with open(args.workflow, 'r', encoding='utf-8') as f:
            workflow = Workflow.from_yaml(f.read())

        browser_manager = BrowserManager(config)
        ok = await browser_manager.initialize()
        if not ok:
            print("❌ 浏览器初始化失败")
            return 1

        executor = WorkflowExecutor(config, browser_manager, mcp_observer=None)
        result = await executor.execute_workflow(workflow)

        reporter = DecisionReporter(config)
        report = reporter.generate_report(result)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_prefix = f"workflow_test_{timestamp}"
        saved_files = reporter.save_report(report, filename_prefix=filename_prefix)

        for format_type, filepath in saved_files.items():
            print(f"📄 {format_type.upper()} 报告: {filepath}")

        if result.get('overall_success'):
            print(f"✅ Workflow '{workflow.name}' completed successfully")
            return 0
        else:
            print(f"❌ Workflow '{workflow.name}' failed")
            return 1

    else:
        try:
            with open(args.workflow, 'r', encoding='utf-8') as f:
                Workflow.from_yaml(f.read())
            print("✅ 配置验证通过（干运行模式）")
            return 0
        except Exception as e:
            print(f"❌ 干运行验证失败: {e}")
            return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(None)))
