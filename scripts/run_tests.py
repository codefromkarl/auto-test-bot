#!/usr/bin/env python3
"""
统一测试入口脚本

支持按类型、标签运行不同测试套件，
自动收集报告并保存到标准位置。
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def setup_parser():
    """设置命令行参数解析"""
    parser = argparse.ArgumentParser(
        description="Auto-Test-Bot 统一测试入口",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # 测试类型
    parser.add_argument(
        "--type", "-t",
        choices=["unit", "integration", "e2e", "all"],
        default="all",
        help="测试类型: unit(单元), integration(集成), e2e(端到端), all(全部)"
    )

    # 测试标签
    parser.add_argument(
        "--tag", "-k",
        type=str,
        help="运行特定标签的测试 (pytest -k)"
    )

    # 输出格式
    parser.add_argument(
        "--format", "-f",
        choices=["json", "html", "text"],
        default="text",
        help="报告输出格式"
    )

    # 输出目录
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="test_artifacts",
        help="测试产物输出目录"
    )

    # 报告类型
    parser.add_argument(
        "--report-type", "-r",
        choices=["test", "evidence", "summary"],
        default="test",
        help="报告类型: test(测试报告), evidence(证据收集), summary(摘要报告)"
    )

    # 调试模式
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    # 失败时停止
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="遇到失败时停止"
    )

    return parser


def get_test_command(
    test_type: str,
    tag: str = None,
    output_dir: str = "test_artifacts",
    report_type: str = "test",
    *,
    failfast: bool = False,
    verbose: bool = False,
) -> str:
    """构建 pytest 命令"""

    # 基础参数
    cmd = [
        sys.executable, "-m", "pytest",
        "-v" if (verbose or tag) else "-q",
        "--tb=short",
    ]

    # 根据报告类型设置输出
    if report_type == "test":
        # 标准测试报告：优先使用 pytest 内置的 JUnit XML（不依赖第三方插件）
        cmd.extend([
            f"--junitxml={output_dir}/xml/junit.xml"
        ])
    elif report_type == "evidence":
        # 证据收集：不强依赖插件（截图/JSON 由执行引擎或外部机制提供）
        cmd.extend([
            f"--junitxml={output_dir}/xml/junit.xml"
        ])
    elif report_type == "summary":
        # 摘要报告：仅统计数据（由本脚本解析 pytest 输出生成 JSON）
        pass
    else:
        raise ValueError(f"Unknown report type: {report_type}")

    # 测试类型参数
    if test_type == "unit":
        cmd.extend(["tests/unit/"])
    elif test_type == "integration":
        cmd.extend(["tests/integration/"])
    elif test_type == "e2e":
        cmd.extend(["tests/e2e/"])
    elif test_type == "all":
        cmd.extend(["tests/"])
    else:
        raise ValueError(f"Unknown test type: {test_type}")

    # 标签过滤
    if tag:
        cmd.extend(["-k", tag])

    # 失败时停止
    if failfast:
        cmd.append("-x")

    return " ".join(cmd)


def ensure_output_directories(output_dir: str, report_type: str = "test") -> str:
    """确保输出目录存在"""
    output_path = Path(output_dir)

    # 根据报告类型创建目录结构
    if report_type == "test":
        # 标准测试报告：JUnit XML + 辅助日志/摘要
        for subdir in ["xml", "json", "logs"]:
            (output_path / subdir).mkdir(parents=True, exist_ok=True)
    elif report_type == "evidence":
        # 证据收集：不强依赖 pytest 插件，目录用于承载外部证据/摘要
        for subdir in ["xml", "json", "screenshots", "logs"]:
            (output_path / subdir).mkdir(parents=True, exist_ok=True)
    elif report_type == "summary":
        # 摘要报告：1个目录
        for subdir in ["json", "logs"]:
            (output_path / subdir).mkdir(parents=True, exist_ok=True)
    else:
        # 默认创建基础目录
        for subdir in ["reports", "screenshots", "logs"]:
            (output_path / subdir).mkdir(parents=True, exist_ok=True)

    return output_path


def generate_test_summary(results: dict, output_dir: str, report_type: str):
    """生成测试摘要"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {
        "timestamp": timestamp,
        "total": results.get("total", 0),
        "passed": results.get("passed", 0),
        "failed": results.get("failed", 0),
        "skipped": results.get("skipped", 0),
        "duration": results.get("duration", 0),
        "test_type": results.get("test_type", "unknown")
    }

    # 保存摘要
    summary_dir = Path(output_dir) / "json"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = summary_dir / f"test_summary_{timestamp}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    return summary_file


def print_summary(summary: dict, verbose: bool = False):
    """打印测试摘要"""
    if verbose:
        print(f"\n📊 测试摘要:")
        print(f"  总数: {summary.get('total', 0)}")
        print(f"  通过: {summary.get('passed', 0)}")
        print(f"  失败: {summary.get('failed', 0)}")
        print(f"  跳过: {summary.get('skipped', 0)}")
        print(f"  耗时: {summary.get('duration', 0):.2f}s")
        print(f"  类型: {summary.get('test_type', 'unknown')}")
    else:
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        total = passed + failed + skipped

        if total > 0:
            status = "✅ 全部通过" if failed == 0 else f"❌ {failed} 个失败"
            extra = f"，跳过 {skipped}" if skipped else ""
            print(f"测试完成: {passed}/{total} {status}{extra}")
        else:
            print("⚠️ 没有测试被执行")


def run_tests(args) -> bool:
    """运行测试主函数"""
    # 确保输出目录
    ensure_output_directories(args.output_dir, args.report_type)

    # 构建命令
    cmd = get_test_command(
        args.type,
        args.tag,
        args.output_dir,
        args.report_type,
        failfast=bool(args.failfast),
        verbose=bool(args.verbose),
    )

    print(f"🚀 执行测试: {cmd}")

    # 运行测试
    import subprocess
    start_time = datetime.now()

    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            cwd=project_root
        )

        # 简单解析结果
        output = result.stdout
        error_output = result.stderr

        if result.returncode != 0:
            print(f"❌ 测试执行失败: {error_output}")
            return False

        # 解析 pytest 汇总行（best-effort）
        import re
        passed = int(re.search(r"(\d+)\s+passed", output).group(1)) if re.search(r"(\d+)\s+passed", output) else 0
        failed = int(re.search(r"(\d+)\s+failed", output).group(1)) if re.search(r"(\d+)\s+failed", output) else 0
        skipped = int(re.search(r"(\d+)\s+skipped", output).group(1)) if re.search(r"(\d+)\s+skipped", output) else 0

        # 生成摘要
        duration = (datetime.now() - start_time).total_seconds()
        summary_data = {
            "test_type": args.type,
            "timestamp": start_time.isoformat(),
            "duration": duration,
            "output_dir": args.output_dir,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
        }

        summary_file = generate_test_summary(summary_data, args.output_dir, args.report_type)
        print_summary(summary_data, args.verbose)

        print(f"📁 报告已保存到: {summary_file}")
        return True

    except Exception as e:
        print(f"❌ 测试执行异常: {e}")
        return False


def main():
    """主函数"""
    parser = setup_parser()
    args = parser.parse_args()

    # 显示信息
    if args.verbose:
        print(f"📋 测试配置:")
        print(f"  类型: {args.type}")
        print(f"  标签: {args.tag or '全部'}")
        print(f"  格式: {args.format}")
        print(f"  输出: {args.output_dir}")
        print(f"  快速失败: {args.failfast}")

    # 运行测试
    success = run_tests(args)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
