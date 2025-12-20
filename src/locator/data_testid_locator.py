"""
基于 data-testid 的元素定位器

提供稳定、可靠的元素定位功能，优先使用 data-testid 进行定位。
"""

import logging
from typing import Optional, List, Dict, Any
from playwright.async_api import Page, Locator


class DataTestIdLocator:
    """基于 data-testid 的元素定位器"""

    def __init__(self, page: Page):
        """
        初始化定位器

        Args:
            page: Playwright 页面对象
        """
        self.page = page
        self.logger = logging.getLogger(__name__)

    def get_by_testid(self, testid: str, timeout: int = 10000) -> Locator:
        """
        通过 data-testid 获取元素

        Args:
            testid: data-testid 的值
            timeout: 超时时间（毫秒）

        Returns:
            Locator: 元素定位器
        """
        selector = f"[data-testid='{testid}']"
        locator = self.page.locator(selector)
        # 注意：Playwright Python 的 locator() 不直接支持 timeout 参数
        # timeout 需要在操作时设置，如 locator.wait_for(timeout=timeout)
        return locator

    def get_by_testid_contains(self, testid_part: str, timeout: int = 10000) -> Locator:
        """
        通过包含的 data-testid 部分获取元素

        Args:
            testid_part: data-testid 的部分值
            timeout: 超时时间（毫秒）

        Returns:
            Locator: 元素定位器
        """
        selector = f"[data-testid*='{testid_part}']"
        return self.page.locator(selector)

    async def wait_for_testid(self, testid: str, state: str = "visible", timeout: int = 10000) -> bool:
        """
        等待具有指定 data-testid 的元素达到特定状态

        Args:
            testid: data-testid 的值
            state: 期望状态 ("visible", "hidden", "attached", "detached")
            timeout: 超时时间（毫秒）

        Returns:
            bool: 是否等待成功
        """
        try:
            selector = f"[data-testid='{testid}']"
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            return True
        except Exception as e:
            self.logger.warning(f"等待 data-testid='{testid}' 失败: {str(e)}")
            return False

    async def click_by_testid(self, testid: str, timeout: int = 10000) -> bool:
        """
        点击具有指定 data-testid 的元素

        Args:
            testid: data-testid 的值
            timeout: 超时时间（毫秒）

        Returns:
            bool: 是否点击成功
        """
        try:
            element = self.get_by_testid(testid, timeout)
            await element.click()
            self.logger.debug(f"成功点击 data-testid='{testid}'")
            return True
        except Exception as e:
            self.logger.error(f"点击 data-testid='{testid}' 失败: {str(e)}")
            return False

    async def fill_by_testid(self, testid: str, value: str, timeout: int = 10000) -> bool:
        """
        填充具有指定 data-testid 的输入框

        Args:
            testid: data-testid 的值
            value: 要填入的值
            timeout: 超时时间（毫秒）

        Returns:
            bool: 是否填充成功
        """
        try:
            element = self.get_by_testid(testid, timeout)
            await element.fill(value)
            self.logger.debug(f"成功填充 data-testid='{testid}' 值为: {value}")
            return True
        except Exception as e:
            self.logger.error(f"填充 data-testid='{testid}' 失败: {str(e)}")
            return False

    async def get_text_by_testid(self, testid: str, timeout: int = 10000) -> Optional[str]:
        """
        获取具有指定 data-testid 的元素的文本内容

        Args:
            testid: data-testid 的值
            timeout: 超时时间（毫秒）

        Returns:
            Optional[str]: 元素的文本内容
        """
        try:
            element = self.get_by_testid(testid, timeout)
            text = await element.inner_text()
            return text
        except Exception as e:
            self.logger.warning(f"获取 data-testid='{testid}' 文本失败: {str(e)}")
            return None

    async def is_visible_by_testid(self, testid: str, timeout: int = 5000) -> bool:
        """
        检查具有指定 data-testid 的元素是否可见

        Args:
            testid: data-testid 的值
            timeout: 超时时间（毫秒）

        Returns:
            bool: 元素是否可见
        """
        try:
            element = self.get_by_testid(testid, timeout)
            return await element.is_visible()
        except:
            return False

    async def get_all_testids(self) -> List[str]:
        """
        获取页面上所有的 data-testid 值

        Returns:
            List[str]: 所有 data-testid 的值列表
        """
        try:
            elements = await self.page.query_selector_all("[data-testid]")
            testids = []
            for element in elements:
                testid = await element.get_attribute("data-testid")
                if testid:
                    testids.append(testid)
            return list(set(testids))  # 去重
        except Exception as e:
            self.logger.error(f"获取所有 data-testid 失败: {str(e)}")
            return []

    async def screenshot_by_testid(self, testid: str, path: str, timeout: int = 10000) -> bool:
        """
        对具有指定 data-testid 的元素截图

        Args:
            testid: data-testid 的值
            path: 截图保存路径
            timeout: 超时时间（毫秒）

        Returns:
            bool: 是否截图成功
        """
        try:
            element = self.get_by_testid(testid, timeout)
            await element.screenshot(path=path)
            self.logger.debug(f"成功截图 data-testid='{testid}' 到 {path}")
            return True
        except Exception as e:
            self.logger.error(f"截图 data-testid='{testid}' 失败: {str(e)}")
            return False

    async def evaluate_by_testid(self, testid: str, expression: str, timeout: int = 10000) -> Any:
        """
        在具有指定 data-testid 的元素上执行 JavaScript 表达式

        Args:
            testid: data-testid 的值
            expression: JavaScript 表达式
            timeout: 超时时间（毫秒）

        Returns:
            Any: 执行结果
        """
        try:
            element = self.get_by_testid(testid, timeout)
            result = await element.evaluate(expression)
            return result
        except Exception as e:
            self.logger.error(f"执行 JavaScript 在 data-testid='{testid}' 失败: {str(e)}")
            return None

    def get_multiple_by_testid(self, testid_pattern: str) -> Locator:
        """
        获取多个匹配 data-testid 模式的元素

        Args:
            testid_pattern: data-testid 模式（支持通配符）

        Returns:
            Locator: 多个元素的定位器
        """
        if "*" in testid_pattern:
            # 支持通配符
            pattern = testid_pattern.replace("*", "")
            selector = f"[data-testid*='{pattern}']"
        else:
            selector = f"[data-testid='{testid_pattern}']"

        return self.page.locator(selector)

    async def wait_for_testid_disappear(self, testid: str, timeout: int = 10000) -> bool:
        """
        等待具有指定 data-testid 的元素消失

        Args:
            testid: data-testid 的值
            timeout: 超时时间（毫秒）

        Returns:
            bool: 元素是否消失
        """
        return await self.wait_for_testid(testid, state="hidden", timeout=timeout)

    async def hover_by_testid(self, testid: str, timeout: int = 10000) -> bool:
        """
        悬停在具有指定 data-testid 的元素上

        Args:
            testid: data-testid 的值
            timeout: 超时时间（毫秒）

        Returns:
            bool: 是否悬停成功
        """
        try:
            element = self.get_by_testid(testid, timeout)
            await element.hover()
            self.logger.debug(f"成功悬停在 data-testid='{testid}'")
            return True
        except Exception as e:
            self.logger.error(f"悬停在 data-testid='{testid}' 失败: {str(e)}")
            return False