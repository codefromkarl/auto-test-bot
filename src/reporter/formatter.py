"""
报告格式化器
格式化测试结果和生成结构化报告
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..utils import Timer


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
        report = {
            'report_info': self._generate_report_info(),
            'execution_summary': self._generate_execution_summary(test_results),
            'test_results': test_results,
            'performance_metrics': self._generate_performance_metrics(test_results),
            'errors_and_issues': self._analyze_errors(test_results),
            'recommendations': self._generate_recommendations(test_results)
        }

        # 添加 MCP 数据
        if self.include_mcp_data and mcp_data:
            report['mcp_monitoring'] = mcp_data

        # 添加截图信息
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

    def _extract_test_prompt(self, test_results: List[Dict[str, Any]]) -> Optional[str]:
        """提取测试提示词"""
        for result in test_results:
            if result.get('step') == 'generate_image':
                return result.get('details', {}).get('prompt_used')
        return None

    def save_report(self, report: Dict[str, Any], filename_prefix: str = None) -> Dict[str, str]:
        """
        保存报告到文件

        Args:
            report: 报告数据
            filename_prefix: 文件名前缀

        Returns:
            Dict[str, str]: 保存的文件路径
        """
        import os

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename_prefix:
            filename_prefix = f"test_report_{timestamp}"

        saved_files = {}

        # 根据格式保存报告
        if self.format in ['json', 'both']:
            json_filename = os.path.join(self.output_dir, f"{filename_prefix}.json")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            saved_files['json'] = json_filename
            self.logger.info(f"JSON 报告已保存到: {json_filename}")

        if self.format in ['html', 'both']:
            html_filename = os.path.join(self.output_dir, f"{filename_prefix}.html")
            html_content = self._generate_html_report(report)
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            saved_files['html'] = html_filename
            self.logger.info(f"HTML 报告已保存到: {html_filename}")

        return saved_files

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """生成 HTML 格式报告"""
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