#!/usr/bin/env python3
"""
Naohai Parallel Test Workflow Launcher
闹海并行测试工作流启动器
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_coordinator import ClaudeWorkflowCoordinator

async def main():
    """启动闹海并行测试工作流"""
    print("🌊 闹海并行测试工作流启动器")
    print("=" * 60)
    print("🤖 分工策略:")
    print("  • Gemini: UI分析、前端测试、页面检查")
    print("  • Codex: 功能测试、逻辑验证、工作流执行")
    print("  • Claude: 协调编排、结果聚合、报告生成")
    print("=" * 60)

    # 检查工作目录
    workspace_dir = Path("workspace")
    if not workspace_dir.exists():
        workspace_dir.mkdir(exist_ok=True)
        print("✅ 创建工作目录: workspace/")

    # 检查配置文件
    config_file = workspace_dir / "parallel_executor_config.yaml"
    if not config_file.exists():
        print("❌ 配置文件不存在: workspace/parallel_executor_config.yaml")
        return 1

    print("📋 加载配置文件...")

    # 创建协调器
    coordinator = ClaudeWorkflowCoordinator(str(config_file))

    print("🚀 启动并行测试工作流...")
    print("=" * 60)

    try:
        # 执行工作流
        final_report = await coordinator.orchestrate_workflow()

        print("\n" + "=" * 60)
        print("✅ 闹海测试工作流执行完成!")
        print("=" * 60)

        # 显示执行摘要
        summary = final_report["execution_summary"]
        print(f"📊 执行统计:")
        print(f"  • 总任务数: {summary['total_tasks']}")
        print(f"  • 成功任务: {summary['completed_tasks']}")
        print(f"  • 失败任务: {summary['failed_tasks']}")
        print(f"  • 成功率: {summary['success_rate']:.1%}")
        print(f"  • 总耗时: {summary['total_duration']:.2f}秒")

        # 显示质量评估
        quality = final_report["quality_assessment"]
        print(f"\n🎯 质量评估:")
        print(f"  • UI质量分数: {quality['ui_quality_score']:.1%}")
        print(f"  • 功能质量分数: {quality['functional_quality_score']:.1%}")

        # 显示报告位置
        print(f"\n📄 报告文件:")
        print(f"  • JSON报告: workspace/claude_outputs/naohai_final_test_report.json")
        print(f"  • HTML报告: reports/naohai_parallel_test_report.html")

        # 显示改进建议
        if final_report.get("recommendations"):
            print(f"\n💡 改进建议:")
            for i, rec in enumerate(final_report["recommendations"], 1):
                print(f"  {i}. {rec}")

        # 检查是否满足质量门禁
        overall_success = summary['success_rate'] >= 0.8

        if overall_success:
            print(f"\n🎉 测试通过! 质量门禁满足要求。")
            return 0
        else:
            print(f"\n⚠️ 测试未完全通过，成功率低于80%。")
            return 1

    except KeyboardInterrupt:
        print(f"\n⏹️ 用户中断执行")
        return 130

    except Exception as e:
        print(f"\n❌ 工作流执行失败: {str(e)}")
        print(f"📄 详细错误信息: workspace/claude_outputs/error_report.json")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))