"""
错误诊断器
综合分析各种错误并提供诊断建议
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .console_monitor import ConsoleMonitor
from .network_analyzer import NetworkAnalyzer
from .performance_tracer import PerformanceTracer
from .dom_debugger import DOMDebugger


class DiagnosticReport:
    """诊断报告类"""

    def __init__(self):
        """初始化诊断报告"""
        self.report_id = f"report_{int(datetime.now().timestamp() * 1000)}"
        self.timestamp = datetime.now().isoformat()
        self.overall_status = "unknown"
        self.error_summary = {}
        self.issues = []
        self.recommendations = []
        self.root_cause_analysis = []
        self.affected_components = []

    def add_issue(self, severity: str, category: str, description: str, details: Dict[str, Any] = None):
        """
        添加问题

        Args:
            severity: 严重程度 (critical, high, medium, low)
            category: 问题类别
            description: 问题描述
            details: 详细信息
        """
        issue = {
            'severity': severity,
            'category': category,
            'description': description,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.issues.append(issue)

    def add_recommendation(self, priority: str, description: str, action_items: List[str]):
        """
        添加建议

        Args:
            priority: 优先级
            description: 建议描述
            action_items: 行动项列表
        """
        recommendation = {
            'priority': priority,
            'description': description,
            'action_items': action_items,
            'timestamp': datetime.now().isoformat()
        }
        self.recommendations.append(recommendation)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'report_id': self.report_id,
            'timestamp': self.timestamp,
            'overall_status': self.overall_status,
            'error_summary': self.error_summary,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'root_cause_analysis': self.root_cause_analysis,
            'affected_components': self.affected_components
        }


class ErrorDiagnostic:
    """错误诊断器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化错误诊断器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 监控器引用
        self.console_monitor: Optional[ConsoleMonitor] = None
        self.network_analyzer: Optional[NetworkAnalyzer] = None
        self.performance_tracer: Optional[PerformanceTracer] = None
        self.dom_debugger: Optional[DOMDebugger] = None

        # 诊断配置
        self.diagnostic_rules = self._load_diagnostic_rules()

    def set_monitors(self, console: ConsoleMonitor, network: NetworkAnalyzer,
                     performance: PerformanceTracer, dom: DOMDebugger):
        """
        设置监控器

        Args:
            console: 控制台监控器
            network: 网络分析器
            performance: 性能追踪器
            dom: DOM 调试器
        """
        self.console_monitor = console
        self.network_analyzer = network
        self.performance_tracer = performance
        self.dom_debugger = dom

    def diagnose_errors(self) -> DiagnosticReport:
        """
        执行综合错误诊断

        Returns:
            DiagnosticReport: 诊断报告
        """
        report = DiagnosticReport()

        try:
            self.logger.info("开始综合错误诊断")

            # 1. 分析控制台错误
            console_issues = self._diagnose_console_errors()
            report.issues.extend(console_issues)

            # 2. 分析网络错误
            network_issues = self._diagnose_network_errors()
            report.issues.extend(network_issues)

            # 3. 分析性能问题
            performance_issues = self._diagnose_performance_issues()
            report.issues.extend(performance_issues)

            # 4. 分析 DOM 问题
            dom_issues = self._diagnose_dom_issues()
            report.issues.extend(dom_issues)

            # 5. 生成错误摘要
            report.error_summary = self._generate_error_summary(report.issues)

            # 6. 确定整体状态
            report.overall_status = self._determine_overall_status(report.issues)

            # 7. 根本原因分析
            report.root_cause_analysis = self._perform_root_cause_analysis(report.issues)

            # 8. 生成建议
            report.recommendations = self._generate_recommendations(report.issues)

            # 9. 确定受影响组件
            report.affected_components = self._identify_affected_components(report.issues)

            self.logger.info(f"错误诊断完成: {len(report.issues)} 个问题")
            return report

        except Exception as e:
            self.logger.error(f"错误诊断失败: {str(e)}")
            report.add_issue('critical', 'diagnostic', f'诊断过程失败: {str(e)}')
            report.overall_status = 'error'
            return report

    def _diagnose_console_errors(self) -> List[Dict[str, Any]]:
        """诊断控制台错误"""
        issues = []

        if not self.console_monitor:
            return issues

        # 获取 JavaScript 错误
        js_errors = self.console_monitor.get_javascript_errors()
        if js_errors:
            if len(js_errors) > 5:
                issues.append({
                    'severity': 'high',
                    'category': 'console',
                    'description': f'检测到过多的 JavaScript 错误: {len(js_errors)} 个',
                    'details': {'error_count': len(js_errors), 'errors': [err.text for err in js_errors[:5]]}
                })

            # 分析常见错误模式
            error_types = self.console_monitor.get_error_summary().get('error_types', {})
            if 'ReferenceError' in error_types and error_types['ReferenceError'] > 2:
                issues.append({
                    'severity': 'high',
                    'category': 'console',
                    'description': '检测到多个引用错误，可能存在未定义变量或函数',
                    'details': {'error_count': error_types['ReferenceError']}
                })

            if 'TypeError' in error_types and error_types['TypeError'] > 2:
                issues.append({
                    'severity': 'medium',
                    'category': 'console',
                    'description': '检测到多个类型错误，可能存在 null/undefined 访问',
                    'details': {'error_count': error_types['TypeError']}
                })

        return issues

    def _diagnose_network_errors(self) -> List[Dict[str, Any]]:
        """诊断网络错误"""
        issues = []

        if not self.network_analyzer:
            return issues

        # 获取网络错误
        network_errors = self.network_analyzer.get_errors()
        if network_errors:
            if len(network_errors) > 3:
                issues.append({
                    'severity': 'high',
                    'category': 'network',
                    'description': f'检测到过多的网络请求失败: {len(network_errors)} 个',
                    'details': {'error_count': len(network_errors)}
                })

            # 分析 5xx 错误
            server_errors = [req for req in network_errors if req.status_code >= 500]
            if server_errors:
                issues.append({
                    'severity': 'critical',
                    'category': 'network',
                    'description': f'检测到服务器错误: {len(server_errors)} 个 5xx 错误',
                    'details': {
                        'server_error_count': len(server_errors),
                        'affected_endpoints': list(set(req.url for req in server_errors))
                    }
                })

            # 分析 4xx 错误
            client_errors = [req for req in network_errors if 400 <= req.status_code < 500]
            if len(client_errors) > 2:
                issues.append({
                    'severity': 'medium',
                    'category': 'network',
                    'description': f'检测到客户端错误: {len(client_errors)} 个 4xx 错误',
                    'details': {'client_error_count': len(client_errors)}
                })

        # 分析慢请求
        slow_requests = self.network_analyzer.get_slow_requests(5000)
        if len(slow_requests) > 3:
            issues.append({
                'severity': 'medium',
                'category': 'network',
                'description': f'检测到多个慢请求: {len(slow_requests)} 个超过 5 秒的请求',
                'details': {'slow_request_count': len(slow_requests)}
            })

        return issues

    def _diagnose_performance_issues(self) -> List[Dict[str, Any]]:
        """诊断性能问题"""
        issues = []

        if not self.performance_tracer:
            return issues

        # 获取最新性能数据
        latest_trace = self.performance_tracer.get_latest_trace()
        if not latest_trace:
            return issues

        # 检查页面加载时间
        if latest_trace.page_load_time > 8000:
            issues.append({
                'severity': 'high',
                'category': 'performance',
                'description': f'页面加载时间过长: {latest_trace.page_load_time}ms',
                'details': {'page_load_time': latest_trace.page_load_time}
            })

        # 检查首次内容绘制
        if latest_trace.first_contentful_paint > 4000:
            issues.append({
                'severity': 'medium',
                'category': 'performance',
                'description': f'首次内容绘制过慢: {latest_trace.first_contentful_paint}ms',
                'details': {'fcp': latest_trace.first_contentful_paint}
            })

        # 检查布局偏移
        if latest_trace.cumulative_layout_shift > 0.25:
            issues.append({
                'severity': 'medium',
                'category': 'performance',
                'description': f'布局偏移过多: {latest_trace.cumulative_layout_shift}',
                'details': {'cls': latest_trace.cumulative_layout_shift}
            })

        return issues

    def _diagnose_dom_issues(self) -> List[Dict[str, Any]]:
        """诊断 DOM 问题"""
        issues = []

        if not self.dom_debugger:
            return issues

        # 获取最新 DOM 快照
        latest_snapshot = self.dom_debugger.get_latest_snapshot()
        if not latest_snapshot:
            return issues

        # 分析布局问题
        layout_issues = self.dom_debugger.analyze_layout_issues(latest_snapshot)

        if layout_issues.get('hidden_elements', 0) > 100:
            issues.append({
                'severity': 'low',
                'category': 'dom',
                'description': f'隐藏元素过多: {layout_issues["hidden_elements"]} 个',
                'details': {'hidden_element_count': layout_issues['hidden_elements']}
            })

        if layout_issues.get('element_count', 0) > 5000:
            issues.append({
                'severity': 'medium',
                'category': 'dom',
                'description': f'DOM 元素过多: {layout_issues["element_count"]} 个',
                'details': {'element_count': layout_issues['element_count']}
            })

        if layout_issues.get('potential_overlaps', 0) > 10:
            issues.append({
                'severity': 'low',
                'category': 'dom',
                'description': f'检测到潜在的元素重叠: {layout_issues["potential_overlaps"]} 处',
                'details': {'overlap_count': layout_issues['potential_overlaps']}
            })

        return issues

    def _generate_error_summary(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成错误摘要"""
        summary = {
            'total_issues': len(issues),
            'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'by_category': {}
        }

        for issue in issues:
            # 按严重程度统计
            severity = issue.get('severity', 'low')
            if severity in summary['by_severity']:
                summary['by_severity'][severity] += 1

            # 按类别统计
            category = issue.get('category', 'unknown')
            if category not in summary['by_category']:
                summary['by_category'][category] = 0
            summary['by_category'][category] += 1

        return summary

    def _determine_overall_status(self, issues: List[Dict[str, Any]]) -> str:
        """确定整体状态"""
        if not issues:
            return 'healthy'

        # 检查严重程度
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1

        if severity_counts['critical'] > 0:
            return 'critical'
        elif severity_counts['high'] > 2:
            return 'unhealthy'
        elif severity_counts['high'] > 0 or severity_counts['medium'] > 5:
            return 'degraded'
        elif severity_counts['medium'] > 0 or severity_counts['low'] > 10:
            return 'warning'
        else:
            return 'healthy'

    def _perform_root_cause_analysis(self, issues: List[Dict[str, Any]]) -> List[str]:
        """执行根本原因分析"""
        analysis = []

        # 分析 JavaScript 错误和网络失败的关联
        js_errors = [issue for issue in issues if issue.get('category') == 'console']
        network_errors = [issue for issue in issues if issue.get('category') == 'network']

        if js_errors and network_errors:
            analysis.append("JavaScript 错误和网络请求失败同时存在，可能是前端代码依赖的后端 API 出现问题")

        # 分析性能问题和其他问题的关联
        performance_issues = [issue for issue in issues if issue.get('category') == 'performance']
        if performance_issues and network_errors:
            analysis.append("网络请求失败可能导致页面加载性能下降")

        if performance_issues and js_errors:
            analysis.append("JavaScript 错误可能阻塞了页面渲染，导致性能问题")

        # 分析 DOM 问题
        dom_issues = [issue for issue in issues if issue.get('category') == 'dom']
        if dom_issues:
            analysis.append("DOM 结构问题可能影响页面渲染性能和用户体验")

        if not analysis:
            analysis.append("问题相对独立，没有发现明显的关联模式")

        return analysis

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成建议"""
        recommendations = []

        # 基于问题严重程度生成建议
        critical_issues = [issue for issue in issues if issue.get('severity') == 'critical']
        high_issues = [issue for issue in issues if issue.get('severity') == 'high']

        if critical_issues:
            recommendations.append({
                'priority': 'immediate',
                'description': '立即处理严重问题',
                'action_items': [
                    '检查服务器状态和配置',
                    '修复关键的 JavaScript 错误',
                    '确保核心 API 端点正常工作'
                ]
            })

        if high_issues:
            recommendations.append({
                'priority': 'high',
                'description': '优先处理高优先级问题',
                'action_items': [
                    '优化网络请求性能',
                    '减少 JavaScript 错误',
                    '改善页面加载性能'
                ]
            })

        # 基于问题类别生成具体建议
        if any(issue.get('category') == 'console' for issue in issues):
            recommendations.append({
                'priority': 'medium',
                'description': '改进 JavaScript 代码质量',
                'action_items': [
                    '添加错误处理和空值检查',
                    '使用 TypeScript 进行类型检查',
                    '实现更严格的代码审查流程'
                ]
            })

        if any(issue.get('category') == 'network' for issue in issues):
            recommendations.append({
                'priority': 'medium',
                'description': '优化网络请求处理',
                'action_items': [
                    '添加请求重试机制',
                    '实现更好的错误处理',
                    '优化 API 响应时间'
                ]
            })

        if any(issue.get('category') == 'performance' for issue in issues):
            recommendations.append({
                'priority': 'low',
                'description': '优化页面性能',
                'action_items': [
                    '压缩和优化图片资源',
                    '实现代码分割和懒加载',
                    '使用 CDN 加速静态资源'
                ]
            })

        return recommendations

    def _identify_affected_components(self, issues: List[Dict[str, Any]]) -> List[str]:
        """识别受影响的组件"""
        components = set()

        for issue in issues:
            category = issue.get('category', '')
            if category == 'console':
                components.add('JavaScript 引擎')
                components.add('前端应用')
            elif category == 'network':
                components.add('API 服务')
                components.add('网络层')
            elif category == 'performance':
                components.add('页面渲染')
                components.add('资源加载')
            elif category == 'dom':
                components.add('DOM 结构')
                components.add('UI 组件')

        return list(components)

    def _load_diagnostic_rules(self) -> Dict[str, Any]:
        """加载诊断规则"""
        return {
            'console': {
                'max_js_errors': 5,
                'max_error_frequency': 3,
                'critical_error_types': ['ReferenceError', 'TypeError']
            },
            'network': {
                'max_error_rate': 0.1,
                'max_slow_requests': 3,
                'slow_request_threshold': 5000
            },
            'performance': {
                'max_page_load_time': 8000,
                'max_fcp': 4000,
                'max_cls': 0.25
            },
            'dom': {
                'max_hidden_elements': 100,
                'max_total_elements': 5000,
                'max_overlaps': 10
            }
        }

    def export_diagnostic_report(self, report: DiagnosticReport, filename: str):
        """
        导出诊断报告

        Args:
            report: 诊断报告
            filename: 文件名
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

            self.logger.info(f"诊断报告已导出到: {filename}")

        except Exception as e:
            self.logger.error(f"导出诊断报告失败: {str(e)}")