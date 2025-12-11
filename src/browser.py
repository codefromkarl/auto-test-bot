"""
浏览器管理模块
负责 Playwright 浏览器的初始化、配置和基本操作
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import yaml


class BrowserManager:
    """浏览器管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化浏览器管理器

        Args:
            config: 浏览器配置字典
        """
        self.config = config.get('browser', {})
        self.logger = logging.getLogger(__name__)

        # 浏览器实例
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 配置参数
        self.browser_type = self.config.get('type', 'chromium')
        self.headless = self.config.get('headless', True)
        self.viewport = self.config.get('viewport', {'width': 1920, 'height': 1080})
        self.user_agent = self.config.get('user_agent', 'AutoTestBot/1.0 (Playwright)')
        self.ignore_https_errors = self.config.get('ignore_https_errors', True)

    async def initialize(self) -> bool:
        """
        初始化浏览器

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("正在初始化浏览器...")

            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 选择浏览器类型
            if self.browser_type.lower() == 'chromium':
                browser_launcher = self.playwright.chromium
            elif self.browser_type.lower() == 'firefox':
                browser_launcher = self.playwright.firefox
            elif self.browser_type.lower() == 'webkit':
                browser_launcher = self.playwright.webkit
            else:
                self.logger.error(f"不支持的浏览器类型: {self.browser_type}")
                return False

            # 启动浏览器
            launch_options = {
                'headless': self.headless,
                'args': self.config.get('launch_args', [])
            }

            self.browser = await browser_launcher.launch(**launch_options)

            # 创建浏览器上下文
            context_options = {
                'viewport': self.viewport,
                'user_agent': self.user_agent,
                'ignore_https_errors': self.ignore_https_errors,
                'java_script_enabled': True,
                'accept_downloads': False
            }

            self.context = await self.browser.new_context(**context_options)

            # 创建页面
            self.page = await self.context.new_page()

            # 设置默认超时
            timeout = self.config.get('default_timeout', 30000)
            self.page.set_default_timeout(timeout)

            self.logger.info(f"浏览器初始化成功: {self.browser_type}")
            return True

        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {str(e)}")
            return False

    async def navigate_to(self, url: str) -> bool:
        """
        导航到指定 URL

        Args:
            url: 目标 URL

        Returns:
            bool: 导航是否成功
        """
        if not self.page:
            self.logger.error("浏览器页面未初始化")
            return False

        try:
            self.logger.info(f"正在访问: {url}")

            # 设置页面加载超时
            page_load_timeout = self.config.get('page_load_timeout', 60000)

            # 导航到目标页面
            response = await self.page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=page_load_timeout
            )

            # 检查响应状态
            if response and response.status >= 400:
                self.logger.error(f"页面访问失败: HTTP {response.status}")
                return False

            self.logger.info("页面加载成功")
            return True

        except Exception as e:
            self.logger.error(f"页面导航失败: {str(e)}")
            return False

    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        等待元素出现

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            bool: 元素是否出现
        """
        if not self.page:
            return False

        try:
            wait_timeout = timeout or self.config.get('element_timeout', 10000)

            await self.page.wait_for_selector(
                selector,
                state='visible',
                timeout=wait_timeout
            )

            return True

        except Exception as e:
            self.logger.warning(f"等待元素失败 [{selector}]: {str(e)}")
            return False

    async def find_element(self, selector: str) -> Optional[Any]:
        """
        查找元素

        Args:
            selector: CSS 选择器

        Returns:
            元素对象或 None
        """
        if not self.page:
            return None

        try:
            element = await self.page.query_selector(selector)
            return element

        except Exception as e:
            self.logger.warning(f"查找元素失败 [{selector}]: {str(e)}")
            return None

    async def click_element(self, selector: str) -> bool:
        """
        点击元素

        Args:
            selector: CSS 选择器

        Returns:
            bool: 点击是否成功
        """
        try:
            await self.page.click(selector)
            return True

        except Exception as e:
            self.logger.error(f"点击元素失败 [{selector}]: {str(e)}")
            return False

    async def fill_input(self, selector: str, text: str) -> bool:
        """
        填充输入框

        Args:
            selector: CSS 选择器
            text: 输入文本

        Returns:
            bool: 填充是否成功
        """
        try:
            await self.page.fill(selector, text)
            return True

        except Exception as e:
            self.logger.error(f"填充输入框失败 [{selector}]: {str(e)}")
            return False

    async def take_screenshot(self, filename: str) -> bool:
        """
        截取屏幕截图

        Args:
            filename: 文件名

        Returns:
            bool: 截图是否成功
        """
        try:
            await self.page.screenshot(path=filename, full_page=True)
            self.logger.info(f"截图已保存: {filename}")
            return True

        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return False

    async def get_page_title(self) -> str:
        """
        获取页面标题

        Returns:
            str: 页面标题
        """
        if not self.page:
            return ""

        try:
            return await self.page.title()

        except Exception:
            return ""

    async def get_page_url(self) -> str:
        """
        获取当前页面 URL

        Returns:
            str: 当前 URL
        """
        if not self.page:
            return ""

        try:
            return self.page.url

        except Exception:
            return ""

    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行 JavaScript 代码

        Args:
            script: JavaScript 代码

        Returns:
            执行结果
        """
        if not self.page:
            return None

        try:
            return await self.page.evaluate(script)

        except Exception as e:
            self.logger.error(f"JavaScript 执行失败: {str(e)}")
            return None

    async def wait_for_navigation(self, timeout: Optional[int] = None) -> bool:
        """
        等待页面导航完成

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            bool: 导航是否完成
        """
        if not self.page:
            return False

        try:
            wait_timeout = timeout or self.config.get('page_load_timeout', 60000)
            await self.page.wait_for_load_state('domcontentloaded', timeout=wait_timeout)
            return True

        except Exception as e:
            self.logger.warning(f"等待导航完成失败: {str(e)}")
            return False

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self.logger.info("浏览器已关闭")

        except Exception as e:
            self.logger.error(f"关闭浏览器失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        if hasattr(self, 'page') and self.page:
            # 确保异步关闭
            try:
                loop = asyncio.get_event_loop()
                if not loop.is_closed():
                    loop.create_task(self.close())
            except Exception:
                pass