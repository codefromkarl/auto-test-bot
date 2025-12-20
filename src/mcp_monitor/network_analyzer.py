"""
网络请求分析器
通过 MCP 监控和分析网络请求
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse


class NetworkRequest:
    """网络请求类"""

    def __init__(self, data: Dict[str, Any]):
        """
        初始化网络请求

        Args:
            data: 请求数据字典
        """
        self.request_id = data.get('request_id')
        self.url = data.get('url', '')
        self.method = data.get('method', 'GET')
        self.status_code = data.get('status_code', 0)
        self.status_text = data.get('status_text', '')
        self.request_headers = data.get('request_headers', {})
        self.response_headers = data.get('response_headers', {})
        self.request_body = data.get('request_body', '')
        self.response_body = data.get('response_body', '')
        self.initiator = data.get('initiator', '')
        self.resource_type = data.get('resource_type', 'other')
        self.priority = data.get('priority', 'Medium')
        self.timing = data.get('timing', {})
        self.timestamp = data.get('timestamp', datetime.now().isoformat())
        self.start_time = data.get('start_time')
        self.end_time = data.get('end_time')

        # 计算响应时间
        self.response_time = self._calculate_response_time()

    def _calculate_response_time(self) -> float:
        """计算响应时间（毫秒）"""
        if self.timing:
            # 使用 timing 信息
            return self.timing.get('responseEnd', 0) - self.timing.get('requestStart', 0)
        elif self.start_time and self.end_time:
            # 使用开始结束时间
            return (self.end_time - self.start_time) * 1000
        return 0

    def is_successful(self) -> bool:
        """检查请求是否成功"""
        return 200 <= self.status_code < 400

    def is_error(self) -> bool:
        """检查是否为错误请求"""
        return self.status_code >= 400 or self.response_time == 0

    def is_api_request(self) -> bool:
        """检查是否为 API 请求"""
        return (
            '/api/' in self.url or
            self.url.endswith('.json') or
            'content-type' in self.response_headers and
            'application/json' in self.response_headers['content-type']
        )

    def is_static_resource(self) -> bool:
        """检查是否为静态资源"""
        static_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2']
        return any(self.url.lower().endswith(ext) for ext in static_extensions)

    def get_domain(self) -> str:
        """获取域名"""
        parsed = urlparse(self.url)
        return parsed.netloc

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'request_id': self.request_id,
            'url': self.url,
            'method': self.method,
            'status_code': self.status_code,
            'status_text': self.status_text,
            'resource_type': self.resource_type,
            'response_time': self.response_time,
            'is_successful': self.is_successful(),
            'is_error': self.is_error(),
            'is_api_request': self.is_api_request(),
            'is_static_resource': self.is_static_resource(),
            'domain': self.get_domain(),
            'timestamp': self.timestamp,
            'initiator': self.initiator,
            'priority': self.priority,
            'timing': self.timing
        }


class NetworkAnalyzer:
    """网络请求分析器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化网络分析器

        Args:
            config: 配置字典
        """
        self.config = config.get('network', {})
        self.logger = logging.getLogger(__name__)

        # 监控配置
        self.enabled = self.config.get('enabled', True)
        self.max_buffer_size = self.config.get('max_buffer_size', 1000)
        self.capture_headers = self.config.get('capture_headers', True)
        self.capture_body = self.config.get('capture_body', False)
        self.filter_methods = self.config.get('filter_methods', ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])

        # 请求缓冲区
        self.requests: List[NetworkRequest] = []
        self.error_count = 0
        self.api_request_count = 0

    def start_monitoring(self):
        """开始监控"""
        if not self.enabled:
            self.logger.info("网络监控已禁用")
            return

        self.logger.info("开始网络监控")
        self.requests.clear()
        self.error_count = 0
        self.api_request_count = 0

    def stop_monitoring(self) -> Dict[str, Any]:
        """
        停止监控并返回结果

        Returns:
            Dict[str, Any]: 监控结果
        """
        if not self.enabled:
            return {'enabled': False}

        summary = {
            'enabled': True,
            'total_requests': len(self.requests),
            'error_count': self.error_count,
            'api_request_count': self.api_request_count,
            'success_rate': self._calculate_success_rate(),
            'average_response_time': self._calculate_average_response_time(),
            'requests': [req.to_dict() for req in self.requests]
        }

        self.logger.info(f"网络监控结束: {summary['total_requests']} 个请求")
        return summary

    def add_request(self, request_data: Dict[str, Any]):
        """
        添加网络请求

        Args:
            request_data: 请求数据
        """
        if not self.enabled:
            return

        # 过滤请求方法
        method = request_data.get('method', 'GET')
        if method not in self.filter_methods:
            return

        # 检查缓冲区大小
        if len(self.requests) >= self.max_buffer_size:
            self.requests.pop(0)

        # 处理请求头和响应头
        if not self.capture_headers:
            request_data.pop('request_headers', None)
            request_data.pop('response_headers', None)

        # 处理请求体和响应体
        if not self.capture_body:
            request_data.pop('request_body', None)
            request_data.pop('response_body', None)

        request = NetworkRequest(request_data)
        self.requests.append(request)

        # 统计
        if request.is_error():
            self.error_count += 1
            self.logger.error(f"网络请求失败 [{method}] {request.url} - {request.status_code}")

        if request.is_api_request():
            self.api_request_count += 1

        self.logger.debug(f"网络请求 [{method}] {request.url} - {request.status_code} - {request.response_time:.2f}ms")

    def get_errors(self) -> List[NetworkRequest]:
        """
        获取所有错误请求

        Returns:
            List[NetworkRequest]: 错误请求列表
        """
        return [req for req in self.requests if req.is_error()]

    def get_api_requests(self) -> List[NetworkRequest]:
        """
        获取所有 API 请求

        Returns:
            List[NetworkRequest]: API 请求列表
        """
        return [req for req in self.requests if req.is_api_request()]

    def get_slow_requests(self, threshold_ms: float = 3000) -> List[NetworkRequest]:
        """
        获取慢请求

        Args:
            threshold_ms: 响应时间阈值（毫秒）

        Returns:
            List[NetworkRequest]: 慢请求列表
        """
        return [req for req in self.requests if req.response_time > threshold_ms]

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            Dict[str, Any]: 性能摘要
        """
        if not self.requests:
            return {}

        response_times = [req.response_time for req in self.requests if req.response_time > 0]

        return {
            'total_requests': len(self.requests),
            'successful_requests': len([req for req in self.requests if req.is_successful()]),
            'error_requests': self.error_count,
            'success_rate': self._calculate_success_rate(),
            'api_requests': self.api_request_count,
            'static_resource_requests': len([req for req in self.requests if req.is_static_resource()]),
            'average_response_time': self._calculate_average_response_time(),
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'median_response_time': self._calculate_median_response_time(),
            'slow_requests': len(self.get_slow_requests())
        }

    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self.requests:
            return 0.0
        successful = len([req for req in self.requests if req.is_successful()])
        return (successful / len(self.requests)) * 100

    def _calculate_average_response_time(self) -> float:
        """计算平均响应时间"""
        response_times = [req.response_time for req in self.requests if req.response_time > 0]
        return sum(response_times) / len(response_times) if response_times else 0

    def _calculate_median_response_time(self) -> float:
        """计算中位数响应时间"""
        response_times = [req.response_time for req in self.requests if req.response_time > 0]
        if not response_times:
            return 0
        response_times.sort()
        mid = len(response_times) // 2
        return response_times[mid] if len(response_times) % 2 == 1 else (response_times[mid-1] + response_times[mid]) / 2

    def analyze_endpoints(self) -> Dict[str, Any]:
        """
        分析 API 端点

        Returns:
            Dict[str, Any]: 端点分析结果
        """
        api_requests = self.get_api_requests()
        endpoints = {}

        for req in api_requests:
            # 提取端点（简化版，实际可能需要更复杂的路径解析）
            parsed = urlparse(req.url)
            endpoint = f"{parsed.path}?{parsed.query}" if parsed.query else parsed.path

            if endpoint not in endpoints:
                endpoints[endpoint] = {
                    'url': req.url,
                    'count': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'total_response_time': 0,
                    'min_response_time': float('inf'),
                    'max_response_time': 0,
                    'status_codes': {}
                }

            ep = endpoints[endpoint]
            ep['count'] += 1
            ep['total_response_time'] += req.response_time
            ep['min_response_time'] = min(ep['min_response_time'], req.response_time)
            ep['max_response_time'] = max(ep['max_response_time'], req.response_time)

            # 状态码统计
            status_code = req.status_code
            if status_code not in ep['status_codes']:
                ep['status_codes'][status_code] = 0
            ep['status_codes'][status_code] += 1

            if req.is_successful():
                ep['success_count'] += 1
            else:
                ep['error_count'] += 1

        # 计算平均响应时间
        for ep in endpoints.values():
            if ep['count'] > 0:
                ep['average_response_time'] = ep['total_response_time'] / ep['count']
                if ep['min_response_time'] == float('inf'):
                    ep['min_response_time'] = 0

        return endpoints

    def has_performance_issues(self) -> bool:
        """
        检查是否有性能问题

        Returns:
            bool: 是否有性能问题
        """
        return (
            self._calculate_success_rate() < 95 or  # 成功率过低
            self._calculate_average_response_time() > 5000 or  # 平均响应时间过长
            len(self.get_slow_requests(3000)) > len(self.requests) * 0.1  # 慢请求过多
        )

    def export_requests(self, filename: str, format_type: str = 'json'):
        """
        导出请求数据到文件

        Args:
            filename: 文件名
            format_type: 格式类型 (json, csv)
        """
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'summary': self.get_performance_summary(),
                'endpoints': self.analyze_endpoints(),
                'requests': [req.to_dict() for req in self.requests]
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
                        'timestamp', 'method', 'url', 'status_code',
                        'response_time', 'resource_type', 'is_api_request'
                    ])
                    for req in self.requests:
                        writer.writerow([
                            req.timestamp, req.method, req.url,
                            req.status_code, req.response_time,
                            req.resource_type, req.is_api_request()
                        ])

            self.logger.info(f"网络请求数据已导出到: {filename}")

        except Exception as e:
            self.logger.error(f"导出网络请求数据失败: {str(e)}")