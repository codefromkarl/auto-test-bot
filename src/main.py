"""
自动化测试机器人主程序
协调各个模块执行完整的测试流程
"""

import asyncio
import logging
import sys
import os
import argparse
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import ConfigLoader, MCPConfigLoader, setup_logging, create_test_logger, performance
from browser import BrowserManager
from steps import OpenSiteStep, GenerateImageStep, GenerateVideoStep, ValidateStep
from mcp import ConsoleMonitor, NetworkAnalyzer, PerformanceTracer, DOMDebugger, ErrorDiagnostic
from reporter import ReportFormatter


class AutoTestBot:
    """自动化测试机器人主类"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化自动化测试机器人

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.logger = None
        self.test_logger = None

        # 配置
        self.config: Dict[str, Any] = {}
        self.mcp_config: Dict[str, Any] = {}

        # 核心组件
        self.browser_manager: Optional[BrowserManager] = None
        self.test_steps: Dict[str, Any] = {}

        # MCP 监控器
        self.console_monitor: Optional[ConsoleMonitor] = None
        self.network_analyzer: Optional[NetworkAnalyzer] = None
        self.performance_tracer: Optional[PerformanceTracer] = None
        self.dom_debugger: Optional[DOMDebugger] = None
        self.error_diagnostic: Optional[ErrorDiagnostic] = None

        # 测试结果
        self.test_results: list = []
        self.mcp_data: Dict[str, Any] = {}
        self.screenshots: list = []

    async def initialize(self) -> bool:
        """
        初始化所有组件

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 加载配置
            await self._load_configurations()

            # 设置日志
            await self._setup_logging()

            # 初始化浏览器
            await self._initialize_browser()

            # 初始化 MCP 监控器
            await self._initialize_mcp_monitors()

            # 初始化测试步骤
            await self._initialize_test_steps()

            self.logger.info("自动化测试机器人初始化完成")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"初始化失败: {str(e)}")
            else:
                print(f"初始化失败: {str(e)}")
            return False

    async def _load_configurations(self):
        """加载配置文件"""
        # 加载主配置
        config_loader = ConfigLoader(self.config_path)
        self.config = config_loader.load_config()

        # 加载 MCP 配置
        mcp_config_loader = MCPConfigLoader()
        self.mcp_config = mcp_config_loader.load_config()

    async def _setup_logging(self):
        """设置日志系统"""
        # 配置日志
        logging_config = self.config.get('logging', {})
        setup_logging(logging_config)

        # 创建日志记录器
        self.logger = logging.getLogger(__name__)
        self.test_logger = create_test_logger("auto_test_bot")

        self.test_logger.start_test("自动化测试机器人")

    async def _initialize_browser(self):
        """初始化浏览器管理器"""
        self.browser_manager = BrowserManager(self.config)
        success = await self.browser_manager.initialize()

        if not success:
            raise RuntimeError("浏览器初始化失败")

    async def _initialize_mcp_monitors(self):
        """初始化 MCP 监控器"""
        if not self.mcp_config.get('mcp_server', {}).get('enabled', True):
            self.logger.info("MCP 监控已禁用")
            return

        # 创建监控器实例
        self.console_monitor = ConsoleMonitor(self.mcp_config)
        self.network_analyzer = NetworkAnalyzer(self.mcp_config)
        self.performance_tracer = PerformanceTracer(self.mcp_config)
        self.dom_debugger = DOMDebugger(self.mcp_config)
        self.error_diagnostic = ErrorDiagnostic(self.config)

        # 设置监控器关联
        self.error_diagnostic.set_monitors(
            self.console_monitor,
            self.network_analyzer,
            self.performance_tracer,
            self.dom_debugger
        )

        self.logger.info("MCP 监控器初始化完成")

    async def _initialize_test_steps(self):
        """初始化测试步骤"""
        self.test_steps = {
            'open_site': OpenSiteStep(self.browser_manager, self.config),
            'generate_image': GenerateImageStep(self.browser_manager, self.config),
            'generate_video': GenerateVideoStep(self.browser_manager, self.config),
            'validate': ValidateStep(self.config)
        }

        # 设置 MCP 监控
        for step in self.test_steps.values():
            if hasattr(step, 'setup_mcp_monitoring'):
                step.setup_mcp_monitoring(
                    self.console_monitor,
                    self.network_analyzer
                )

        self.logger.info("测试步骤初始化完成")

    async def run_test(self) -> Dict[str, Any]:
        """
        执行完整的测试流程

        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            self.test_logger.start_test("执行完整测试流程")

            # 启动性能监控
            performance.start_timer('total_test')

            # 1. 启动 MCP 监控
            await self._start_mcp_monitoring()

            # 2. 执行测试步骤
            image_url = None
            steps_config = self.config.get('test', {}).get('steps', {})

            # 执行网站打开
            if steps_config.get('open_site', True):
                result = await self._execute_step('open_site')
                if not result.get('success'):
                    return await self._finalize_test(result)

            # 执行文生图
            if steps_config.get('generate_image', True):
                result = await self._execute_step('generate_image')
                if result.get('success'):
                    image_url = result.get('generated_image_url')
                else:
                    return await self._finalize_test(result)

            # 执行图生视频
            if steps_config.get('generate_video', True):
                result = await self._execute_step('generate_video', image_url=image_url)
                if not result.get('success'):
                    return await self._finalize_test(result)

            # 执行结果验证
            result = await self._execute_step('validate')
            return await self._finalize_test(result)

        except Exception as e:
            self.logger.error(f"测试执行异常: {str(e)}")
            error_result = {
                'step': 'main',
                'success': False,
                'error': str(e),
                'details': {},
                'metrics': {}
            }
            return await self._finalize_test(error_result)

    async def _start_mcp_monitoring(self):
        """启动 MCP 监控"""
        if not self.mcp_config.get('mcp_server', {}).get('enabled', True):
            return

        try:
            if self.console_monitor:
                self.console_monitor.start_monitoring()

            if self.network_analyzer:
                self.network_analyzer.start_monitoring()

            if self.performance_tracer:
                self.performance_tracer.start_tracing()

            if self.dom_debugger:
                # DOM 调试在需要时启动

            self.logger.info("MCP 监控已启动")

        except Exception as e:
            self.logger.error(f"启动 MCP 监控失败: {str(e)}")

    async def _execute_step(self, step_name: str, **kwargs) -> Dict[str, Any]:
        """
        执行指定步骤

        Args:
            step_name: 步骤名称
            **kwargs: 步骤参数

        Returns:
            Dict[str, Any]: 步骤执行结果
        """
        if step_name not in self.test_steps:
            raise ValueError(f"未知的测试步骤: {step_name}")

        step = self.test_steps[step_name]

        # 开始步骤计时
        step_timer = performance.start_timer(step_name)

        # 记录步骤开始
        self.test_logger.start_step(step.get_step_name())

        try:
            # 执行步骤
            result = await step.execute(**kwargs)

            # 记录步骤结果
            if result.get('success'):
                self.test_logger.step_success(step.get_step_name())
            else:
                self.test_logger.step_failure(step.get_step_name(), result.get('error', 'Unknown error'))

            # 保存结果
            self.test_results.append(result)

            return result

        except Exception as e:
            error_result = {
                'step': step_name,
                'success': False,
                'error': str(e),
                'details': {},
                'metrics': {}
            }

            self.test_logger.step_failure(step.get_step_name(), str(e))
            self.test_results.append(error_result)
            return error_result

        finally:
            # 停止步骤计时
            performance.stop_timer(step_name)

    async def _finalize_test(self, last_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        完成测试流程并生成报告

        Args:
            last_result: 最后一个步骤的结果

        Returns:
            Dict[str, Any]: 最终测试结果
        """
        try:
            self.logger.info("开始完成测试流程")

            # 停止总计时
            total_time = performance.stop_timer('total_test')

            # 3. 停止 MCP 监控并收集数据
            await self._stop_mcp_monitoring()

            # 4. 生成错误诊断报告
            await self._generate_error_diagnostic()

            # 5. 截取屏幕截图
            await self._take_final_screenshot()

            # 6. 生成测试报告
            final_result = await self._generate_final_report(last_result, total_time)

            # 7. 保存报告
            await self._save_reports(final_result)

            # 8. 记录测试完成
            self.test_logger.end_test(
                final_result.get('overall_success', False),
                f"总耗时: {total_time:.2f}ms"
            )

            return final_result

        except Exception as e:
            self.logger.error(f"完成测试流程失败: {str(e)}")
            return {
                'overall_success': False,
                'error': f"测试完成失败: {str(e)}",
                'test_results': self.test_results
            }

    async def _stop_mcp_monitoring(self):
        """停止 MCP 监控并收集数据"""
        if not self.mcp_config.get('mcp_server', {}).get('enabled', True):
            return

        try:
            self.mcp_data = {}

            # 停止控制台监控
            if self.console_monitor:
                self.mcp_data['console'] = self.console_monitor.stop_monitoring()

            # 停止网络监控
            if self.network_analyzer:
                self.mcp_data['network'] = self.network_analyzer.stop_monitoring()

            # 停止性能追踪
            if self.performance_tracer:
                trace = self.performance_tracer.stop_tracing()
                if trace:
                    self.mcp_data['performance'] = trace.to_dict()

            # 获取 DOM 快照
            if self.dom_debugger and self.browser_manager:
                current_url = await self.browser_manager.get_page_url()
                dom_snapshot = self.dom_debugger.create_snapshot(
                    current_url,
                    {}  # 这里应该从浏览器获取真实 DOM 数据
                )
                if dom_snapshot:
                    self.mcp_data['dom'] = dom_snapshot.to_dict()

            self.logger.info("MCP 监控数据收集完成")

        except Exception as e:
            self.logger.error(f"停止 MCP 监控失败: {str(e)}")

    async def _generate_error_diagnostic(self):
        """生成错误诊断报告"""
        if not self.error_diagnostic:
            return

        try:
            diagnostic_report = self.error_diagnostic.diagnose_errors()
            self.mcp_data['diagnostic'] = diagnostic_report.to_dict()
            self.logger.info("错误诊断报告生成完成")

        except Exception as e:
            self.logger.error(f"生成错误诊断失败: {str(e)}")

    async def _take_final_screenshot(self):
        """截取最终屏幕截图"""
        if not self.config.get('reporting', {}).get('include_screenshots', True):
            return

        try:
            screenshot_dir = self.config.get('reporting', {}).get('output_dir', 'reports')
            os.makedirs(screenshot_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = os.path.join(screenshot_dir, f"final_screenshot_{timestamp}.png")

            success = await self.browser_manager.take_screenshot(screenshot_filename)
            if success:
                self.screenshots.append(screenshot_filename)
                self.logger.info(f"最终截图已保存: {screenshot_filename}")

        except Exception as e:
            self.logger.error(f"截取最终截图失败: {str(e)}")

    async def _generate_final_report(self, last_result: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """生成最终报告"""
        try:
            formatter = ReportFormatter(self.config)

            # 格式化报告
            report = formatter.format_test_report(
                self.test_results,
                self.mcp_data,
                self.screenshots
            )

            # 添加总体信息
            report['overall_success'] = last_result.get('success', False)
            report['total_test_time'] = total_time
            report['performance_summary'] = performance.get_summary()

            return report

        except Exception as e:
            self.logger.error(f"生成最终报告失败: {str(e)}")
            return {
                'overall_success': False,
                'error': f"报告生成失败: {str(e)}",
                'test_results': self.test_results
            }

    async def _save_reports(self, final_report: Dict[str, Any]):
        """保存测试报告"""
        try:
            formatter = ReportFormatter(self.config)

            # 保存报告文件
            saved_files = formatter.save_report(final_report)

            self.logger.info("测试报告已保存:")
            for format_type, filepath in saved_files.items():
                self.logger.info(f"  {format_type.upper()}: {filepath}")

        except Exception as e:
            self.logger.error(f"保存测试报告失败: {str(e)}")

    async def cleanup(self):
        """清理资源"""
        try:
            # 关闭浏览器
            if self.browser_manager:
                await self.browser_manager.close()

            # 清理 MCP 监控器
            if self.performance_tracer:
                self.performance_tracer.clear_traces()

            if self.dom_debugger:
                self.dom_debugger.clear_snapshots()

            self.logger.info("资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {str(e)}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='自动化测试机器人')
    parser.add_argument('--config', default='config/config.yaml', help='配置文件路径')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--mcp-diagnostic', action='store_true', help='MCP 深度诊断模式')

    args = parser.parse_args()

    # 创建测试机器人
    bot = AutoTestBot(args.config)

    try:
        # 初始化
        if not await bot.initialize():
            print("初始化失败，退出程序")
            sys.exit(1)

        # 执行测试
        result = await bot.run_test()

        # 输出结果
        if result.get('overall_success'):
            print(f"✅ 测试成功完成，总耗时: {result.get('total_test_time', 0):.2f}ms")
        else:
            print(f"❌ 测试失败: {result.get('error', 'Unknown error')}")

        # 输出性能摘要
        if 'performance_summary' in result:
            perf_summary = result['performance_summary']
            print(f"\n📊 性能摘要:")
            for name, timer in perf_summary.get('timers', {}).items():
                print(f"  {name}: {timer.get('elapsed_time_str', 'N/A')}")

        # 设置退出码
        sys.exit(0 if result.get('overall_success') else 1)

    except KeyboardInterrupt:
        print("\n用户中断测试")
        sys.exit(1)

    except Exception as e:
        print(f"程序执行异常: {str(e)}")
        sys.exit(1)

    finally:
        # 清理资源
        await bot.cleanup()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())