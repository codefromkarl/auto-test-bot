#!/usr/bin/env python3
"""
Data-TestId 集成测试脚本

验证完整的 data-testid 集成方案，包括定位器、度量和 CI 门禁。
"""

import sys
import asyncio
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
from locator.metrics_hybrid_locator import MetricsHybridLocator
from reporter.testid_coverage_reporter import TestIdCoverageReporter


class DataTestIdIntegrationTester:
    """Data-TestId 集成测试器"""

    def __init__(self, config_path: str = None):
        """
        初始化测试器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config/data_testid_config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ 无法加载配置文件 {self.config_path}: {e}")
            sys.exit(1)

    async def test_locators(self, page) -> dict:
        """
        测试定位器功能

        Args:
            page: Playwright 页面对象

        Returns:
            dict: 测试结果
        """
        print("🧪 开始测试定位器功能...")

        # 创建度量定位器
        locator = MetricsHybridLocator(page, self.config.get('locators', {}))

        # 确保进入文生图区域（示例页默认隐藏该区域）
        try:
            # 覆盖导航契约（用于 CI 门禁统计）
            await locator.click('nav_ai_create_tab', timeout=3000)
            await locator.click('nav_text_image_tab', timeout=3000)
            await locator.is_visible('prompt_input', timeout=3000)
        except Exception:
            pass

        # 测试场景
        test_scenarios = [
            ('prompt_input', 'fill'),
            ('prompt_textarea', 'exists'),  # 覆盖 prompt-textarea 契约
            ('generate_image_button', 'click'),
            ('loading_indicator', 'wait_for_disappear'),
            ('image_result', 'check_visible'),
            ('generated_image', 'exists'),
            ('generate_video_button', 'click'),
            ('loading_indicator', 'wait_for_disappear'),
            ('video_result', 'check_visible'),
            ('generated_video', 'exists'),
            ('error_message', 'exists')
        ]

        results = {
            'total_tests': len(test_scenarios),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }

        for element_name, action in test_scenarios:
            print(f"  测试 {element_name} ({action})...")

            try:
                if action == 'fill':
                    success = await locator.fill(element_name, '测试提示词内容')
                elif action == 'click':
                    success = await locator.click(element_name, timeout=5000)
                elif action == 'wait_for_disappear':
                    # 先等待元素出现，再等待消失
                    element = await locator.locate(element_name, timeout=3000)
                    success = element is not None
                    if success:
                        success = await locator.wait_for_disappear(element_name, timeout=5000)
                elif action == 'check_visible':
                    success = await locator.is_visible(element_name, timeout=10000)
                elif action == 'exists':
                    element = await locator.locate(element_name, timeout=3000)
                    success = element is not None
                else:
                    success = False

                test_result = {
                    'element': element_name,
                    'action': action,
                    'success': success,
                    'strategy_used': locator.metrics['element_stats'].get(element_name, {}).get('strategy_type', 'unknown')
                }

                results['test_details'].append(test_result)

                if success:
                    results['passed_tests'] += 1
                    print(f"    ✅ 通过 (策略: {test_result['strategy_used']})")
                else:
                    results['failed_tests'] += 1
                    print(f"    ❌ 失败")

            except Exception as e:
                error_result = {
                    'element': element_name,
                    'action': action,
                    'success': False,
                    'error': str(e)
                }
                results['test_details'].append(error_result)
                results['failed_tests'] += 1
                print(f"    ❌ 异常: {str(e)}")

        # 获取定位器度量
        results['locator_metrics'] = locator.get_metrics()
        results['ci_validation'] = locator.validate_ci_gates()

        return results

    async def test_page_navigation(self, page) -> dict:
        """
        测试页面导航功能

        Args:
            page: Playwright 页面对象

        Returns:
            dict: 导航测试结果
        """
        print("🧪 开始测试页面导航...")

        locator = MetricsHybridLocator(page, self.config.get('locators', {}))

        # 导航测试
        navigation_tests = [
            ('nav_ai_create_tab', 'AI创作'),
            ('nav_text_image_tab', '文生图'),
        ]

        results = {
            'total_navigations': len(navigation_tests),
            'successful_navigations': 0,
            'navigation_details': []
        }

        for element_name, target_name in navigation_tests:
            print(f"  尝试导航到 {target_name}...")

            try:
                # 点击导航元素
                success = await locator.click(element_name, timeout=5000)
                if success:
                    await page.wait_for_timeout(2000)  # 等待页面加载
                    print(f"    ✅ 成功点击 {target_name}")
                    results['successful_navigations'] += 1
                else:
                    print(f"    ❌ 点击 {target_name} 失败")

                results['navigation_details'].append({
                    'element': element_name,
                    'target': target_name,
                    'success': success
                })

            except Exception as e:
                print(f"    ❌ 导航异常: {str(e)}")
                results['navigation_details'].append({
                    'element': element_name,
                    'target': target_name,
                    'success': False,
                    'error': str(e)
                })

        return results

    async def run_full_integration_test(self) -> dict:
        """
        运行完整的集成测试

        Returns:
            dict: 完整测试结果
        """
        print("🚀 开始 Data-TestId 完整集成测试")
        print("=" * 50)

        test_results = {
            'test_session': {
                'started_at': datetime.now().isoformat(),
                'config_file': self.config_path,
                'test_type': 'full_integration'
            },
            'locator_tests': {},
            'navigation_tests': {},
            'overall_result': {
                'passed': False,
                'summary': ''
            }
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # 加载测试页面（如果有的话）
                test_page = "docs/data-testid-integration/test_data_testid_example.html"
                if Path(test_page).exists():
                    file_url = f"file://{Path(test_page).absolute()}"
                    await page.goto(file_url)
                    print(f"📄 加载测试页面: {file_url}")
                else:
                    print("⚠️  测试页面不存在，使用空白页面测试")

                # 等待页面加载
                await page.wait_for_timeout(2000)

                # 执行定位器测试
                locator_results = await self.test_locators(page)
                test_results['locator_tests'] = locator_results

                # 执行导航测试（如果有导航元素的话）
                navigation_results = await self.test_page_navigation(page)
                test_results['navigation_tests'] = navigation_results

                # 计算总体结果
                total_tests = locator_results['total_tests'] + navigation_results['total_navigations']
                total_passed = locator_results['passed_tests'] + navigation_results['successful_navigations']

                test_results['overall_result']['total_tests'] = total_tests
                test_results['overall_result']['total_passed'] = total_passed
                test_results['overall_result']['pass_rate'] = round(total_passed / total_tests * 100, 2) if total_tests > 0 else 0

                # 检查 CI 门禁
                ci_validation = locator_results.get('ci_validation', {})
                test_results['ci_validation'] = ci_validation

                if ci_validation.get('passed', False):
                    test_results['overall_result']['passed'] = True
                    test_results['overall_result']['summary'] = "🎉 所有测试通过，CI 门禁验证成功！"
                else:
                    test_results['overall_result']['passed'] = False
                    failures = ci_validation.get('failures', [])
                    test_results['overall_result']['summary'] = f"❌ CI 门禁验证失败: {'; '.join(failures)}"

            finally:
                await browser.close()

        test_results['test_session']['completed_at'] = datetime.now().isoformat()

        return test_results

    def generate_test_report(self, results: dict) -> str:
        """
        生成测试报告

        Args:
            results: 测试结果

        Returns:
            str: 格式化的报告
        """
        lines = []
        lines.append("📊 Data-TestId 集成测试报告")
        lines.append("=" * 50)
        lines.append("")

        # 测试会话信息
        session = results['test_session']
        lines.append("🕐 测试会话信息:")
        lines.append(f"  开始时间: {session['started_at']}")
        lines.append(f"  结束时间: {session['completed_at']}")
        lines.append(f"  配置文件: {session['config_file']}")
        lines.append("")

        # 定位器测试结果
        locator_tests = results['locator_tests']
        lines.append("🧪 定位器测试结果:")
        lines.append(f"  总测试数: {locator_tests['total_tests']}")
        lines.append(f"  通过测试: {locator_tests['passed_tests']}")
        lines.append(f"  失败测试: {locator_tests['failed_tests']}")
        lines.append("")

        # 度量信息
        if 'locator_metrics' in locator_tests:
            metrics = locator_tests['locator_metrics']
            lines.append("📈 度量信息:")
            lines.append(f"  data-testid 命中率: {metrics['data_testid_hit_rate']}%")
            lines.append(f"  回退率: {metrics['fallback_rate']}%")
            lines.append(f"  失败率: {metrics['failure_rate']}%")
            lines.append("")

        # CI 验证结果
        if 'ci_validation' in results:
            ci_validation = results['ci_validation']
            lines.append("🚪 CI 门禁验证:")
            if ci_validation.get('passed', False):
                lines.append("  ✅ 验证通过")
            else:
                lines.append("  ❌ 验证失败")
                failures = ci_validation.get('failures', [])
                for failure in failures:
                    lines.append(f"    • {failure}")
            lines.append("")

        # 总体结果
        overall = results['overall_result']
        lines.append("📋 总体结果:")
        lines.append(f"  总测试数: {overall['total_tests']}")
        lines.append(f"  通过测试: {overall['total_passed']}")
        lines.append(f"  通过率: {overall['pass_rate']}%")
        lines.append(f"  结果: {overall['summary']}")
        lines.append("")

        # 详细测试信息
        lines.append("📝 详细测试信息:")
        for test_detail in locator_tests.get('test_details', []):
            element = test_detail['element']
            action = test_detail['action']
            success = "✅" if test_detail['success'] else "❌"
            strategy = test_detail.get('strategy_used', 'unknown')
            lines.append(f"  {success} {element} ({action}) - 策略: {strategy}")

        return "\n".join(lines)

    def save_test_results(self, results: dict, output_file: str):
        """
        保存测试结果

        Args:
            results: 测试结果
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📄 测试结果已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存测试结果失败: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Data-TestId 集成测试')
    parser.add_argument('--config', default='config/data_testid_config.yaml',
                    help='配置文件路径')
    parser.add_argument('--output', default='reports/data_testid_integration_test.json',
                    help='测试结果输出文件')
    parser.add_argument('--report', default='reports/data_testid_integration_report.txt',
                    help='测试报告输出文件')

    args = parser.parse_args()

    # 创建测试器
    tester = DataTestIdIntegrationTester(args.config)

    # 运行测试
    try:
        results = await tester.run_full_integration_test()

        # 生成报告
        report_text = tester.generate_test_report(results)
        print(report_text)

        # 保存结果
        tester.save_test_results(results, args.output)

        # 保存报告文本
        try:
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"📄 测试报告已保存到: {args.report}")
        except Exception as e:
            print(f"⚠️  保存报告失败: {e}")

        # 返回退出码
        overall_result = results['overall_result']
        if overall_result.get('passed', False):
            print("🎉 Data-TestId 集成测试通过!")
            sys.exit(0)
        else:
            print("💥 Data-TestId 集成测试失败!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 测试执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
