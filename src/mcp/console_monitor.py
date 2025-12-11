"""
控制台日志监控器
通过 MCP 收集和分析浏览器控制台输出
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


class ConsoleMessage:
    """控制台消息类"""

    def __init__(self, data: Dict[str, Any]):
        """
        初始化控制台消息

        Args:
            data: 消息数据字典
        """
        self.timestamp = data.get('timestamp', datetime.now().isoformat())
        self.level = data.get('level', 'log')
        self.source = data.get('source', 'console')
        self.text = data.get('text', '')
        self.url = data.get('url', '')
        self.line_number = data.get('line_number')
        self.column_number = data.get('column_number')
        self.stack_trace = data.get('stack_trace', [])
        self.args = data.get('args', [])

    def is_error(self) -> bool:
        """检查是否为错误消息"""
        return self.level in ['error', 'exception']

    def is_warning(self) -> bool:
        """检查是否为警告消息"""
        return self.level == 'warning'

    def is_javascript_error(self) -> bool:
        """检查是否为 JavaScript 错误"""
        return self.is_error() and self.source in ['javascript', 'console']

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'level': self.level,
            'source': self.source,
            'text': self.text,
            'url': self.url,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'stack_trace': self.stack_trace,
            'args': self.args
        }


class ConsoleMonitor:
    """控制台监控器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化控制台监控器

        Args:
            config: 配置字典
        """
        self.config = config.get('console', {})
        self.logger = logging.getLogger(__name__)

        # 监控配置
        self.enabled = self.config.get('enabled', True)
        self.max_buffer_size = self.config.get('max_buffer_size', 1000)
        self.filter_levels = self.config.get('filter_levels', ['log', 'info', 'warn', 'error'])

        # 消息缓冲区
        self.messages: List[ConsoleMessage] = []
        self.error_count = 0
        self.warning_count = 0

    def start_monitoring(self):
        """开始监控"""
        if not self.enabled:
            self.logger.info("控制台监控已禁用")
            return

        self.logger.info("开始控制台监控")
        self.messages.clear()
        self.error_count = 0
        self.warning_count = 0

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
            'total_messages': len(self.messages),
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'messages': [msg.to_dict() for msg in self.messages]
        }

        self.logger.info(f"控制台监控结束: {summary['total_messages']} 条消息")
        return summary

    def add_message(self, message_data: Dict[str, Any]):
        """
        添加控制台消息

        Args:
            message_data: 消息数据
        """
        if not self.enabled:
            return

        # 过滤消息级别
        level = message_data.get('level', 'log')
        if level not in self.filter_levels:
            return

        message = ConsoleMessage(message_data)

        # 检查缓冲区大小
        if len(self.messages) >= self.max_buffer_size:
            self.messages.pop(0)

        self.messages.append(message)

        # 统计错误和警告
        if message.is_error():
            self.error_count += 1
            self.logger.error(f"控制台错误: {message.text}")
            if message.stack_trace:
                self.logger.debug(f"错误堆栈: {json.dumps(message.stack_trace, indent=2)}")

        elif message.is_warning():
            self.warning_count += 1
            self.logger.warning(f"控制台警告: {message.text}")

        else:
            self.logger.debug(f"控制台消息 [{level}]: {message.text}")

    def get_errors(self) -> List[ConsoleMessage]:
        """
        获取所有错误消息

        Returns:
            List[ConsoleMessage]: 错误消息列表
        """
        return [msg for msg in self.messages if msg.is_error()]

    def get_warnings(self) -> List[ConsoleMessage]:
        """
        获取所有警告消息

        Returns:
            List[ConsoleMessage]: 警告消息列表
        """
        return [msg for msg in self.messages if msg.is_warning()]

    def get_javascript_errors(self) -> List[ConsoleMessage]:
        """
        获取 JavaScript 错误

        Returns:
            List[ConsoleMessage]: JavaScript 错误列表
        """
        return [msg for msg in self.messages if msg.is_javascript_error()]

    def get_error_summary(self) -> Dict[str, Any]:
        """
        获取错误摘要

        Returns:
            Dict[str, Any]: 错误摘要
        """
        js_errors = self.get_javascript_errors()
        other_errors = [msg for msg in self.get_errors() if not msg.is_javascript_error()]

        return {
            'total_errors': self.error_count,
            'total_warnings': self.warning_count,
            'javascript_errors': len(js_errors),
            'other_errors': len(other_errors),
            'error_types': self._analyze_error_types(),
            'common_errors': self._get_common_errors()
        }

    def _analyze_error_types(self) -> Dict[str, int]:
        """
        分析错误类型

        Returns:
            Dict[str, int]: 错误类型统计
        """
        error_types = {}
        for error in self.get_errors():
            # 简单的错误类型分析
            error_text = error.text.lower()
            if 'referenceerror' in error_text:
                error_types['ReferenceError'] = error_types.get('ReferenceError', 0) + 1
            elif 'typeerror' in error_text:
                error_types['TypeError'] = error_types.get('TypeError', 0) + 1
            elif 'syntaxerror' in error_text:
                error_types['SyntaxError'] = error_types.get('SyntaxError', 0) + 1
            elif 'network' in error_text:
                error_types['NetworkError'] = error_types.get('NetworkError', 0) + 1
            else:
                error_types['Other'] = error_types.get('Other', 0) + 1

        return error_types

    def _get_common_errors(self) -> List[Dict[str, Any]]:
        """
        获取常见错误

        Returns:
            List[Dict[str, Any]]: 常见错误列表
        """
        error_counts = {}
        for error in self.get_errors():
            # 使用错误文本作为键进行统计
            error_key = error.text[:100]  # 限制长度
            if error_key not in error_counts:
                error_counts[error_key] = {
                    'message': error.text,
                    'count': 0,
                    'first_occurrence': error.timestamp,
                    'url': error.url
                }
            error_counts[error_key]['count'] += 1

        # 按出现次数排序
        sorted_errors = sorted(error_counts.values(), key=lambda x: x['count'], reverse=True)
        return sorted_errors[:10]  # 返回前10个最常见错误

    def has_critical_errors(self) -> bool:
        """
        检查是否有严重错误

        Returns:
            bool: 是否有严重错误
        """
        # 严重错误的标准可以根据需要调整
        return (
            self.error_count > 10 or  # 错误数量过多
            len(self.get_javascript_errors()) > 5 or  # JS 错误过多
            self._has_uncaught_exceptions()
        )

    def _has_uncaught_exceptions(self) -> bool:
        """
        检查是否有未捕获的异常

        Returns:
            bool: 是否有未捕获的异常
        """
        for error in self.get_errors():
            if 'uncaught' in error.text.lower() or 'exception' in error.text.lower():
                return True
        return False

    def get_messages_by_time_range(self, start_time: str, end_time: str) -> List[ConsoleMessage]:
        """
        获取指定时间范围内的消息

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[ConsoleMessage]: 消息列表
        """
        filtered_messages = []
        for message in self.messages:
            if start_time <= message.timestamp <= end_time:
                filtered_messages.append(message)
        return filtered_messages

    def export_messages(self, filename: str, format_type: str = 'json'):
        """
        导出消息到文件

        Args:
            filename: 文件名
            format_type: 格式类型 (json, csv)
        """
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'summary': self.get_error_summary(),
                'messages': [msg.to_dict() for msg in self.messages]
            }

            if format_type.lower() == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            elif format_type.lower() == 'csv':
                # 简化的 CSV 导出
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'level', 'source', 'text', 'url'])
                    for msg in self.messages:
                        writer.writerow([
                            msg.timestamp, msg.level, msg.source,
                            msg.text.replace('\n', ' '), msg.url
                        ])

            self.logger.info(f"控制台消息已导出到: {filename}")

        except Exception as e:
            self.logger.error(f"导出控制台消息失败: {str(e)}")