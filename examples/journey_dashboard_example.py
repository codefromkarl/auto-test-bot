#!/usr/bin/env python3
"""
用户旅程看板使用示例
演示如何使用 journey_dashboard 和 visual_reporter 生成可视化测试报告
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reporting.journey_dashboard import JourneyDashboard, StepStatus, IssueSeverity
from src.reporting.visual_reporter import VisualReporter


def simulate_test_execution():
    """
    模拟测试执行过程
    """
    # 配置
    config = {
        'output_dir': 'reports/dashboard',
        'screenshot_dir': 'test_data/screenshots',
        'artifact_dir': 'test_data/artifacts'
    }

    # 初始化看板
    dashboard = JourneyDashboard(config)
    reporter = VisualReporter(config)

    # 开始测试旅程
    journey_id = dashboard.start_journey("闹海AI创建视频测试")
    print(f"开始测试旅程: {journey_id}")

    # 步骤1: 打开网站
    print("\n执行步骤1: 打开网站")
    step1_id = dashboard.add_step(
        step_name="open_site",
        description="访问闹海AI平台首页",
        screenshots=["test_data/screenshots/homepage.png"],
        metrics={"page_load_time": 2.3, "dom_ready": 2.1}
    )
    time.sleep(1)  # 模拟执行时间
    dashboard.complete_step(step1_id, success=True)

    # 步骤2: 导航到AI创建页面
    print("执行步骤2: 导航到AI创建页面")
    step2_id = dashboard.add_step(
        step_name="navigate_to_ai_create",
        description="点击导航栏进入AI创建功能",
        screenshots=["test_data/screenshots/ai_create_page.png"],
        metrics={"navigation_time": 1.5}
    )
    time.sleep(0.5)
    dashboard.complete_step(step2_id, success=True)

    # 步骤3: 输入剧本
    print("执行步骤3: 输入剧本内容")
    step3_id = dashboard.add_step(
        step_name="input_script",
        description="在文本框中输入测试剧本",
        screenshots=["test_data/screenshots/script_input.png"],
        metrics={"input_length": 256, "input_time": 15.2}
    )
    time.sleep(0.8)
    dashboard.complete_step(step3_id, success=True)

    # 步骤4: 生成图片（模拟有警告）
    print("执行步骤4: 生成角色图片")
    step4_id = dashboard.add_step(
        step_name="generate_image",
        description="根据剧本生成角色图片",
        screenshots=[
            "test_data/screenshots/generating.png",
            "test_data/screenshots/generated_image.png"
        ],
        artifacts=[
            {
                "name": "角色图片1.png",
                "path": "test_data/artifacts/character_1.png",
                "type": "image"
            },
            {
                "name": "角色图片2.png",
                "path": "test_data/artifacts/character_2.png",
                "type": "image"
            }
        ],
        metrics={"generation_time": 45.6, "retry_count": 1}
    )
    time.sleep(1.2)
    # 添加一个问题
    issues = [
        {
            "type": "warning",
            "message": "图片生成时间较长，超过预期30秒",
            "severity": IssueSeverity.MEDIUM.value,
            "timestamp": datetime.now().isoformat()
        }
    ]
    dashboard.complete_step(step4_id, success=True, issues=issues)

    # 步骤5: 生成视频（模拟失败）
    print("执行步骤5: 生成视频")
    step5_id = dashboard.add_step(
        step_name="generate_video",
        description="将图片合成为视频",
        screenshots=["test_data/screenshots/video_generation_failed.png"],
        metrics={"attempt_time": 120.0}
    )
    time.sleep(0.5)
    dashboard.complete_step(
        step5_id,
        success=False,
        error_message="视频生成失败: 服务端返回500错误",
        issues=[
            {
                "type": "error",
                "message": "视频合成服务不可用",
                "severity": IssueSeverity.HIGH.value,
                "timestamp": datetime.now().isoformat()
            }
        ]
    )

    # 步骤6: 验证结果
    print("执行步骤6: 验证结果")
    step6_id = dashboard.add_step(
        step_name="validate",
        description="验证最终产出",
        metrics={"validation_time": 2.0}
    )
    time.sleep(0.3)
    dashboard.complete_step(
        step6_id,
        success=False,
        error_message="关键步骤失败，无法完成验证"
    )

    # 结束旅程并生成看板数据
    print("\n生成看板数据...")
    dashboard_data = dashboard.end_journey()

    # 保存看板数据
    saved_files = dashboard.save_dashboard(dashboard_data)
    print(f"看板数据已保存到: {saved_files}")

    # 生成HTML报告
    print("生成HTML可视化报告...")
    html_path = reporter.generate_html_report(dashboard_data)
    print(f"HTML报告已生成: {html_path}")

    # 打印统计信息
    print("\n=== 测试统计 ===")
    stats = dashboard_data['statistics']
    print(f"总步骤数: {stats['total_steps']}")
    print(f"成功步骤: {stats['successful_steps']}")
    print(f"失败步骤: {stats['failed_steps']}")
    print(f"成功率: {stats['success_rate']:.1f}%")
    print(f"总问题数: {stats['total_issues']}")
    print(f"总截图数: {stats['total_screenshots']}")

    # 打印体验评分
    if dashboard_data.get('experience_score'):
        print("\n=== 体验评分 ===")
        score = dashboard_data['experience_score']
        print(f"综合评分: {score['overall_score']:.1f}分")
        print(f"可用性: {score['usability_score']:.1f}分")
        print(f"性能: {score['performance_score']:.1f}分")
        print(f"可靠性: {score['reliability_score']:.1f}分")
        print(f"满意度: {score['satisfaction_score']:.1f}分")

    # 打印问题汇总
    if dashboard_data.get('issues_summary', {}).get('total_issues', 0) > 0:
        print("\n=== 问题汇总 ===")
        issues = dashboard_data['issues_summary']
        print(f"总问题数: {issues['total_issues']}")
        print("严重程度分布:")
        for severity, count in issues['severity_breakdown'].items():
            print(f"  {severity}: {count}个")

    return dashboard_data, html_path


def create_test_data():
    """创建测试数据目录和示例文件"""
    import base64

    # 创建目录
    os.makedirs("test_data/screenshots", exist_ok=True)
    os.makedirs("test_data/artifacts", exist_ok=True)
    os.makedirs("reports/dashboard", exist_ok=True)

    # 创建一个简单的图片占位符（1x1像素的PNG）
    placeholder_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )

    # 创建示例截图文件
    screenshot_files = [
        "test_data/screenshots/homepage.png",
        "test_data/screenshots/ai_create_page.png",
        "test_data/screenshots/script_input.png",
        "test_data/screenshots/generating.png",
        "test_data/screenshots/generated_image.png",
        "test_data/screenshots/video_generation_failed.png"
    ]

    for file_path in screenshot_files:
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(placeholder_png)

    # 创建示例产物文件
    artifact_files = [
        "test_data/artifacts/character_1.png",
        "test_data/artifacts/character_2.png"
    ]

    for file_path in artifact_files:
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(placeholder_png)

    print("测试数据已创建")


def main():
    """主函数"""
    print("=== 用户旅程看板示例 ===\n")

    # 创建测试数据
    create_test_data()

    # 模拟测试执行
    try:
        dashboard_data, html_path = simulate_test_execution()

        print("\n=== 完成 ===")
        print(f"请打开浏览器查看报告: {html_path}")
        print("\n功能特性:")
        print("✅ 时间轴式步骤展示")
        print("✅ 截图预览功能")
        print("✅ 体验评分系统")
        print("✅ 问题标记和分类")
        print("✅ 交互式图表")
        print("✅ 响应式设计")
        print("✅ 打印和导出功能")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()