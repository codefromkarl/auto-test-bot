"""
带度量功能的混合定位器 - 支持命中策略统计和回退率度量

提供可度量的元素定位，用于推动前端补充 data-testid。
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from playwright.async_api import Page, Locator
from .data_testid_locator import DataTestIdLocator


class MetricsHybridLocator:
    """带度量功能的混合定位器"""

    def __init__(self, page: Page, config: dict = None):
        """
        初始化度量混合定位器

        Args:
            page: Playwright 页面对象
            config: 定位策略配置
        """
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.data_testid = DataTestIdLocator(page)
        self.config = config or self._get_default_config()

        # 度量数据
        self.metrics = {
            'total_locations': 0,
            'data_testid_hits': 0,
            'fallback_hits': 0,
            'location_failures': 0,
            'element_stats': {},  # 每个元素的详细统计
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S')
        }

        # B 流程必需的 data-testid 契约
        self.required_testids = {
            'navigation': ['nav-ai-create-tab', 'nav-text-image-tab'],
            'text_image_flow': [
                'prompt-textarea', 'prompt-input',
                'generate-image-button',
                'loading-indicator',
                'image-result', 'generated-image',
                'error-message'
            ],
            'video_flow': [
                'generate-video-button',
                'video-result', 'generated-video'
            ]
        }

    def _get_default_config(self) -> dict:
        """获取默认的定位策略配置（兼容原有）"""
        return {
            "prompt_input": [
                "[data-testid='prompt-input']",
                "[data-testid='prompt-textarea']",
                "textarea[placeholder*='提示']",
                "textarea[placeholder*='描述']",
                ".arco-textarea",
                "textarea:first-of-type"
            ],
            "generate_image_button": [
                "[data-testid='generate-image-button']",
                "[data-testid='generate-button']",
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
            ]
        }

    async def locate(self, element_name: str, timeout: int = 10000) -> Optional[Locator]:
        """
        使用多策略定位元素（带度量）

        Args:
            element_name: 元素名称（对应配置中的键）
            timeout: 超时时间

        Returns:
            Optional[Locator]: 找到的元素定位器，失败返回 None
        """
        self.metrics['total_locations'] += 1

        # 初始化元素统计
        if element_name not in self.metrics['element_stats']:
            self.metrics['element_stats'][element_name] = {
                'attempts': 0,
                'successful_strategy': None,
                'strategy_type': None,  # 'data_testid' or 'fallback'
                'strategies_tried': [],
                'match_count': 0
            }

        element_stats = self.metrics['element_stats'][element_name]
        element_stats['attempts'] += 1

        strategies = self.config.get(element_name, [])

        if not strategies:
            self.logger.warning(f"未找到元素 '{element_name}' 的定位策略")
            self.metrics['location_failures'] += 1
            return None

        self.logger.debug(f"尝试定位元素 '{element_name}'，共 {len(strategies)} 种策略")

        for i, strategy in enumerate(strategies):
            try:
                element_stats['strategies_tried'].append(strategy)
                self.logger.debug(f"策略 {i+1}/{len(strategies)}: {strategy}")

                # 如果是 data-testid 策略，优先使用并记录
                if "[data-testid=" in strategy:
                    testid = self._extract_testid_from_strategy(strategy)
                    element = self.data_testid.get_by_testid(testid)

                    # 使用正确的 Playwright API 进行等待
                    try:
                        await element.wait_for(state='attached', timeout=2000)
                        count = await element.count()
                        if count > 0:
                            # 记录成功
                            element_stats['successful_strategy'] = strategy
                            element_stats['strategy_type'] = 'data_testid'
                            element_stats['match_count'] = count
                            self.metrics['data_testid_hits'] += 1

                            self.logger.info(f"✓ data-testid 命中 '{element_name}': {strategy} (匹配{count}个)")
                            return element.first if count > 1 else element
                    except Exception as wait_e:
                        self.logger.debug(f"data-testid 等待超时: {strategy}, 错误: {str(wait_e)}")
                        continue
                else:
                    # 其他策略
                    element = self.page.locator(strategy)
                    count = await element.count()

                    if count > 0:
                        visible_element = element.first
                        if i < 3:  # 前几个策略用于交互元素
                            if await visible_element.is_visible():
                                element_stats['successful_strategy'] = strategy
                                element_stats['strategy_type'] = 'fallback'
                                element_stats['match_count'] = count
                                self.metrics['fallback_hits'] += 1

                                self.logger.info(f"✓ 回退命中 '{element_name}': {strategy} (匹配{count}个)")
                                return visible_element
                        else:
                            element_stats['successful_strategy'] = strategy
                            element_stats['strategy_type'] = 'fallback'
                            element_stats['match_count'] = count
                            self.metrics['fallback_hits'] += 1

                            self.logger.info(f"✓ 回退命中 '{element_name}': {strategy} (匹配{count}个)")
                            return element.first

            except Exception as e:
                self.logger.debug(f"策略失败: {strategy}, 错误: {str(e)}")
                continue

        # 所有策略都失败
        self.metrics['location_failures'] += 1
        element_stats['successful_strategy'] = None
        element_stats['strategy_type'] = 'failed'
        self.logger.error(f"✗ 所有定位策略都失败了: {element_name}")
        return None

    def _extract_testid_from_strategy(self, strategy: str) -> str:
        """从策略字符串中提取 data-testid 值"""
        if "'" in strategy:
            return strategy.split("'")[1]
        elif '"' in strategy:
            return strategy.split('"')[1]
        return strategy

    async def locate_and_wait(self, element_name: str, state: str = "visible", timeout: int = 10000) -> Optional[Locator]:
        """
        定位元素并等待其达到指定状态（带度量）
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
        定位并点击元素（带度量）
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return False

        try:
            try:
                await element.scroll_into_view_if_needed(timeout=timeout)
            except Exception:
                pass
            await element.click(timeout=timeout)
            self.logger.info(f"成功点击元素: {element_name}")
            return True
        except Exception as e:
            self.logger.error(f"点击元素失败: {element_name}, 错误: {str(e)}")
            return False

    async def fill(self, element_name: str, value: str, timeout: int = 10000) -> bool:
        """
        定位并填充输入框（带度量）
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return False

        try:
            try:
                await element.scroll_into_view_if_needed(timeout=timeout)
            except Exception:
                pass
            await element.fill(value, timeout=timeout)
            self.logger.info(f"成功填充元素: {element_name} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"填充元素失败: {element_name}, 错误: {str(e)}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取度量统计

        Returns:
            Dict[str, Any]: 度量数据
        """
        total = self.metrics['total_locations']
        data_testid_hits = self.metrics['data_testid_hits']
        fallback_hits = self.metrics['fallback_hits']
        failures = self.metrics['location_failures']

        return {
            'session_id': self.metrics['session_id'],
            'total_locations': total,
            'data_testid_hits': data_testid_hits,
            'fallback_hits': fallback_hits,
            'location_failures': failures,
            'data_testid_hit_rate': round(data_testid_hits / total * 100, 2) if total > 0 else 0,
            'fallback_rate': round(fallback_hits / total * 100, 2) if total > 0 else 0,
            'failure_rate': round(failures / total * 100, 2) if total > 0 else 0,
            'element_details': self.metrics['element_stats'],
            'required_testids_coverage': self._calculate_required_coverage()
        }

    def _calculate_required_coverage(self) -> Dict[str, Any]:
        """计算必需 data-testid 的覆盖率"""
        coverage = {
            'navigation': {'required': len(self.required_testids['navigation']), 'covered': 0},
            'text_image_flow': {'required': len(self.required_testids['text_image_flow']), 'covered': 0},
            'video_flow': {'required': len(self.required_testids['video_flow']), 'covered': 0}
        }

        all_testids_hit = set()

        # 收集所有命中的 data-testid
        for element_name, stats in self.metrics['element_stats'].items():
            if stats['strategy_type'] == 'data_testid' and stats['successful_strategy']:
                testid = self._extract_testid_from_strategy(stats['successful_strategy'])
                all_testids_hit.add(testid)

        # 计算覆盖率
        for category, testids in self.required_testids.items():
            for testid in testids:
                if testid in all_testids_hit:
                    coverage[category]['covered'] += 1

        # 计算百分比
        for category in coverage:
            required = coverage[category]['required']
            covered = coverage[category]['covered']
            coverage[category]['coverage_rate'] = round(covered / required * 100, 2) if required > 0 else 0

        return coverage

    def validate_ci_gates(self) -> Dict[str, Any]:
        """
        验证 CI 门禁条件

        Returns:
            Dict[str, Any]: 门禁验证结果
        """
        metrics = self.get_metrics()
        coverage = metrics['required_testids_coverage']

        # CI 门禁条件
        gates = {
            'data_testid_hit_rate_min': 80.0,  # 整体命中率 >= 80%
            'fallback_rate_max': 20.0,        # 回退率 <= 20%
            'required_navigation_coverage': 100.0,  # 导航必需元素 100% 覆盖
            'required_text_image_coverage': 100.0,  # 文生图必需元素 100% 覆盖
            'required_video_coverage': 100.0,       # 视频流程必需元素 100% 覆盖
        }

        results = {
            'passed': True,
            'failures': [],
            'warnings': [],
            'metrics': metrics
        }

        # 检查各个门禁条件
        if metrics['data_testid_hit_rate'] < gates['data_testid_hit_rate_min']:
            results['passed'] = False
            results['failures'].append(
                f"data-testid 命中率 {metrics['data_testid_hit_rate']}% 低于要求 {gates['data_testid_hit_rate_min']}%"
            )

        if metrics['fallback_rate'] > gates['fallback_rate_max']:
            results['passed'] = False
            results['failures'].append(
                f"回退率 {metrics['fallback_rate']}% 超过限制 {gates['fallback_rate_max']}%"
            )

        # 检查必需元素覆盖率
        for category in ['navigation', 'text_image_flow', 'video_flow']:
            if category not in coverage:
                continue

            coverage_rate = coverage[category]['coverage_rate']
            required_rate = gates.get(f'required_{category}_coverage', 100)

            if coverage_rate < required_rate:
                results['passed'] = False
                results['failures'].append(
                    f"{category} 必需 data-testid 覆盖率 {coverage_rate}% 低于要求 {required_rate}%"
                )
            elif coverage_rate < 100:
                results['warnings'].append(
                    f"{category} 部分必需 data-testid 未覆盖 ({coverage_rate}%)"
                )

        return results

    def get_missing_required_testids(self) -> Dict[str, List[str]]:
        """
        获取缺失的必需 data-testid

        Returns:
            Dict[str, List[str]]: 按类别分组的缺失 testid
        """
        missing = {}
        all_testids_hit = set()

        # 收集所有命中的 data-testid
        for element_name, stats in self.metrics['element_stats'].items():
            if stats['strategy_type'] == 'data_testid' and stats['successful_strategy']:
                testid = self._extract_testid_from_strategy(stats['successful_strategy'])
                all_testids_hit.add(testid)

        # 找出缺失的
        for category, testids in self.required_testids.items():
            category_missing = []
            for testid in testids:
                if testid not in all_testids_hit:
                    category_missing.append(testid)

            if category_missing:
                missing[category] = category_missing

        return missing

    async def is_visible(self, element_name: str, timeout: int = 5000) -> bool:
        """
        检查元素是否可见（带度量）
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return False

        try:
            await element.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    async def wait_for_disappear(self, element_name: str, timeout: int = 10000) -> bool:
        """
        等待元素消失（带度量）
        """
        element = await self.locate(element_name, timeout)
        if not element:
            return True

        try:
            await element.wait_for(state="hidden", timeout=timeout)
            return True
        except:
            return False

    def reset_metrics(self):
        """重置度量数据"""
        self.metrics = {
            'total_locations': 0,
            'data_testid_hits': 0,
            'fallback_hits': 0,
            'location_failures': 0,
            'element_stats': {},
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
