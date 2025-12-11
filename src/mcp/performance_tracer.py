"""
性能追踪器
通过 MCP 收集和分析性能指标
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


class PerformanceTrace:
    """性能追踪数据类"""

    def __init__(self, data: Dict[str, Any]):
        """
        初始化性能追踪数据

        Args:
            data: 追踪数据字典
        """
        self.trace_id = data.get('trace_id')
        self.start_time = data.get('start_time')
        self.end_time = data.get('end_time')
        self.duration = data.get('duration', 0)
        self.page_load_time = data.get('page_load_time', 0)
        self.dom_content_loaded = data.get('dom_content_loaded', 0)
        self.first_paint = data.get('first_paint', 0)
        self.first_contentful_paint = data.get('first_contentful_paint', 0)
        self.largest_contentful_paint = data.get('largest_contentful_paint', 0)
        self.cumulative_layout_shift = data.get('cumulative_layout_shift', 0)
        self.first_input_delay = data.get('first_input_delay', 0)
        self.resources = data.get('resources', [])
        self.network_requests = data.get('network_requests', [])
        self.timestamp = data.get('timestamp', datetime.now().isoformat())

    def has_performance_issues(self) -> bool:
        """检查是否有性能问题"""
        return (
            self.page_load_time > 5000 or  # 页面加载时间过长
            self.first_contentful_paint > 3000 or  # 首次内容绘制过慢
            self.largest_contentful_paint > 4000 or  # 最大内容绘制过慢
            self.cumulative_layout_shift > 0.1 or  # 布局偏移过多
            self.first_input_delay > 100  # 首次输入延迟过长
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'trace_id': self.trace_id,
            'duration': self.duration,
            'page_load_time': self.page_load_time,
            'dom_content_loaded': self.dom_content_loaded,
            'first_paint': self.first_paint,
            'first_contentful_paint': self.first_contentful_paint,
            'largest_contentful_paint': self.largest_contentful_paint,
            'cumulative_layout_shift': self.cumulative_layout_shift,
            'first_input_delay': self.first_input_delay,
            'resource_count': len(self.resources),
            'network_request_count': len(self.network_requests),
            'has_performance_issues': self.has_performance_issues(),
            'timestamp': self.timestamp
        }


class PerformanceTracer:
    """性能追踪器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化性能追踪器

        Args:
            config: 配置字典
        """
        self.config = config.get('performance_tracing', {})
        self.logger = logging.getLogger(__name__)

        # 追踪配置
        self.enabled = self.config.get('enabled', True)
        self.trace_duration = self.config.get('trace_duration', 30000)
        self.tracing_categories = self.config.get('tracing_categories', [
            'devtools.timeline',
            'toplevel',
            'blink.console',
            'blink.user_timing',
            'netlog'
        ])
        self.trace_buffer_size = self.config.get('trace_buffer_size', 1000000)

        # 追踪数据
        self.traces: List[PerformanceTrace] = []
        self.is_tracing = False

    def start_tracing(self) -> bool:
        """
        开始性能追踪

        Returns:
            bool: 是否成功开始追踪
        """
        if not self.enabled:
            self.logger.info("性能追踪已禁用")
            return False

        try:
            self.logger.info("开始性能追踪")
            self.is_tracing = True

            # 实际实现中，这里会通过 MCP 启动 Chrome DevTools 的性能追踪
            # 目前返回 True 表示成功
            return True

        except Exception as e:
            self.logger.error(f"开始性能追踪失败: {str(e)}")
            return False

    def stop_tracing(self) -> Optional[PerformanceTrace]:
        """
        停止性能追踪并返回追踪数据

        Returns:
            Optional[PerformanceTrace]: 性能追踪数据
        """
        if not self.is_tracing:
            self.logger.warning("性能追踪未在运行")
            return None

        try:
            self.logger.info("停止性能追踪")
            self.is_tracing = False

            # 模拟获取性能数据
            # 实际实现中，这里会从 MCP 获取真实的性能追踪数据
            trace_data = self._collect_performance_data()
            trace = PerformanceTrace(trace_data)

            self.traces.append(trace)
            self.logger.info(f"性能追踪完成: {trace.page_load_time}ms")

            return trace

        except Exception as e:
            self.logger.error(f"停止性能追踪失败: {str(e)}")
            return None

    def _collect_performance_data(self) -> Dict[str, Any]:
        """
        收集性能数据

        Returns:
            Dict[str, Any]: 性能数据字典
        """
        # 模拟性能数据收集
        # 实际实现中会通过 MCP 从浏览器获取真实数据
        import time
        import random

        trace_id = f"trace_{int(time.time() * 1000)}"
        current_time = time.time() * 1000

        return {
            'trace_id': trace_id,
            'start_time': current_time - 10000,
            'end_time': current_time,
            'duration': 10000,
            'page_load_time': random.randint(2000, 8000),
            'dom_content_loaded': random.randint(1000, 5000),
            'first_paint': random.randint(500, 2000),
            'first_contentful_paint': random.randint(800, 3000),
            'largest_contentful_paint': random.randint(1500, 6000),
            'cumulative_layout_shift': random.uniform(0, 0.2),
            'first_input_delay': random.randint(20, 150),
            'resources': self._collect_resource_data(),
            'network_requests': self._collect_network_data()
        }

    def _collect_resource_data(self) -> List[Dict[str, Any]]:
        """收集资源数据"""
        # 模拟资源数据
        resources = []
        resource_types = ['script', 'stylesheet', 'image', 'font', 'document']

        for i in range(random.randint(10, 30)):
            resources.append({
                'name': f'resource_{i}',
                'type': random.choice(resource_types),
                'size': random.randint(1000, 500000),
                'duration': random.randint(50, 2000),
                'cached': random.choice([True, False])
            })

        return resources

    def _collect_network_data(self) -> List[Dict[str, Any]]:
        """收集网络数据"""
        # 模拟网络请求数据
        requests = []

        for i in range(random.randint(5, 15)):
            requests.append({
                'url': f'https://example.com/api/endpoint_{i}',
                'method': random.choice(['GET', 'POST']),
                'status': random.choice([200, 201, 400, 404, 500]),
                'duration': random.randint(100, 3000),
                'size': random.randint(500, 100000)
            })

        return requests

    def get_latest_trace(self) -> Optional[PerformanceTrace]:
        """
        获取最新的追踪数据

        Returns:
            Optional[PerformanceTrace]: 最新的追踪数据
        """
        return self.traces[-1] if self.traces else None

    def get_all_traces(self) -> List[PerformanceTrace]:
        """
        获取所有追踪数据

        Returns:
            List[PerformanceTrace]: 所有追踪数据
        """
        return self.traces.copy()

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            Dict[str, Any]: 性能摘要
        """
        if not self.traces:
            return {'error': '没有性能追踪数据'}

        latest_trace = self.get_latest_trace()
        if not latest_trace:
            return {'error': '无法获取最新追踪数据'}

        # 计算平均值
        avg_page_load = sum(t.page_load_time for t in self.traces) / len(self.traces)
        avg_fcp = sum(t.first_contentful_paint for t in self.traces) / len(self.traces)
        avg_lcp = sum(t.largest_contentful_paint for t in self.traces) / len(self.traces)

        return {
            'trace_count': len(self.traces),
            'latest_trace': latest_trace.to_dict(),
            'averages': {
                'page_load_time': avg_page_load,
                'first_contentful_paint': avg_fcp,
                'largest_contentful_paint': avg_lcp
            },
            'performance_score': self._calculate_performance_score(latest_trace),
            'recommendations': self._generate_recommendations(latest_trace)
        }

    def _calculate_performance_score(self, trace: PerformanceTrace) -> Dict[str, Any]:
        """
        计算性能评分

        Args:
            trace: 性能追踪数据

        Returns:
            Dict[str, Any]: 性能评分
        """
        scores = {}

        # FCP 评分 (0-100)
        if trace.first_contentful_paint <= 1800:
            scores['fcp'] = 100
        elif trace.first_contentful_paint <= 3000:
            scores['fcp'] = 90 - (trace.first_contentful_paint - 1800) * 10 / 1200
        else:
            scores['fcp'] = max(0, 90 - (trace.first_contentful_paint - 3000) * 20 / 2000)

        # LCP 评分 (0-100)
        if trace.largest_contentful_paint <= 2500:
            scores['lcp'] = 100
        elif trace.largest_contentful_paint <= 4000:
            scores['lcp'] = 90 - (trace.largest_contentful_paint - 2500) * 10 / 1500
        else:
            scores['lcp'] = max(0, 90 - (trace.largest_contentful_paint - 4000) * 20 / 6000)

        # CLS 评分 (0-100)
        if trace.cumulative_layout_shift <= 0.1:
            scores['cls'] = 100
        elif trace.cumulative_layout_shift <= 0.25:
            scores['cls'] = 90 - (trace.cumulative_layout_shift - 0.1) * 100 / 0.15
        else:
            scores['cls'] = max(0, 90 - (trace.cumulative_layout_shift - 0.25) * 200 / 0.75)

        # FID 评分 (0-100)
        if trace.first_input_delay <= 100:
            scores['fid'] = 100
        elif trace.first_input_delay <= 300:
            scores['fid'] = 90 - (trace.first_input_delay - 100) * 20 / 200
        else:
            scores['fid'] = max(0, 90 - (trace.first_input_delay - 300) * 30 / 700)

        # 总体评分
        scores['overall'] = (scores['fcp'] + scores['lcp'] + scores['cls'] + scores['fid']) / 4

        return scores

    def _generate_recommendations(self, trace: PerformanceTrace) -> List[str]:
        """
        生成性能优化建议

        Args:
            trace: 性能追踪数据

        Returns:
            List[str]: 优化建议列表
        """
        recommendations = []

        if trace.page_load_time > 5000:
            recommendations.append("页面加载时间过长，建议优化服务器响应时间或减少资源大小")

        if trace.first_contentful_paint > 3000:
            recommendations.append("首次内容绘制过慢，建议优化关键资源加载顺序")

        if trace.largest_contentful_paint > 4000:
            recommendations.append("最大内容绘制过慢，建议优化图片和关键 CSS")

        if trace.cumulative_layout_shift > 0.1:
            recommendations.append("布局偏移过多，建议为图片和广告设置固定尺寸")

        if trace.first_input_delay > 100:
            recommendations.append("首次输入延迟过长，建议减少 JavaScript 执行时间")

        if not recommendations:
            recommendations.append("性能表现良好，继续保持")

        return recommendations

    def has_performance_regression(self, baseline: Dict[str, float], threshold: float = 0.1) -> bool:
        """
        检查是否有性能回归

        Args:
            baseline: 基线性能数据
            threshold: 回归阈值

        Returns:
            bool: 是否有性能回归
        """
        if not self.traces:
            return False

        latest = self.get_latest_trace()
        if not latest:
            return False

        # 检查关键指标
        metrics = ['page_load_time', 'first_contentful_paint', 'largest_contentful_paint']

        for metric in metrics:
            baseline_value = baseline.get(metric, 0)
            current_value = getattr(latest, metric, 0)

            if baseline_value > 0:
                regression_ratio = (current_value - baseline_value) / baseline_value
                if regression_ratio > threshold:
                    self.logger.warning(f"检测到性能回归 {metric}: {regression_ratio:.2%}")
                    return True

        return False

    def export_traces(self, filename: str, format_type: str = 'json'):
        """
        导出追踪数据到文件

        Args:
            filename: 文件名
            format_type: 格式类型 (json, csv)
        """
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'summary': self.get_performance_summary(),
                'traces': [trace.to_dict() for trace in self.traces]
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
                        'trace_id', 'page_load_time', 'first_contentful_paint',
                        'largest_contentful_paint', 'cumulative_layout_shift',
                        'first_input_delay', 'has_issues'
                    ])
                    for trace in self.traces:
                        writer.writerow([
                            trace.trace_id, trace.page_load_time,
                            trace.first_contentful_paint, trace.largest_contentful_paint,
                            trace.cumulative_layout_shift, trace.first_input_delay,
                            trace.has_performance_issues()
                        ])

            self.logger.info(f"性能追踪数据已导出到: {filename}")

        except Exception as e:
            self.logger.error(f"导出性能追踪数据失败: {str(e)}")

    def clear_traces(self):
        """清除所有追踪数据"""
        self.traces.clear()
        self.logger.info("性能追踪数据已清除")