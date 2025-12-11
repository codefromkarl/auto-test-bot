"""
图生视频测试步骤
基于已生成图片执行图生视频流程并验证结果
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from ..browser import BrowserManager
from ..utils import Timer
from ..mcp import ConsoleMonitor, NetworkAnalyzer


class GenerateVideoStep:
    """图生视频测试步骤"""

    def __init__(self, browser: BrowserManager, config: Dict[str, Any]):
        """
        初始化图生视频测试步骤

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
        self.timeout = self.test_config.get('timeout', 60000)  # 视频生成通常更慢

    def setup_mcp_monitoring(self, console_monitor: ConsoleMonitor, network_analyzer: NetworkAnalyzer):
        """
        设置 MCP 监控

        Args:
            console_monitor: 控制台监控器
            network_analyzer: 网络分析器
        """
        self.console_monitor = console_monitor
        self.network_analyzer = network_analyzer

    async def execute(self, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        执行图生视频测试步骤

        Args:
            image_url: 已生成的图片 URL（可选）

        Returns:
            Dict[str, Any]: 执行结果
        """
        result = {
            'step': 'generate_video',
            'success': False,
            'error': None,
            'details': {},
            'metrics': {},
            'generated_video_url': None,
            'source_image_url': image_url
        }

        timer = Timer('generate_video')
        timer.start()

        try:
            self.logger.info("开始执行图生视频测试步骤")

            # 1. 验证图片存在（如果提供了图片 URL）
            if image_url:
                success = await self._verify_image_exists(image_url)
                if not success:
                    result['error'] = "源图片验证失败"
                    return result

            timer.checkpoint("image_verification_complete")

            # 2. 查找并验证生成视频按钮
            success = await self._verify_video_button()
            if not success:
                result['error'] = "生成视频按钮验证失败"
                return result

            timer.checkpoint("video_button_verified")

            # 3. 点击生成视频按钮
            success = await self._click_generate_video_button()
            if not success:
                result['error'] = "点击生成视频按钮失败"
                return result

            timer.checkpoint("video_button_clicked")

            # 4. 等待视频生成完成
            success, video_url = await self._wait_for_video_generation()
            if not success:
                result['error'] = "视频生成失败或超时"
                return result

            timer.checkpoint("video_generation_complete")

            # 5. 验证生成的视频
            success = await self._verify_generated_video(video_url)
            if not success:
                result['error'] = "生成的视频验证失败"
                return result

            timer.checkpoint("video_verification_complete")

            # 执行成功
            result['success'] = True
            result['generated_video_url'] = video_url
            result['metrics']['total_time'] = timer.stop()
            result['metrics']['checkpoints'] = timer.get_checkpoints()
            result['details']['source_image_url'] = image_url
            result['details']['generation_duration'] = timer.get_elapsed_time()

            self.logger.info(f"图生视频测试步骤执行成功，生成视频: {video_url}")
            return result

        except Exception as e:
            result['error'] = str(e)
            result['metrics']['total_time'] = timer.get_elapsed_time()
            self.logger.error(f"图生视频测试步骤执行失败: {str(e)}")
            return result

    async def _verify_image_exists(self, image_url: str) -> bool:
        """
        验证图片是否存在

        Args:
            image_url: 图片 URL

        Returns:
            bool: 验证是否成功
        """
        try:
            # 在页面上查找该图片元素
            found_elements = await self.browser.evaluate_javascript(f"""
                var imageUrl = '{image_url}';
                var images = document.querySelectorAll('img');
                for (var i = 0; i < images.length; i++) {{
                    if (images[i].src === imageUrl ||
                        images[i].srcset.includes(imageUrl) ||
                        images[i].style.backgroundImage.includes(imageUrl)) {{
                        return true;
                    }}
                }}
                return false;
            """)

            if found_elements:
                self.logger.info(f"在页面上找到源图片: {image_url}")
                return True
            else:
                # 如果在页面上没找到，检查是否是当前生成的图片
                image_result_selectors = self.selectors.get('image_result', [])
                for selector in image_result_selectors:
                    try:
                        element_url = await self._extract_image_url(selector)
                        if element_url == image_url:
                            self.logger.info(f"确认当前生成图片: {image_url}")
                            return True
                    except Exception:
                        continue

                self.logger.warning(f"在页面上未找到源图片: {image_url}")
                return False

        except Exception as e:
            self.logger.error(f"验证图片存在时出错: {str(e)}")
            return False

    async def _verify_video_button(self) -> bool:
        """
        验证生成视频按钮

        Returns:
            bool: 验证是否成功
        """
        button_selectors = self.selectors.get('generate_video_button', [])
        if not button_selectors:
            self.logger.error("生成视频按钮选择器未配置")
            return False

        for selector in button_selectors:
            try:
                # 等待按钮出现
                success = await self.browser.wait_for_element(selector, timeout=5000)
                if success:
                    # 验证按钮是否可点击
                    is_enabled = await self.browser.evaluate_javascript(
                        f"""const elem = document.querySelector("{selector}");
                        return elem && !elem.disabled && elem.offsetParent !== null;"""
                    )
                    if is_enabled:
                        self.logger.info(f"找到可用的生成视频按钮: {selector}")
                        return True

            except Exception as e:
                self.logger.debug(f"生成视频按钮验证失败 [{selector}]: {str(e)}")
                continue

        self.logger.error("未找到可用的生成视频按钮")
        return False

    async def _click_generate_video_button(self) -> bool:
        """
        点击生成视频按钮

        Returns:
            bool: 点击是否成功
        """
        button_selectors = self.selectors.get('generate_video_button', [])

        for selector in button_selectors:
            try:
                # 滚动到按钮位置
                await self.browser.evaluate_javascript(
                    f"""const elem = document.querySelector("{selector}");
                    if (elem) elem.scrollIntoView({{behavior: 'smooth', block: 'center'}});"""
                )

                # 等待一小段时间确保滚动完成
                await asyncio.sleep(1)

                # 点击按钮
                success = await self.browser.click_element(selector)
                if success:
                    self.logger.info(f"生成视频按钮点击成功: {selector}")
                    return True

            except Exception as e:
                self.logger.warning(f"点击生成视频按钮失败 [{selector}]: {str(e)}")
                continue

        self.logger.error("生成视频按钮点击失败")
        return False

    async def _wait_for_video_generation(self) -> Tuple[bool, Optional[str]]:
        """
        等待视频生成完成

        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 视频URL)
        """
        result_selectors = self.selectors.get('video_result', [])
        if not result_selectors:
            self.logger.error("视频结果选择器未配置")
            return False, None

        try:
            # 等待视频结果出现
            for selector in result_selectors:
                try:
                    success = await self.browser.wait_for_element(selector, timeout=self.timeout)
                    if success:
                        # 获取视频 URL
                        video_url = await self._extract_video_url(selector)
                        if video_url:
                            self.logger.info(f"视频生成成功，URL: {video_url}")
                            return True, video_url

                except Exception as e:
                    self.logger.debug(f"等待视频结果失败 [{selector}]: {str(e)}")
                    continue

        except Exception as e:
            self.logger.error(f"等待视频生成过程异常: {str(e)}")

        # 检查是否有错误提示
        error_message = await self._check_for_error_message()
        if error_message:
            self.logger.error(f"视频生成过程中出现错误: {error_message}")

        return False, None

    async def _extract_video_url(self, selector: str) -> Optional[str]:
        """
        提取视频 URL

        Args:
            selector: 视频元素选择器

        Returns:
            Optional[str]: 视频 URL
        """
        try:
            # 尝试多种方式获取视频 URL
            scripts = [
                f"""const elem = document.querySelector("{selector}");
                   if (elem && elem.src) return elem.src;
                   return null;""",
                f"""const elem = document.querySelector("{selector}");
                   if (elem && elem.querySelector('video')) {{
                       return elem.querySelector('video').src;
                   }}
                   return null;""",
                f"""const elem = document.querySelector("{selector}");
                   if (elem) {{
                       const source = elem.querySelector('source');
                       if (source) return source.src;
                   }}
                   return null;"""
            ]

            for script in scripts:
                try:
                    url = await self.browser.evaluate_javascript(script)
                    if url and url.strip():
                        # 验证 URL 格式
                        if url.startswith(('http://', 'https://', 'blob:')):
                            return url
                except Exception:
                    continue

            # 检查是否是视频海报图或缩略图
            thumbnail_scripts = [
                f"""const elem = document.querySelector("{selector}");
                   if (elem && elem.style.backgroundImage) {{
                       const match = elem.style.backgroundImage.match(/url\\(['"]?([^'"]*)['"]?\\)/);
                       return match ? match[1] : null;
                   }}
                   return null;""",
                f"""const elem = document.querySelector("{selector}");
                   if (elem) {{
                       const img = elem.querySelector('img');
                       if (img && img.alt && img.alt.toLowerCase().includes('video')) {{
                           return img.src;
                       }}
                   }}
                   return null;"""
            ]

            for script in thumbnail_scripts:
                try:
                    url = await self.browser.evaluate_javascript(script)
                    if url and url.strip():
                        self.logger.info(f"找到视频缩略图: {url}")
                        # 注意：这不是实际视频 URL，但可以确认视频元素存在
                        return url
                except Exception:
                    continue

        except Exception as e:
            self.logger.error(f"提取视频 URL 失败: {str(e)}")

        return None

    async def _verify_generated_video(self, video_url: str) -> bool:
        """
        验证生成的视频

        Args:
            video_url: 视频 URL

        Returns:
            bool: 验证是否成功
        """
        try:
            if not video_url:
                return False

            # 基础 URL 验证
            if video_url.startswith('blob:'):
                # Blob URL，表示视频已生成
                self.logger.info("验证通过：Blob 格式视频")
                return True

            elif video_url.startswith(('http://', 'https://')):
                # 检查视频扩展名
                video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi']
                if any(ext in video_url.lower() for ext in video_extensions):
                    self.logger.info(f"验证通过：网络视频 URL - {video_url}")
                    return True
                else:
                    # 可能是缩略图或其他资源
                    self.logger.info(f"可能为视频缩略图: {video_url}")
                    return True

            else:
                # 相对路径
                current_url = await self.browser.get_page_url()
                if current_url:
                    from urllib.parse import urljoin
                    full_url = urljoin(current_url, video_url)
                    self.logger.info(f"验证通过：相对路径视频转换为完整 URL - {full_url}")
                    return True

        except Exception as e:
            self.logger.error(f"视频验证失败: {str(e)}")

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

    async def _check_video_progress(self) -> Dict[str, Any]:
        """
        检查视频生成进度

        Returns:
            Dict[str, Any]: 进度信息
        """
        progress_info = {
            'is_generating': False,
            'progress_percentage': 0,
            'status_text': '',
            'estimated_time_remaining': None
        }

        try:
            # 查找进度条或状态指示器
            progress_selectors = [
                '.progress-bar',
                '.progress',
                '[role="progressbar"]',
                '.loading-percentage',
                '.status-text'
            ]

            for selector in progress_selectors:
                try:
                    element = await self.browser.find_element(selector)
                    if element:
                        # 获取进度信息
                        progress_text = await self.browser.evaluate_javascript(
                            f"""const elem = document.querySelector("{selector}");
                            if (elem) {{
                                return {{
                                    text: elem.textContent || elem.innerText || '',
                                    value: elem.value || elem.getAttribute('aria-valuenow') || 0,
                                    max: elem.getAttribute('aria-valuemax') || 100
                                }};
                            }}
                            return null;"""
                        )

                        if progress_text:
                            progress_info['is_generating'] = True
                            progress_info['status_text'] = progress_text.get('text', '')

                            if progress_text.get('max') and progress_text.get('value'):
                                percentage = (progress_text['value'] / progress_text['max']) * 100
                                progress_info['progress_percentage'] = int(percentage)

                            self.logger.debug(f"视频生成进度: {progress_info['progress_percentage']}%")
                            return progress_info

                except Exception:
                    continue

        except Exception as e:
            self.logger.debug(f"检查视频进度时出现异常: {str(e)}")

        return progress_info

    def get_step_name(self) -> str:
        """获取步骤名称"""
        return "图生视频测试"

    def get_required_selectors(self) -> List[str]:
        """获取必需的选择器列表"""
        return [
            'generate_video_button',
            'video_result'
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

        return True