"""
网站打开步骤
访问测试网站并验证基本功能
"""

import logging
from typing import Dict, Any, Optional, List
from ..browser import BrowserManager
from ..utils import Timer
from ..mcp import ConsoleMonitor, NetworkAnalyzer


class OpenSiteStep:
    """网站打开步骤"""

    def __init__(self, browser: BrowserManager, config: Dict[str, Any]):
        """
        初始化网站打开步骤

        Args:
            browser: 浏览器管理器
            config: 配置字典
        """
        self.browser = browser
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.test_config = config.get('test', {})
        self.selectors = self.test_config.get('selectors', {})

        # MCP 监控器
        self.console_monitor: Optional[ConsoleMonitor] = None
        self.network_analyzer: Optional[NetworkAnalyzer] = None

    def setup_mcp_monitoring(self, console_monitor: ConsoleMonitor, network_analyzer: NetworkAnalyzer):
        """
        设置 MCP 监控

        Args:
            console_monitor: 控制台监控器
            network_analyzer: 网络分析器
        """
        self.console_monitor = console_monitor
        self.network_analyzer = network_analyzer

    async def execute(self) -> Dict[str, Any]:
        """
        执行网站打开步骤

        Returns:
            Dict[str, Any]: 执行结果
        """
        result = {
            'step': 'open_site',
            'success': False,
            'error': None,
            'details': {},
            'metrics': {}
        }

        timer = Timer('open_site')
        timer.start()

        try:
            self.logger.info("开始执行网站打开步骤")

            # 1. 访问网站
            success = await self._navigate_to_site()
            if not success:
                result['error'] = "无法访问测试网站"
                return result

            timer.checkpoint("navigation_complete")

            # 2. 验证页面基本元素
            success = await self._verify_page_elements()
            if not success:
                result['error'] = "页面基本元素验证失败"
                return result

            timer.checkpoint("elements_verified")

            # 3. 检查页面状态
            page_info = await self._check_page_status()
            result['details']['page_info'] = page_info

            timer.checkpoint("page_status_checked")

            # 4. 等待页面完全加载
            await self._wait_for_page_ready()
            timer.checkpoint("page_ready")

            # 执行成功
            result['success'] = True
            result['metrics']['total_time'] = timer.stop()
            result['metrics']['checkpoints'] = timer.get_checkpoints()

            self.logger.info("网站打开步骤执行成功")
            return result

        except Exception as e:
            result['error'] = str(e)
            result['metrics']['total_time'] = timer.get_elapsed_time()
            self.logger.error(f"网站打开步骤执行失败: {str(e)}")
            return result

    async def _navigate_to_site(self) -> bool:
        """
        导航到测试网站

        Returns:
            bool: 导航是否成功
        """
        test_url = self.test_config.get('url')
        if not test_url:
            self.logger.error("测试 URL 未配置")
            return False

        try:
            success = await self.browser.navigate_to(test_url)
            if success:
                self.logger.info(f"成功访问网站: {test_url}")
            return success

        except Exception as e:
            self.logger.error(f"访问网站失败: {str(e)}")
            return False

    async def _verify_page_elements(self) -> bool:
        """
        验证页面基本元素

        Returns:
            bool: 验证是否成功
        """
        required_elements = [
            'prompt_input',
            'generate_image_button',
            'generate_video_button'
        ]

        for element_name in required_elements:
            if not await self._verify_element_exists(element_name):
                self.logger.error(f"关键元素不存在: {element_name}")
                return False

        self.logger.info("所有关键元素验证通过")
        return True

    async def _verify_element_exists(self, element_name: str) -> bool:
        """
        验证指定元素是否存在

        Args:
            element_name: 元素名称

        Returns:
            bool: 元素是否存在
        """
        element_selectors = self.selectors.get(element_name, [])
        if not element_selectors:
            self.logger.warning(f"元素 {element_name} 的选择器未配置")
            return False

        # 尝试每个选择器
        for selector in element_selectors:
            try:
                if await self.browser.wait_for_element(selector, timeout=5000):
                    self.logger.debug(f"找到元素 {element_name}: {selector}")
                    return True
            except Exception as e:
                self.logger.debug(f"选择器 {selector} 未找到元素: {str(e)}")
                continue

        self.logger.warning(f"未找到元素 {element_name}")
        return False

    async def _check_page_status(self) -> Dict[str, Any]:
        """
        检查页面状态

        Returns:
            Dict[str, Any]: 页面状态信息
        """
        page_info = {}

        try:
            # 获取页面标题
            page_info['title'] = await self.browser.get_page_title()

            # 获取当前 URL
            page_info['url'] = await self.browser.get_page_url()

            # 检查页面是否加载完成
            page_info['ready_state'] = await self.browser.evaluate_javascript(
                "document.readyState"
            )

            # 检查是否有 JavaScript 错误
            js_errors = await self.browser.evaluate_javascript("""
                // 检查是否有未捕获的错误
                if (window.errorCount !== undefined) {
                    return window.errorCount;
                }
                return 0;
            """)
            page_info['js_errors'] = js_errors or 0

            # 检查页面性能
            performance_info = await self.browser.evaluate_javascript("""
                if (window.performance && window.performance.timing) {
                    var timing = window.performance.timing;
                    return {
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        loadComplete: timing.loadEventEnd - timing.navigationStart,
                        domInteractive: timing.domInteractive - timing.navigationStart
                    };
                }
                return null;
            """)
            page_info['performance'] = performance_info

            self.logger.info(f"页面状态检查完成: {page_info}")
            return page_info

        except Exception as e:
            self.logger.error(f"页面状态检查失败: {str(e)}")
            page_info['error'] = str(e)
            return page_info

    async def _wait_for_page_ready(self) -> bool:
        """
        等待页面完全准备就绪

        Returns:
            bool: 等待是否成功
        """
        try:
            # 等待页面加载完成
            await self.browser.wait_for_navigation(timeout=10000)

            # 等待特定时间确保所有脚本执行完成
            import asyncio
            await asyncio.sleep(2)

            # 检查页面是否准备好
            ready = await self.browser.evaluate_javascript("""
                return document.readyState === 'complete' &&
                       (!window.jQuery || window.jQuery.active === 0) &&
                       document.readyState === 'complete';
            """)

            if ready:
                self.logger.info("页面已完全准备就绪")
                return True
            else:
                self.logger.warning("页面可能未完全准备就绪，但继续执行")
                return True

        except Exception as e:
            self.logger.warning(f"等待页面准备就绪时出现警告: {str(e)}")
            return True  # 继续执行

    def get_step_name(self) -> str:
        """获取步骤名称"""
        return "打开网站"

    def get_required_selectors(self) -> List[str]:
        """获取必需的选择器列表"""
        return [
            'prompt_input',
            'generate_image_button',
            'generate_video_button'
        ]

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        # 检查基本配置
        if 'test' not in self.config:
            self.logger.error("缺少 test 配置")
            return False

        if 'url' not in self.config['test']:
            self.logger.error("缺少测试 URL 配置")
            return False

        if 'selectors' not in self.config['test']:
            self.logger.error("缺少选择器配置")
            return False

        # 检查必需的选择器
        required_selectors = self.get_required_selectors()
        selectors = self.config['test']['selectors']

        for selector_name in required_selectors:
            if selector_name not in selectors:
                self.logger.error(f"缺少选择器配置: {selector_name}")
                return False

            if not selectors[selector_name] or not isinstance(selectors[selector_name], list):
                self.logger.error(f"选择器配置格式错误: {selector_name}")
                return False

        return True