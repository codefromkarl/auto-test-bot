"""
DOM 调试器
通过 MCP 检查和分析 DOM 状态
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


class DOMSnapshot:
    """DOM 快照类"""

    def __init__(self, data: Dict[str, Any]):
        """
        初始化 DOM 快照

        Args:
            data: DOM 数据字典
        """
        self.snapshot_id = data.get('snapshot_id')
        self.url = data.get('url', '')
        self.title = data.get('title', '')
        self.element_count = data.get('element_count', 0)
        self.visible_elements = data.get('visible_elements', [])
        self.hidden_elements = data.get('hidden_elements', [])
        self.computed_styles = data.get('computed_styles', {})
        self.layout_info = data.get('layout_info', {})
        self.viewport_info = data.get('viewport_info', {})
        self.timestamp = data.get('timestamp', datetime.now().isoformat())

    def has_layout_issues(self) -> bool:
        """检查是否有布局问题"""
        return (
            len(self.hidden_elements) > 50 or  # 隐藏元素过多
            self.element_count > 10000 or     # 元素总数过多
            self._has_overlay_elements()       # 有覆盖元素
        )

    def _has_overlay_elements(self) -> bool:
        """检查是否有覆盖元素"""
        # 简化的覆盖元素检测
        return any(
            'position' in style.get('position', '') and
            style.get('z-index', 0) > 1000
            for style in self.computed_styles.values()
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'snapshot_id': self.snapshot_id,
            'url': self.url,
            'title': self.title,
            'element_count': self.element_count,
            'visible_element_count': len(self.visible_elements),
            'hidden_element_count': len(self.hidden_elements),
            'has_layout_issues': self.has_layout_issues(),
            'viewport_info': self.viewport_info,
            'timestamp': self.timestamp
        }


class DOMDebugger:
    """DOM 调试器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 DOM 调试器

        Args:
            config: 配置字典
        """
        self.config = config.get('dom_debug', {})
        self.logger = logging.getLogger(__name__)

        # 调试配置
        self.enabled = self.config.get('enabled', True)
        self.max_depth = self.config.get('max_depth', 10)
        self.capture_attributes = self.config.get('capture_attributes', True)
        self.capture_text_content = self.config.get('capture_text_content', True)

        # DOM 快照
        self.snapshots: List[DOMSnapshot] = []

    def create_snapshot(self, url: str, dom_data: Dict[str, Any]) -> Optional[DOMSnapshot]:
        """
        创建 DOM 快照

        Args:
            url: 页面 URL
            dom_data: DOM 数据

        Returns:
            Optional[DOMSnapshot]: DOM 快照
        """
        if not self.enabled:
            return None

        try:
            snapshot_data = {
                'snapshot_id': f"snapshot_{int(datetime.now().timestamp() * 1000)}",
                'url': url,
                'title': dom_data.get('title', ''),
                'element_count': self._count_elements(dom_data),
                'visible_elements': self._get_visible_elements(dom_data),
                'hidden_elements': self._get_hidden_elements(dom_data),
                'computed_styles': self._get_computed_styles(dom_data),
                'layout_info': self._get_layout_info(dom_data),
                'viewport_info': self._get_viewport_info(dom_data)
            }

            snapshot = DOMSnapshot(snapshot_data)
            self.snapshots.append(snapshot)

            self.logger.info(f"DOM 快照已创建: {snapshot.element_count} 个元素")
            return snapshot

        except Exception as e:
            self.logger.error(f"创建 DOM 快照失败: {str(e)}")
            return None

    def _count_elements(self, dom_data: Dict[str, Any]) -> int:
        """计算元素数量"""
        # 模拟计算，实际实现会解析真实 DOM
        import random
        return random.randint(500, 2000)

    def _get_visible_elements(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取可见元素"""
        # 模拟可见元素数据
        visible_elements = []
        element_types = ['div', 'button', 'input', 'img', 'span', 'p']

        for i in range(20):
            visible_elements.append({
                'tag': element_types[i % len(element_types)],
                'id': f'visible_elem_{i}',
                'class': f'visible-class-{i}',
                'text': f'Visible Element {i}' if self.capture_text_content else '',
                'rect': {
                    'x': i * 50,
                    'y': i * 30,
                    'width': 100 + i * 10,
                    'height': 50 + i * 5
                }
            })

        return visible_elements

    def _get_hidden_elements(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取隐藏元素"""
        # 模拟隐藏元素数据
        hidden_elements = []

        for i in range(10):
            hidden_elements.append({
                'tag': 'div',
                'id': f'hidden_elem_{i}',
                'class': f'hidden-class-{i}',
                'display': 'none',
                'visibility': 'hidden'
            })

        return hidden_elements

    def _get_computed_styles(self, dom_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取计算样式"""
        # 模拟计算样式数据
        styles = {}

        for i in range(15):
            element_id = f'elem_{i}'
            styles[element_id] = {
                'position': 'static' if i % 2 == 0 else 'relative',
                'display': 'block',
                'visibility': 'visible',
                'z-index': i,
                'opacity': 1.0,
                'color': f'rgb({i * 10}, {i * 15}, {i * 20})',
                'background-color': f'rgb({255 - i * 10}, {255 - i * 15}, {255 - i * 20})'
            }

        return styles

    def _get_layout_info(self, dom_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取布局信息"""
        return {
            'document_width': 1920,
            'document_height': 3000,
            'scroll_width': 1920,
            'scroll_height': 3000,
            'client_width': 1920,
            'client_height': 1080
        }

    def _get_viewport_info(self, dom_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取视口信息"""
        return {
            'width': 1920,
            'height': 1080,
            'scale': 1.0,
            'orientation': 'landscape'
        }

    def find_element(self, selector: str, snapshot: Optional[DOMSnapshot] = None) -> Optional[Dict[str, Any]]:
        """
        查找元素

        Args:
            selector: CSS 选择器
            snapshot: DOM 快照（可选）

        Returns:
            Optional[Dict[str, Any]]: 元素信息
        """
        if not self.enabled:
            return None

        target_snapshot = snapshot or (self.snapshots[-1] if self.snapshots else None)
        if not target_snapshot:
            return None

        # 模拟元素查找
        # 实际实现会使用 CSS 选择器解析
        for element in target_snapshot.visible_elements:
            if selector in element.get('class', '') or selector == element.get('id', ''):
                return element

        return None

    def check_element_visibility(self, element_info: Dict[str, Any]) -> bool:
        """
        检查元素可见性

        Args:
            element_info: 元素信息

        Returns:
            bool: 元素是否可见
        """
        if not element_info:
            return False

        rect = element_info.get('rect', {})
        if not rect:
            return False

        # 简化的可见性检查
        return (
            rect.get('width', 0) > 0 and
            rect.get('height', 0) > 0 and
            rect.get('x', -1) >= 0 and
            rect.get('y', -1) >= 0
        )

    def get_element_position(self, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取元素位置信息

        Args:
            element_info: 元素信息

        Returns:
            Dict[str, Any]: 位置信息
        """
        if not element_info:
            return {}

        rect = element_info.get('rect', {})
        return {
            'x': rect.get('x', 0),
            'y': rect.get('y', 0),
            'width': rect.get('width', 0),
            'height': rect.get('height', 0),
            'top': rect.get('y', 0),
            'left': rect.get('x', 0),
            'right': rect.get('x', 0) + rect.get('width', 0),
            'bottom': rect.get('y', 0) + rect.get('height', 0)
        }

    def check_element_overlap(self, element1: Dict[str, Any], element2: Dict[str, Any]) -> bool:
        """
        检查两个元素是否重叠

        Args:
            element1: 第一个元素
            element2: 第二个元素

        Returns:
            bool: 是否重叠
        """
        pos1 = self.get_element_position(element1)
        pos2 = self.get_element_position(element2)

        if not pos1 or not pos2:
            return False

        return not (
            pos1['right'] <= pos2['left'] or
            pos1['left'] >= pos2['right'] or
            pos1['bottom'] <= pos2['top'] or
            pos1['top'] >= pos2['bottom']
        )

    def analyze_layout_issues(self, snapshot: Optional[DOMSnapshot] = None) -> Dict[str, Any]:
        """
        分析布局问题

        Args:
            snapshot: DOM 快照（可选）

        Returns:
            Dict[str, Any]: 布局问题分析
        """
        target_snapshot = snapshot or (self.snapshots[-1] if self.snapshots else None)
        if not target_snapshot:
            return {'error': '没有 DOM 快照数据'}

        issues = {
            'hidden_elements': len(target_snapshot.hidden_elements),
            'element_count': target_snapshot.element_count,
            'viewport_coverage': self._calculate_viewport_coverage(target_snapshot),
            'potential_overlaps': self._find_potential_overlaps(target_snapshot),
            'recommendations': []
        }

        # 生成建议
        if issues['hidden_elements'] > 100:
            issues['recommendations'].append("隐藏元素过多，建议清理无用的 DOM 元素")

        if issues['element_count'] > 5000:
            issues['recommendations'].append("DOM 元素过多，建议优化页面结构")

        if issues['potential_overlaps'] > 5:
            issues['recommendations'].append("检测到可能的元素重叠，建议检查 CSS 定位")

        if issues['viewport_coverage'] < 50:
            issues['recommendations'].append("视口利用率低，建议优化布局")

        return issues

    def _calculate_viewport_coverage(self, snapshot: DOMSnapshot) -> float:
        """计算视口覆盖率"""
        if not snapshot.visible_elements:
            return 0.0

        total_area = 0
        viewport_area = 1920 * 1080  # 假设视口大小

        for element in snapshot.visible_elements:
            rect = element.get('rect', {})
            width = rect.get('width', 0)
            height = rect.get('height', 0)
            total_area += width * height

        return min(100.0, (total_area / viewport_area) * 100)

    def _find_potential_overlaps(self, snapshot: DOMSnapshot) -> int:
        """查找潜在的重叠元素"""
        overlap_count = 0
        elements = snapshot.visible_elements

        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                if self.check_element_overlap(elements[i], elements[j]):
                    overlap_count += 1

        return overlap_count

    def get_latest_snapshot(self) -> Optional[DOMSnapshot]:
        """
        获取最新的快照

        Returns:
            Optional[DOMSnapshot]: 最新的快照
        """
        return self.snapshots[-1] if self.snapshots else None

    def export_snapshots(self, filename: str, format_type: str = 'json'):
        """
        导出快照数据到文件

        Args:
            filename: 文件名
            format_type: 格式类型 (json, csv)
        """
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'snapshot_count': len(self.snapshots),
                'snapshots': [snapshot.to_dict() for snapshot in self.snapshots]
            }

            if format_type.lower() == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            elif format_type.lower() == 'csv':
                # 简化的 CSV 导出
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'snapshot_id', 'url', 'title', 'element_count',
                        'visible_element_count', 'hidden_element_count',
                        'has_layout_issues', 'timestamp'
                    ])
                    for snapshot in self.snapshots:
                        writer.writerow([
                            snapshot.snapshot_id, snapshot.url, snapshot.title,
                            snapshot.element_count, len(snapshot.visible_elements),
                            len(snapshot.hidden_elements), snapshot.has_layout_issues(),
                            snapshot.timestamp
                        ])

            self.logger.info(f"DOM 快照数据已导出到: {filename}")

        except Exception as e:
            self.logger.error(f"导出 DOM 快照数据失败: {str(e)}")

    def clear_snapshots(self):
        """清除所有快照"""
        self.snapshots.clear()
        self.logger.info("DOM 快照数据已清除")