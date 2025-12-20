"""
混合定位器 - 结合 data-testid 和其他定位方式

提供高可用的元素定位策略，当 data-testid 不可用时自动回退到其他稳定方式。
"""

import logging
from typing import List, Optional, Callable, Any
from playwright.async_api import Page, Locator
from .data_testid_locator import DataTestIdLocator


class HybridLocator:
    """混合定位器 - 多策略元素定位"""

    def __init__(self, page: Page, config: dict = None):
        """
        初始化混合定位器

        Args:
            page: Playwright 页面对象
            config: 定位策略配置
        """
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.data_testid = DataTestIdLocator(page)
        self.config = config or self._get_default_config()

    def _get_default_config(self) -> dict:
        """获取默认的定位策略配置"""
        return {
            "prompt_input": [
                "[data-testid='prompt-input']",
                "[data-testid='prompt-textarea']",
                "textarea[placeholder*='提示']",
                "textarea[placeholder*='描述']",
                ".arco-textarea",
                "textarea:first-of-type"
            ],
            "generate_button": [
                "[data-testid='generate-button']",
                "[data-testid='generate-image-button']",
                "button:has-text('生成图片')",
                "button:has-text('生成')",
                ".arco-btn-primary",
                "button[type='submit']"
            ],
            "generate_video_button": [
                "[data-testid='generate-video-button']",
                "button:has-text('生成视频')",
                "button[data-action='video']",
                ".arco-btn-secondary:has-text('视频')"
            ],
            "image_result": [
                "[data-testid='image-result']",
                "[data-testid='result-image']",
                ".image-result",
                ".generated-image",
                "img[alt*='生成']"
            ],
            "video_result": [
                "[data-testid='video-result']",
                "[data-testid='result-video']",
                ".video-result",
                ".generated-video",
                "video[controls]"
            ],
            "loading_indicator": [
                "[data-testid='loading']",
                "[data-testid='loading-indicator']",
                "[data-testid='spinner']",
                ".loading",
                ".spinner",
                "[data-loading='true']"
            ],
            "error_message": [
                "[data-testid='error-message']",
                "[data-testid='error']",
                ".error-message",
                ".arco-message-error",
                "[role='alert']"
            ],
            "nav_ai_create": [
                "[data-testid='nav-ai-create']",
                "[data-testid='nav-ai-create-tab']",
                "a:has-text('AI创作')",
                "button:has-text('AI创作')",
                ".nav-item:has-text('AI创作')"
            ],
            "nav_text_image": [
                "[data-testid='nav-text-image']",
                "[data-testid='nav-text-image-tab']",
                "a:has-text('文生图')",
                "button:has-text('文生图')",
                ".nav-item:has-text('文生图')"
            ],
            "clear_button": [
                "[data-testid='clear-button']",
                "[data-testid='clear-btn']",
                "button:has-text('清空')",
                "button:has-text('清除')",
                ".arco-btn:has-text('清空')"
            ]
        }

    async def locate(self, element_name: str, timeout: int = 10000) -> Optional[Locator]:
        """
        使用多策略定位元素

        Args:
            element_name: 元素名称（对应配置中的键）
            timeout: 每个策略的超时时间

        Returns:
            Optional[Locator]: 找到的元素定位器，失败返回 None
        """
        strategies = self.config.get(element_name, [])

        if not strategies:
            self.logger.warning(f"未找到元素 '{element_name}' 的定位策略")
            return None

        self.logger.debug(f"尝试定位元素 '{element_name}'，共 {len(strategies)} 种策略")

        for i, strategy in enumerate(strategies):
            try:
                self.logger.debug(f"策略 {i+1}/{len(strategies)}: {strategy}")

                # 如果是 data-testid 策略，优先使用
                if "[data-testid=" in strategy:
                    testid = strategy.split("'")[1] if "'" in strategy else strategy.split('"')[1]
                    if await self.data_testid.is_visible_by_testid(testid, timeout=1000):
                        element = self.data_testid.get_by_testid(testid)
                        self.logger.info(f"成功使用 data-testid 定位 '{element_name}': {strategy}")
                        return element
                else:
                    # 其他策略
                    element = self.page.locator(strategy)
                    count = await element.count()

                    if count > 0:
                        # 检查元素是否可见（如果需要交互）
                        if i < 3:  # 前几个策略通常用于交互元素
                            visible_element = element.first
                            if await visible_element.is_visible():
                                self.logger.info(f"成功定位 '{element_name}': {strategy}")
                                return visible_element
                        else:
                            # 容器类元素不需要可见性检查
                            self.logger.info(f"成功定位 '{element_name}': {strategy}")
                            return element.first

            except Exception as e:
                self.logger.debug(f"策略失败: {strategy}, 错误: {str(e)}")
                continue

        self.logger.error(f"所有定位策略都失败了: {element_name}")
        return None

    async def locate_and_wait(self, element_name: str, state: str = "visible", timeout: int = 10000) -> Optional[Locator]:
        """
        定位元素并等待其达到指定状态

        Args:
            element_name: 元素名称
            state: 期望状态
            timeout: 超时时间

        Returns:
            Optional[Locator]: 元素定位器
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return None

        try:
            await element.wait_for(state=state, timeout=timeout)
            return element
        except Exception as e:
            self.logger.warning(f"等待元素状态失败: {element_name}, 状态: {state}, 错误: {str(e)}")
            return None

    async def click(self, element_name: str, timeout: int = 10000) -> bool:
        """
        定位并点击元素

        Args:
            element_name: 元素名称
            timeout: 超时时间

        Returns:
            bool: 是否成功点击
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return False

        try:
            await element.click()
            self.logger.info(f"成功点击元素: {element_name}")
            return True
        except Exception as e:
            self.logger.error(f"点击元素失败: {element_name}, 错误: {str(e)}")
            return False

    async def fill(self, element_name: str, value: str, timeout: int = 10000) -> bool:
        """
        定位并填充输入框

        Args:
            element_name: 元素名称
            value: 要填入的值
            timeout: 超时时间

        Returns:
            bool: 是否成功填充
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return False

        try:
            await element.fill(value)
            self.logger.info(f"成功填充元素: {element_name} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"填充元素失败: {element_name}, 错误: {str(e)}")
            return False

    async def get_text(self, element_name: str, timeout: int = 10000) -> Optional[str]:
        """
        获取元素的文本内容

        Args:
            element_name: 元素名称
            timeout: 超时时间

        Returns:
            Optional[str]: 元素的文本内容
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return None

        try:
            text = await element.inner_text()
            return text
        except Exception as e:
            self.logger.error(f"获取元素文本失败: {element_name}, 错误: {str(e)}")
            return None

    async def is_visible(self, element_name: str, timeout: int = 5000) -> bool:
        """
        检查元素是否可见

        Args:
            element_name: 元素名称
            timeout: 超时时间

        Returns:
            bool: 元素是否可见
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return False

        try:
            return await element.is_visible()
        except:
            return False

    async def wait_for_disappear(self, element_name: str, timeout: int = 10000) -> bool:
        """
        等待元素消失

        Args:
            element_name: 元素名称
            timeout: 超时时间

        Returns:
            bool: 元素是否消失
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return True  # 元素不存在，视为已消失

        try:
            await element.wait_for(state="hidden", timeout=timeout)
            return True
        except:
            return False

    async def locate_with_retry(self, element_name: str, max_attempts: int = 3, delay: float = 1.0) -> Optional[Locator]:
        """
        带重试机制的元素定位

        Args:
            element_name: 元素名称
            max_attempts: 最大重试次数
            delay: 重试间隔（秒）

        Returns:
            Optional[Locator]: 元素定位器
        """
        import asyncio

        for attempt in range(max_attempts):
            element = await self.locate(element_name)
            if element:
                return element

            if attempt < max_attempts - 1:
                self.logger.debug(f"定位失败，{delay}秒后重试 ({attempt + 1}/{max_attempts}): {element_name}")
                await asyncio.sleep(delay)

        self.logger.error(f"重试 {max_attempts} 次后仍无法定位元素: {element_name}")
        return None

    def update_config(self, element_name: str, strategies: List[str]):
        """
        更新元素的定位策略

        Args:
            element_name: 元素名称
            strategies: 新的定位策略列表
        """
        self.config[element_name] = strategies
        self.logger.info(f"更新元素 '{element_name}' 的定位策略: {strategies}")

    def add_strategy(self, element_name: str, strategy: str, position: int = 0):
        """
        添加新的定位策略

        Args:
            element_name: 元素名称
            strategy: 定位策略
            position: 插入位置（0表示最前面）
        """
        if element_name not in self.config:
            self.config[element_name] = []

        self.config[element_name].insert(position, strategy)
        self.logger.info(f"为元素 '{element_name}' 添加策略: {strategy}")

    async def validate_strategies(self) -> dict:
        """
        验证当前页面的定位策略有效性

        Returns:
            dict: 验证结果
        """
        results = {}

        for element_name, strategies in self.config.items():
            valid_strategies = []

            for strategy in strategies:
                try:
                    element = self.page.locator(strategy)
                    count = await element.count()
                    if count > 0:
                        valid_strategies.append({
                            "strategy": strategy,
                            "count": count,
                            "visible": await element.first.is_visible()
                        })
                except:
                    continue

            results[element_name] = {
                "total_strategies": len(strategies),
                "valid_strategies": len(valid_strategies),
                "strategies": valid_strategies
            }

        return results

    async def get_current_testids(self) -> List[str]:
        """
        获取当前页面所有的 data-testid

        Returns:
            List[str]: data-testid 列表
        """
        return await self.data_testid.get_all_testids()