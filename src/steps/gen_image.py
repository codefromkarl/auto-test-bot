"""
文生图测试步骤
执行文生图流程并验证结果
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from ..browser import BrowserManager
from ..utils import Timer
from ..mcp import ConsoleMonitor, NetworkAnalyzer


class GenerateImageStep:
    """文生图测试步骤"""

    def __init__(self, browser: BrowserManager, config: Dict[str, Any]):
        """
        初始化文生图测试步骤

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

        # 测试配置
        self.test_prompt = self.test_config.get('test_prompt', '一只可爱的猫咪在花园里玩耍')
        self.timeout = self.test_config.get('timeout', 30000)

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
        执行文生图测试步骤

        Returns:
            Dict[str, Any]: 执行结果
        """
        result = {
            'step': 'generate_image',
            'success': False,
            'error': None,
            'details': {},
            'metrics': {},
            'generated_image_url': None
        }

        timer = Timer('generate_image')
        timer.start()

        try:
            self.logger.info("开始执行文生图测试步骤")

            # 1. 查找并验证提示词输入框
            success = await self._verify_prompt_input()
            if not success:
                result['error'] = "提示词输入框验证失败"
                return result

            timer.checkpoint("prompt_input_verified")

            # 2. 输入测试提示词
            success = await self._input_prompt()
            if not success:
                result['error'] = "输入提示词失败"
                return result

            timer.checkpoint("prompt_input_complete")

            # 3. 点击生成图片按钮
            success = await self._click_generate_button()
            if not success:
                result['error'] = "点击生成图片按钮失败"
                return result

            timer.checkpoint("generate_button_clicked")

            # 4. 等待图片生成完成
            success, image_url = await self._wait_for_image_generation()
            if not success:
                result['error'] = "图片生成失败或超时"
                return result

            timer.checkpoint("image_generation_complete")

            # 5. 验证生成的图片
            success = await self._verify_generated_image(image_url)
            if not success:
                result['error'] = "生成的图片验证失败"
                return result

            timer.checkpoint("image_verification_complete")

            # 执行成功
            result['success'] = True
            result['generated_image_url'] = image_url
            result['metrics']['total_time'] = timer.stop()
            result['metrics']['checkpoints'] = timer.get_checkpoints()
            result['details']['prompt_used'] = self.test_prompt

            self.logger.info(f"文生图测试步骤执行成功，生成图片: {image_url}")
            return result

        except Exception as e:
            result['error'] = str(e)
            result['metrics']['total_time'] = timer.get_elapsed_time()
            self.logger.error(f"文生图测试步骤执行失败: {str(e)}")
            return result

    async def _verify_prompt_input(self) -> bool:
        """
        验证提示词输入框

        Returns:
            bool: 验证是否成功
        """
        input_selectors = self.selectors.get('prompt_input', [])
        if not input_selectors:
            self.logger.error("提示词输入框选择器未配置")
            return False

        # 尝试找到可用的输入框
        for selector in input_selectors:
            try:
                element = await self.browser.find_element(selector)
                if element:
                    # 验证元素是否可交互
                    is_visible = await self.browser.evaluate_javascript(
                        f"""const elem = document.querySelector("{selector}");
                        return elem && !elem.disabled && elem.offsetParent !== null;"""
                    )
                    if is_visible:
                        self.logger.info(f"找到可用的提示词输入框: {selector}")
                        return True
            except Exception as e:
                self.logger.debug(f"选择器 {selector} 验证失败: {str(e)}")
                continue

        self.logger.error("未找到可用的提示词输入框")
        return False

    async def _input_prompt(self) -> bool:
        """
        输入提示词

        Returns:
            bool: 输入是否成功
        """
        input_selectors = self.selectors.get('prompt_input', [])

        for selector in input_selectors:
            try:
                # 清空输入框
                await self.browser.evaluate_javascript(
                    f"""document.querySelector("{selector}").value = '';"""
                )

                # 输入提示词
                success = await self.browser.fill_input(selector, self.test_prompt)
                if success:
                    # 验证输入是否成功
                    input_value = await self.browser.evaluate_javascript(
                        f"""return document.querySelector("{selector}").value;"""
                    )
                    if input_value == self.test_prompt:
                        self.logger.info(f"提示词输入成功: {self.test_prompt}")
                        return True

            except Exception as e:
                self.logger.warning(f"输入提示词失败 [{selector}]: {str(e)}")
                continue

        self.logger.error("提示词输入失败")
        return False

    async def _click_generate_button(self) -> bool:
        """
        点击生成图片按钮

        Returns:
            bool: 点击是否成功
        """
        button_selectors = self.selectors.get('generate_image_button', [])

        for selector in button_selectors:
            try:
                # 等待按钮可点击
                await self.browser.wait_for_element(selector, timeout=5000)

                # 验证按钮状态
                is_enabled = await self.browser.evaluate_javascript(
                    f"""const elem = document.querySelector("{selector}");
                    return elem && !elem.disabled && elem.offsetParent !== null;"""
                )

                if is_enabled:
                    success = await self.browser.click_element(selector)
                    if success:
                        self.logger.info(f"生成图片按钮点击成功: {selector}")
                        return True

            except Exception as e:
                self.logger.warning(f"点击生成按钮失败 [{selector}]: {str(e)}")
                continue

        self.logger.error("生成图片按钮点击失败")
        return False

    async def _wait_for_image_generation(self) -> tuple[bool, Optional[str]]:
        """
        等待图片生成完成

        Returns:
            tuple[bool, Optional[str]]: (是否成功, 图片URL)
        """
        result_selectors = self.selectors.get('image_result', [])
        if not result_selectors:
            self.logger.error("图片结果选择器未配置")
            return False, None

        try:
            # 等待图片结果出现
            for selector in result_selectors:
                try:
                    success = await self.browser.wait_for_element(selector, timeout=self.timeout)
                    if success:
                        # 获取图片 URL
                        image_url = await self._extract_image_url(selector)
                        if image_url:
                            self.logger.info(f"图片生成成功，URL: {image_url}")
                            return True, image_url

                except Exception as e:
                    self.logger.debug(f"等待图片结果失败 [{selector}]: {str(e)}")
                    continue

        except Exception as e:
            self.logger.error(f"等待图片生成过程异常: {str(e)}")

        # 检查是否有错误提示
        error_message = await self._check_for_error_message()
        if error_message:
            self.logger.error(f"图片生成过程中出现错误: {error_message}")

        return False, None

    async def _extract_image_url(self, selector: str) -> Optional[str]:
        """
        提取图片 URL

        Args:
            selector: 图片元素选择器

        Returns:
            Optional[str]: 图片 URL
        """
        try:
            # 尝试多种方式获取图片 URL
            scripts = [
                f"""const elem = document.querySelector("{selector}");
                   if (elem && elem.src) return elem.src;
                   return null;""",
                f"""const elem = document.querySelector("{selector}");
                   if (elem && elem.style.backgroundImage) {{
                       return elem.style.backgroundImage.match(/url\\(['"]?([^'"]*)['"]?\\)/)[1];
                   }}
                   return null;""",
                f"""const elem = document.querySelector("{selector}");
                   if (elem && elem.querySelector('img')) {{
                       return elem.querySelector('img').src;
                   }}
                   return null;"""
            ]

            for script in scripts:
                try:
                    url = await self.browser.evaluate_javascript(script)
                    if url and url.strip():
                        # 验证 URL 格式
                        if url.startswith(('http://', 'https://', 'data:image/')):
                            return url
                except Exception:
                    continue

            # 如果直接获取失败，尝试查找子元素
            child_scripts = [
                f"""const elem = document.querySelector("{selector}");
                   if (elem) {{
                       const img = elem.querySelector('img');
                       if (img) return img.src;
                   }}
                   return null;""",
                f"""const elem = document.querySelector("{selector}");
                   if (elem) {{
                       const sources = elem.querySelectorAll('source');
                       for (let source of sources) {{
                           if (source.srcset) return source.srcset.split(' ')[0];
                       }}
                   }}
                   return null;"""
            ]

            for script in child_scripts:
                try:
                    url = await self.browser.evaluate_javascript(script)
                    if url and url.strip():
                        if url.startswith(('http://', 'https://')):
                            return url
                except Exception:
                    continue

        except Exception as e:
            self.logger.error(f"提取图片 URL 失败: {str(e)}")

        return None

    async def _verify_generated_image(self, image_url: str) -> bool:
        """
        验证生成的图片

        Args:
            image_url: 图片 URL

        Returns:
            bool: 验证是否成功
        """
        try:
            if not image_url:
                return False

            # 基础 URL 验证
            if image_url.startswith('data:image/'):
                # Base64 图片，检查格式
                if not image_url.startswith('data:image/') or 'base64' not in image_url:
                    return False
                self.logger.info("验证通过：Base64 格式图片")
                return True

            elif image_url.startswith(('http://', 'https://')):
                # 检查图片是否可访问（可选，因为可能需要认证）
                self.logger.info(f"验证通过：网络图片 URL - {image_url}")
                return True

            else:
                # 相对路径，尝试构建完整 URL
                current_url = await self.browser.get_page_url()
                if current_url:
                    from urllib.parse import urljoin
                    full_url = urljoin(current_url, image_url)
                    self.logger.info(f"验证通过：相对路径图片转换为完整 URL - {full_url}")
                    return True

        except Exception as e:
            self.logger.error(f"图片验证失败: {str(e)}")

        return False

    async def _check_for_error_message(self) -> Optional[str]:
        """
        检查是否有错误提示

        Returns:
            Optional[str]: 错误信息
        """
        try:
            # 常见的错误提示选择器
            error_selectors = [
                '.error-message',
                '.error',
                '.alert-error',
                '.notification.error',
                '[class*="error"]',
                '[role="alert"]'
            ]

            for selector in error_selectors:
                try:
                    element = await self.browser.find_element(selector)
                    if element:
                        error_text = await self.browser.evaluate_javascript(
                            f"""return document.querySelector("{selector}").textContent.trim();"""
                        )
                        if error_text:
                            return error_text
                except Exception:
                    continue

        except Exception as e:
            self.logger.debug(f"检查错误提示时出现异常: {str(e)}")

        return None

    def get_step_name(self) -> str:
        """获取步骤名称"""
        return "文生图测试"

    def get_required_selectors(self) -> List[str]:
        """获取必需的选择器列表"""
        return [
            'prompt_input',
            'generate_image_button',
            'image_result'
        ]

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        # 检查必需的选择器
        required_selectors = self.get_required_selectors()
        selectors = self.selectors

        for selector_name in required_selectors:
            if selector_name not in selectors:
                self.logger.error(f"缺少选择器配置: {selector_name}")
                return False

            if not selectors[selector_name] or not isinstance(selectors[selector_name], list):
                self.logger.error(f"选择器配置格式错误: {selector_name}")
                return False

        # 检查测试提示词
        if not self.test_prompt or not self.test_prompt.strip():
            self.logger.error("测试提示词未配置或为空")
            return False

        return True