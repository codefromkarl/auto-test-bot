"""
报告格式化器
格式化测试结果和生成结构化报告
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils import Timer


class ReportFormatter:
    """报告格式化器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化报告格式化器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reporting_config = config.get('reporting', {})

        # 报告配置
        self.output_dir = self.reporting_config.get('output_dir', 'reports')
        self.format = self.reporting_config.get('format', 'both')
        self.include_screenshots = self.reporting_config.get('include_screenshots', True)
        self.include_mcp_data = self.reporting_config.get('include_mcp_data', True)

    def format_test_report(self, test_results: List[Dict[str, Any]],
                          mcp_data: Optional[Dict[str, Any]] = None,
                          screenshots: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        格式化测试报告

        Args:
            test_results: 测试结果列表
            mcp_data: MCP 监控数据
            screenshots: 截图文件列表

        Returns:
            Dict[str, Any]: 格式化的报告
        """
        # 生成基础报告结构
        report = {
            'report_info': self._generate_report_info(),
            'execution_summary': self._generate_execution_summary(test_results),
            'test_results': test_results,
            'performance_metrics': self._generate_performance_metrics(test_results),
            'errors_and_issues': self._analyze_errors(test_results),
            'recommendations': self._generate_recommendations(test_results)
        }

        # 添加 MCP 数据（如果启用）
        if self.include_mcp_data and mcp_data:
            report['mcp_monitoring'] = self._format_mcp_data(mcp_data)

        # 添加截图信息（如果启用）
        if self.include_screenshots and screenshots:
            report['screenshots'] = screenshots

        return report

    def _generate_report_info(self) -> Dict[str, Any]:
        """生成报告基本信息"""
        return {
            'report_id': f"report_{int(datetime.now().timestamp() * 1000)}",
            'generated_at': datetime.now().isoformat(),
            'test_bot_version': "1.0.0",
            'report_format': self.format
        }

    def _generate_execution_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成执行摘要"""
        if not test_results:
            return {
                'total_steps': 0,
                'successful_steps': 0,
                'failed_steps': 0,
                'overall_success': False,
                'total_duration': 0,
                'success_rate': 0
            }

        successful_steps = len([r for r in test_results if r.get('success', False)])
        failed_steps = len(test_results) - successful_steps
        total_duration = sum(r.get('metrics', {}).get('total_time', 0) for r in test_results)

        # 确定整体成功状态
        validate_step = next((r for r in test_results if r.get('step') == 'validate'), None)
        overall_success = validate_step.get('success', False) if validate_step else False

        return {
            'total_steps': len(test_results),
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'overall_success': overall_success,
            'total_duration': total_duration,
            'success_rate': (successful_steps / len(test_results)) * 100,
            'test_prompt': self._extract_test_prompt(test_results)
        }

    def _generate_performance_metrics(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成性能指标"""
        metrics = {
            'step_metrics': {},
            'timing_breakdown': {},
            'slowest_step': None,
            'fastest_step': None,
            'total_execution_time': 0
        }

        step_times = []
        for result in test_results:
            step_name = result.get('step', 'unknown')
            duration = result.get('metrics', {}).get('total_time', 0)

            metrics['step_metrics'][step_name] = {
                'duration': duration,
                'success': result.get('success', False),
                'checkpoints': result.get('metrics', {}).get('checkpoints', {})
            }

            if duration > 0:
                step_times.append({'step': step_name, 'duration': duration})

        if step_times:
            # 排序找到最快和最慢的步骤
            step_times.sort(key=lambda x: x['duration'])
            metrics['fastest_step'] = step_times[0]
            metrics['slowest_step'] = step_times[-1]

        # 计算总执行时间
        metrics['total_execution_time'] = sum(
            r.get('metrics', {}).get('total_time', 0) for r in test_results
        )

        return metrics

    def _analyze_errors(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析错误和问题"""
        errors = []

        for result in test_results:
            if not result.get('success', False):
                error_info = {
                    'step': result.get('step', 'unknown'),
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat(),
                    'severity': self._determine_error_severity(result.get('step', ''))
                }

                # 添加详细信息
                details = result.get('details', {})
                if details:
                    error_info['details'] = details

                errors.append(error_info)

        return errors

    def _determine_error_severity(self, step_name: str) -> str:
        """确定错误严重程度"""
        critical_steps = ['open_site', 'generate_image']
        high_steps = ['generate_video']

        if step_name in critical_steps:
            return 'critical'
        elif step_name in high_steps:
            return 'high'
        else:
            return 'medium'

    def _generate_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []

        # 分析失败的步骤
        failed_steps = [r for r in test_results if not r.get('success', False)]

        if not failed_steps:
            recommendations.append("测试执行成功，系统运行正常")
            return recommendations

        # 基于失败步骤生成建议
        for result in failed_steps:
            step_name = result.get('step', 'unknown')
            error = result.get('error', '')

            if step_name == 'open_site':
                if '无法访问' in error or '连接' in error:
                    recommendations.append("检查网站可访问性和网络连接")
                elif '元素' in error:
                    recommendations.append("验证页面结构和 DOM 选择器配置")
                else:
                    recommendations.append("检查网站访问相关的配置和环境")

            elif step_name == 'generate_image':
                if '生成图片' in error or '超时' in error:
                    recommendations.append("检查图片生成功能和后端服务状态")
                elif '输入' in error or '按钮' in error:
                    recommendations.append("验证输入框和按钮的 DOM 选择器")
                else:
                    recommendations.append("检查图片生成流程和相关 API")

            elif step_name == 'generate_video':
                if '生成视频' in error or '超时' in error:
                    recommendations.append("检查视频生成功能和图片到视频的转换流程")
                else:
                    recommendations.append("验证视频生成相关功能和服务")

            elif step_name == 'validate':
                recommendations.append("检查验证逻辑和结果确认机制")

        # 通用建议
        if len(failed_steps) > 2:
            recommendations.append("考虑检查系统整体状态和依赖服务")

        # 性能建议
        total_time = sum(r.get('metrics', {}).get('total_time', 0) for r in test_results)
        if total_time > 120000:  # 超过 2 分钟
            recommendations.append("优化测试执行时间，考虑调整超时设置")

        return recommendations

    def _format_mcp_data(self, mcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化 MCP 监控数据，提高可读性

        Args:
            mcp_data: 原始 MCP 数据

        Returns:
            Dict[str, Any]: 格式化后的 MCP 数据
        """
        formatted = {}

        # 格式化控制台监控数据
        if 'console' in mcp_data:
            console = mcp_data['console']
            formatted['console'] = {
                'enabled': console.get('enabled', False),
                'summary': {
                    'total_messages': console.get('total_messages', 0),
                    'errors': console.get('error_count', 0),
                    'warnings': console.get('warning_count', 0)
                },
                'key_messages': console.get('messages', [])[:10] if console.get('messages') else []  # 只显示前10条
            }

        # 格式化网络监控数据
        if 'network' in mcp_data:
            network = mcp_data['network']
            formatted['network'] = {
                'enabled': network.get('enabled', False),
                'summary': {
                    'total_requests': network.get('total_requests', 0),
                    'api_requests': network.get('api_request_count', 0),
                    'success_rate': f"{network.get('success_rate', 0):.1f}%"
                },
                'avg_response_time': f"{network.get('average_response_time', 0):.0f}ms"
            }

        # 格式化性能监控数据
        if 'performance' in mcp_data:
            perf = mcp_data['performance']
            if isinstance(perf, dict):
                formatted['performance'] = {
                    'trace_duration': f"{perf.get('trace_duration', 0)/1000:.1f}s",
                    'metrics': {
                        'total_time': f"{perf.get('metrics', {}).get('total_time', 0):.0f}ms",
                        'memory_usage': f"{perf.get('metrics', {}).get('memory_usage', 0):.1f}MB"
                    }
                }

        # 格式化 DOM 监控数据
        if 'dom' in mcp_data:
            dom = mcp_data['dom']
            formatted['dom'] = {
                'url': dom.get('url', ''),
                'title': dom.get('title', '')[:50] + '...' if len(dom.get('title', '')) > 50 else dom.get('title', ''),
                'element_count': dom.get('element_count', 0),
                'visible_elements': dom.get('visible_element_count', 0),
                'viewport': f"{dom.get('viewport_info', {}).get('width', 0)}x{dom.get('viewport_info', {}).get('height', 0)}"
            }

        # 格式化错误诊断数据
        if 'diagnostic' in mcp_data:
            diag = mcp_data['diagnostic']
            formatted['diagnostic'] = {
                'overall_status': diag.get('overall_status', 'unknown'),
                'issue_count': diag.get('error_summary', {}).get('total_issues', 0),
                'severity_breakdown': diag.get('error_summary', {}).get('by_severity', {}),
                'main_issues': [issue['description'] for issue in diag.get('issues', [])[:3]]  # 只显示前3个问题
            }

        return formatted

    def _extract_test_prompt(self, test_results: List[Dict[str, Any]]) -> Optional[str]:
        """提取测试提示词"""
        for result in test_results:
            if result.get('step') == 'generate_image':
                return result.get('details', {}).get('prompt_used')
        return None

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """生成标准HTML报告"""
        # 简单的HTML报告模板
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Auto Test Bot 测试报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; color: white; padding: 20px; border-radius: 8px; }}
                .summary {{ margin-bottom: 20px; }}
                .step {{ margin: 10px 0; padding: 15px; border-left: 4px solid #ddd; }}
                .step.success {{ border-left-color: #28a745; }}
                .step.failure {{ border-left-color: #dc3545; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
                .error {{ color: #dc3545; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Auto Test Bot 测试报告</h1>
                <p>生成时间: {timestamp}</p>
            </div>
            <div class="summary">
                <h2>📊 执行总结</h2>
                <p>总体状态: {status}</p>
                <p>总耗时: {total_time}ms</p>
            </div>
            <div class="steps">
                <h2>🔍 步骤执行详情</h2>
                {steps_html}
            </div>
        </body>
        </html>
        """

        # 格式化步骤信息
        steps_html = ""
        test_results = report.get('test_results', [])

        for result in test_results:
            step_name = result.get('step', 'Unknown')
            success = result.get('success', False)
            error = result.get('error', '')

            css_class = "success" if success else "failure"
            status_text = "✅ 成功" if success else "❌ 失败"

            steps_html += f"""
            <div class="step {css_class}">
                <h3>{step_name}: {status_text}</h3>
                <p class="timestamp">时间戳: {result.get('timestamp', '')}</p>
                {f'<p class="error">错误: {error}</p>' if error else ''}
            </div>
            """

        # 生成最终HTML
        timestamp = report.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        status = "✅ 测试成功" if report.get('overall_success', False) else "❌ 测试失败"
        total_time = report.get('total_time', 0)

        return html_template.format(
            timestamp=timestamp,
            status=status,
            total_time=total_time,
            steps_html=steps_html
        )

    def save_report(self, report: Dict[str, Any], filename_prefix: str = None,
                    test_flow_name: str = None) -> Dict[str, str]:
        """
        保存报告到文件

        Args:
            report: 报告数据
            filename_prefix: 文件名前缀
            test_flow_name: 测试流程名称

        Returns:
            Dict[str, str]: 保存的文件路径
        """
        import os

        # 生成时间戳和日期
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = datetime.now().strftime("%Y-%m-%d")

        # 确定测试流程名称
        if not test_flow_name:
            test_flow_name = 'default_test_flow'

        # 生成文件名
        if not filename_prefix:
            filename_prefix = f"test_report_{timestamp}"

        # 创建三级目录结构：测试流程名称/日期/
        output_base_dir = self.output_dir
        test_flow_dir = os.path.join(output_base_dir, test_flow_name, date_str)
        os.makedirs(test_flow_dir, exist_ok=True)

        saved_files = {}

        # 根据格式保存报告
        if self.format in ['json', 'both']:
            json_filename = os.path.join(test_flow_dir, f"{filename_prefix}.json")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            saved_files['json'] = json_filename
            self.logger.info(f"📄 JSON报告已保存: {json_filename}")

        if self.format in ['html', 'both']:
            html_filename = os.path.join(test_flow_dir, f"{filename_prefix}.html")
            html_content = self._generate_html_report(report)
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            saved_files['html'] = html_filename
            self.logger.info(f"📄 可读性报告已保存: {html_filename}")

        return saved_files

    def _generate_human_readable_html(self, report: Dict[str, Any]) -> str:
        """
        生成人工可读的HTML报告（决策导向）

        Args:
            report: 报告数据

        Returns:
            str: HTML内容
        """
        # 提取关键数据
        report_info = report.get('report_info', {})
        exec_summary = report.get('execution_summary', {})
        errors = report.get('errors_and_issues', [])
        performance = report.get('performance_metrics', {})

        # 确定整体状态
        is_success = exec_summary.get('overall_success', False)
        status_icon = "✅ 成功" if is_success else "❌ 失败"
        status_color = "#28a745" if is_success else "#dc3545"

        # 分析失败原因
        failure_reason = "测试流程正常完成" if is_success else "关键功能验证失败"

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧪 自动化测试报告 - 决策版</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
        }}

        .status-success {{
            background: #28a745;
            color: white;
        }}

        .status-failure {{
            background: #dc3545;
            color: white;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .card-title {{
            font-size: 14px;
            font-weight: 600;
            color: #666;
            margin-bottom: 10px;
        }}

        .card-content {{
            font-size: 24px;
            font-weight: bold;
        }}

        .failure-section {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }}

        .failure-title {{
            color: #856404;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
        }}

        .failure-detail {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 10px;
            border-left: 4px solid #f59e0b;
        }}

        .action-items {{
            list-style: none;
            padding: 0;
        }}

        .action-item {{
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }}

        .action-item:last-child {{
            border-bottom: none;
        }}

        .priority-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }}

        .priority-p0 {{
            background: #dc3545;
            color: white;
        }}

        .priority-p1 {{
            background: #f59e0b;
            color: white;
        }}

        .priority-p2 {{
            background: #6c757d;
            color: white;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 14px;
        }}

        @media (max-width: 768px) {{
            .summary-grid {{
                grid-template-columns: 1fr;
            }}

            .container {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 自动化测试报告</h1>
            <div class="status-badge status-{'success' if is_success else 'failure'}">
                {status_icon}
            </div>
            <p style="font-size: 16px; margin: 0;">
                <strong>测试结论：</strong>{failure_reason}
            </p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="card-title">📅 测试时间</div>
                <div class="card-content">{report_info.get('generated_at', '').replace('T', ' ').split('.')[0]}</div>
            </div>
            <div class="summary-card">
                <div class="card-title">🌐 测试地址</div>
                <div class="card-content">{report.get('test_results', [{}])[0].get('details', {}).get('url', 'N/A') if report.get('test_results') else 'N/A'}</div>
            </div>
            <div class="summary-card">
                <div class="card-title">⏱️ 总耗时</div>
                <div class="card-content">{report.get('total_test_time', 0)/1000:.2f}秒</div>
            </div>
        </div>

        {f'<div class="failure-section" {"" if is_success else ""}>'}
            <div class="failure-title">❌ 失败原因分析</div>
            {self._format_failure_cause(errors[0] if errors else {'error': '未知错误'})}
            {self._generate_action_plan(errors[0] if errors else {'step': 'unknown'})}
        </div>

        <div class="footer">
            <p>报告生成时间：{report_info.get('generated_at', '').replace('T', ' ')}</p>
            <p>📄 JSON格式供系统集成使用 | HTML格式供人工查看</p>
        </div>
    </div>
</body>
</html>"""

        return html_content

    def _format_failure_cause(self, error: Dict[str, Any]) -> str:
        """格式化失败原因"""
        step = error.get('step', 'unknown')
        error_msg = error.get('error', '未知错误')

        if step == 'open_site':
            if '元素' in error_msg and 'prompt_input' in error_msg:
                return "页面关键交互元素未找到（提示词输入框）"
            return f"步骤「{step}」执行失败：{error_msg}"

        return f"步骤「{step}」执行失败：{error_msg}"

    def _generate_action_plan(self, error: Dict[str, Any]) -> str:
        """生成行动建议"""
        step = error.get('step', 'unknown')

        if step == 'open_site':
            return '''
            <div class="action-items">
                <div class="action-item">
                    <span class="priority-badge priority-p0">P0</span>
                    立即确认页面DOM结构
                </div>
                <div class="action-item">
                    <span class="priority-badge priority-p1">P1</span>
                    更新测试机器人选择器配置
                </div>
            </div>
            '''

        return '<div class="action-items"><div class="action-item"><span class="priority-badge priority-p2">P2</span>分析具体错误详情</div></div>'
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自动化测试报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .step {{
            margin: 15px 0;
            padding: 15px;
            border-left: 4px solid #007bff;
            background: #f8f9fa;
        }}
        .step.success {{ border-left-color: #28a745; }}
        .step.error {{ border-left-color: #dc3545; }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .error-list {{
            background: #f8d7da;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .recommendations {{
            background: #d1ecf1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>自动化测试报告</h1>
            <p class="timestamp">生成时间: {generated_at}</p>
        </div>

        <div class="summary">
            <h2>执行摘要</h2>
            <p><strong>总体状态:</strong> <span class="{status_class}">{status_text}</span></p>
            <p><strong>成功步骤:</strong> {successful_steps}/{total_steps}</p>
            <p><strong>成功率:</strong> {success_rate:.1f}%</p>
            <p><strong>总耗时:</strong> {total_duration_ms}ms</p>
        </div>

        <h2>测试步骤详情</h2>
        {step_details_html}

        <h2>性能指标</h2>
        <div class="metrics">
            {metrics_html}
        </div>

        {errors_html}

        {recommendations_html}
    </div>
</body>
</html>
        """

        # 填充模板数据
        summary = report.get('execution_summary', {})
        metrics = report.get('performance_metrics', {})
        errors = report.get('errors_and_issues', [])
        recommendations = report.get('recommendations', [])
        test_results = report.get('test_results', [])

        # 状态相关
        status_class = 'success' if summary.get('overall_success') else 'error'
        status_text = '成功' if summary.get('overall_success') else '失败'

        # 步骤详情 HTML
        step_details_html = ""
        for result in test_results:
            step_name = result.get('step', 'unknown')
            success = result.get('success', False)
            duration = result.get('metrics', {}).get('total_time', 0)
            error = result.get('error', '')

            step_class = 'success' if success else 'error'
            step_details_html += f"""
            <div class="step {step_class}">
                <h3>{step_name}</h3>
                <p><strong>状态:</strong> <span class="{step_class}">{'成功' if success else '失败'}</span></p>
                <p><strong>耗时:</strong> {duration}ms</p>
                {f'<p><strong>错误:</strong> {error}</p>' if error else ''}
            </div>
            """

        # 指标 HTML
        metrics_html = ""
        step_metrics = metrics.get('step_metrics', {})
        for step_name, metric_data in step_metrics.items():
            duration = metric_data.get('duration', 0)
            status = '✅' if metric_data.get('success', False) else '❌'
            metrics_html += f"""
            <div class="metric">
                <h4>{step_name}</h4>
                <p>{status}</p>
                <p>{duration}ms</p>
            </div>
            """

        # 错误 HTML
        errors_html = ""
        if errors:
            errors_html = """
            <div class="error-list">
                <h2>错误和问题</h2>
            """
            for error in errors:
                errors_html += f"""
                <div>
                    <h4>{error.get('step', 'unknown')} - {error.get('severity', 'medium')}</h4>
                    <p>{error.get('error', '')}</p>
                </div>
                """
            errors_html += "</div>"

        # 建议HTML
        recommendations_html = ""
        if recommendations:
            recommendations_html = """
            <div class="recommendations">
                <h2>建议和改进措施</h2>
                <ul>
            """
            for rec in recommendations:
                recommendations_html += f"<li>{rec}</li>"
            recommendations_html += "</ul></div>"

        return html_template.format(
            generated_at=report.get('report_info', {}).get('generated_at', ''),
            status_class=status_class,
            status_text=status_text,
            successful_steps=summary.get('successful_steps', 0),
            total_steps=summary.get('total_steps', 0),
            success_rate=summary.get('success_rate', 0),
            total_duration_ms=summary.get('total_duration', 0),
            step_details_html=step_details_html,
            metrics_html=metrics_html,
            errors_html=errors_html,
            recommendations_html=recommendations_html
        )