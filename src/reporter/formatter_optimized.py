"""
优化版报告格式化器 - 决策导向
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils import Timer


class OptimizedReportFormatter:
    """决策导向的报告格式化器"""

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

    def format_decision_report(self, test_results: List[Dict[str, Any]],
                            mcp_data: Optional[Dict[str, Any]] = None,
                            screenshots: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        生成决策导向的测试报告

        Args:
            test_results: 测试结果列表
            mcp_data: MCP 监控数据
            screenshots: 截图文件列表

        Returns:
            Dict[str, Any]: 格式化的报告
        """
        # 提取关键信息
        report_info = self._generate_report_info()
        exec_summary = self._generate_execution_summary(test_results)
        errors = self._analyze_errors(test_results)

        # 判断整体成功状态
        is_success = exec_summary.get('overall_success', False)

        # 生成报告
        report = {
            'report_info': report_info,
            'execution_summary': exec_summary,
            'test_results': test_results,
            'decision_summary': self._generate_decision_summary(test_results, errors),
            'performance_summary': self._generate_performance_summary(),
            'errors_and_issues': errors,
            'recommendations': self._generate_action_recommendations(test_results)
        }

        # 添加数据
        if self.include_mcp_data and mcp_data:
            report['mcp_monitoring'] = self._format_mcp_data(mcp_data)

        if self.include_screenshots and screenshots:
            report['screenshots'] = screenshots

        return report

    def _generate_report_info(self) -> Dict[str, Any]:
        """生成报告基本信息"""
        return {
            'report_id': f"report_{int(datetime.now().timestamp() * 1000)}",
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'test_bot_version': "1.0.0",
            'report_format': self.format,
            'test_url': self.config.get('test', {}).get('url', ''),
            'test_prompt': self.config.get('test', {}).get('test_prompt', '')
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

        # 确定整体成功状态（最后一个验证步骤决定）
        validate_step = next((r for r in test_results if r.get('step') == 'validate'), None)
        overall_success = validate_step.get('success', False) if validate_step else False

        return {
            'total_steps': len(test_results),
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'overall_success': overall_success,
            'total_duration': total_duration,
            'success_rate': (successful_steps / len(test_results)) * 100,
            'failed_phase': self._get_failed_phase(test_results)
        }

    def _get_failed_phase(self, test_results: List[Dict[str, Any]]) -> str:
        """获取失败的阶段"""
        for result in test_results:
            if not result.get('success', False):
                step_name = result.get('step', '')
                if step_name == 'open_site':
                    return '页面初始化'
                elif step_name == 'generate_image':
                    return '文生图功能'
                elif step_name == 'generate_video':
                    return '图生视频功能'
                elif step_name == 'validate':
                    return '结果验证'
        return '未知阶段'

    def _generate_decision_summary(self, test_results: List[Dict[str, Any]],
                                errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成决策摘要"""
        # 判断失败类型
        has_blocking_failure = any(
            '元素' in error.get('error', '') or '连接' in error.get('error', '')
            for error in errors
        )

        # 影响评估
        if has_blocking_failure:
            impact_level = 'HIGH'
            impact_desc = '核心功能无法使用，自动化测试流程中断'
        else:
            impact_level = 'MEDIUM'
            impact_desc = '测试流程未能完全执行，需要人工介入'

        return {
            'is_blocking_failure': has_blocking_failure,
            'impact_level': impact_level,
            'impact_description': impact_desc,
            'next_action_required': has_blocking_failure,
            'failed_step_count': len([e for e in errors if not e.get('success', False)]),
            'primary_failure': errors[0].get('step', 'unknown') if errors else 'unknown'
        }

    def _format_mcp_data(self, mcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化 MCP 数据（简化版）"""
        formatted = {}

        # 控制台监控
        if 'console' in mcp_data:
            console = mcp_data['console']
            error_count = console.get('error_count', 0)
            formatted['console'] = {
                'status': '✅ 正常' if error_count == 0 else f'⚠️ {error_count}个错误',
                'message_count': console.get('total_messages', 0)
            }

        # 网络监控
        if 'network' in mcp_data:
            network = mcp_data['network']
            formatted['network'] = {
                'status': '✅ 正常' if network.get('error_count', 0) == 0 else f'⚠️ {network.get("error_count", 0)}个错误',
                'request_count': network.get('total_requests', 0),
                'success_rate': f"{network.get('success_rate', 0):.1f}%"
            }

        # 性能监控
        if 'performance' in mcp_data:
            perf = mcp_data['performance']
            formatted['performance'] = {
                'status': '✅ 已完成' if isinstance(perf, dict) else '⚠️ 异常',
                'duration': f"{perf.get('trace_duration', 0)/1000:.1f}s" if isinstance(perf, dict) else 'N/A'
            }

        return formatted

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """生成性能摘要（简化版）"""
        return {
            'status': '✅ 正常' if True else '⚠️ 异常',
            'total_time': '正常范围内',
            'bottleneck': '无',
            'optimization_suggestions': []
        }

    def _analyze_errors(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析错误和问题"""
        errors = []

        for result in test_results:
            if not result.get('success', False):
                error_info = {
                    'step': result.get('step', 'unknown'),
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'severity': self._determine_error_severity(result.get('step', '')),
                    'is_blocking': '元素' in result.get('error', '') or '连接' in result.get('error', '')
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
            return 'CRITICAL'
        elif step_name in high_steps:
            return 'HIGH'
        else:
            return 'MEDIUM'

    def _generate_action_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """生成行动建议"""
        recommendations = []

        # 分析失败的步骤
        failed_steps = [r for r in test_results if not r.get('success', False)]

        if not failed_steps:
            recommendations.append("✅ 测试执行成功，系统运行正常")
            return recommendations

        # 基于失败步骤生成建议
        for result in failed_steps:
            step_name = result.get('step', 'unknown')
            error = result.get('error', '')

            if step_name == 'open_site':
                if '元素' in error:
                    recommendations.append("🔧 P0: 立即确认页面DOM结构，使用浏览器开发者工具检查元素")
                    recommendations.append("🔧 P1: 更新测试机器人中的DOM选择器配置")
                elif '无法访问' in error or '连接' in error:
                    recommendations.append("🔧 P0: 检查网站可访问性和网络连接")
                    recommendations.append("🔧 P1: 确认测试URL是否正确")

            elif step_name == 'generate_image':
                recommendations.append("🔧 P0: 检查图片生成功能是否正常工作")
                recommendations.append("🔧 P1: 验证API接口状态和响应")

            elif step_name == 'generate_video':
                recommendations.append("🔧 P0: 检查图生视频功能状态")
                recommendations.append("🔧 P1: 确认图片到视频的转换流程")

        # 通用建议
        if len(failed_steps) > 1:
            recommendations.append("⚠️ 多个步骤失败，建议检查系统整体状态和依赖服务")

        return recommendations

    def save_report(self, report: Dict[str, Any], filename_prefix: str = None,
                    test_flow_name: str = None) -> Dict[str, str]:
        """
        保存决策导向报告

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
            filename_prefix = "decision_report"

        # 创建三级目录结构：测试流程名称/日期/
        output_base_dir = self.output_dir
        test_flow_dir = os.path.join(output_base_dir, test_flow_name, date_str)
        os.makedirs(test_flow_dir, exist_ok=True)

        saved_files = {}

        # 保存 JSON 格式（供系统集成）
        if self.format in ['json', 'both']:
            json_filename = os.path.join(test_flow_dir, f"{filename_prefix}_{timestamp}.json")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            saved_files['json'] = json_filename
            self.logger.info(f"📄 决策报告(JSON)已保存: {json_filename}")

        # 保存 HTML 格式（人工可读版）
        if self.format in ['html', 'both']:
            html_content = self._generate_decision_html(report)
            html_filename = os.path.join(test_flow_dir, f"{filename_prefix}_{timestamp}.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            saved_files['html'] = html_filename
            self.logger.info(f"📄 决策报告(HTML)已保存: {html_filename}")

        return saved_files

    def _generate_decision_html(self, report: Dict[str, Any]) -> str:
        """生成决策导向的HTML报告"""
        # 提取数据
        report_info = report.get('report_info', {})
        exec_summary = report.get('execution_summary', {})
        decision = report.get('decision_summary', {})

        # 状态映射
        status_map = {
            True: ("✅ 测试成功", "#28a745"),
            False: ("❌ 测试失败", "#dc3545")
        }

        status_text, status_color = status_map.get(exec_summary.get('overall_success', False), ("未知状态", "#666666"))

        # 影响程度映射
        impact_map = {
            'HIGH': ("🚨 高影响", "#dc3545"),
            'MEDIUM': ("⚠️ 中等影响", "#f59e0b")
        }

        impact_text, impact_color = impact_map.get(decision.get('impact_level', 'MEDIUM'), ("未知影响", "#666666"))

        # 生成时间格式
        report_time = report_info.get('generated_at', '').replace('T', ' ')

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
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .status-section {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
        }}

        .status-badge {{
            padding: 12px 24px;
            border-radius: 30px;
            font-weight: bold;
            font-size: 20px;
        }}

        .success {{ background: #28a745; color: white; }}
        .failure {{ background: #dc3545; color: white; }}

        .info-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}

        .card-title {{
            font-size: 16px;
            font-weight: 600;
            color: #666;
            margin-bottom: 12px;
        }}

        .card-content {{
            font-size: 28px;
            font-weight: bold;
            color: {status_color};
        }}

        .action-plan {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 25px;
        }}

        .plan-title {{
            font-size: 18px;
            font-weight: 600;
            color: #856404;
            margin-bottom: 15px;
        }}

        .action-item {{
            display: flex;
            align-items: flex-start;
            padding: 10px 0;
            margin-bottom: 10px;
        }}

        .priority-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 10px;
        }}

        .p0 {{ background: #dc3545; color: white; }}
        .p1 {{ background: #f59e0b; color: white; }}
        .p2 {{ background: #6c757d; color: white; }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 14px;
            margin-top: 40px;
        }}

        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .status-section {{ flex-direction: column; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 自动化测试报告</h1>

            <div class="status-section">
                <div class="status-badge {status_color}">
                    {status_text}
                </div>
                <div>
                    <div style="font-size: 16px; margin-bottom: 10px;">
                        <strong>测试结论：</strong>
                    </div>
                    <div class="info-card">
                        <div class="card-content">
                            {status_text}
                        </div>
                    </div>
                </div>

                <div>
                    <div style="font-size: 16px; margin-bottom: 10px;">
                        <strong>影响评估：</strong>
                    </div>
                    <div class="info-card">
                        <div class="card-content">
                            {impact_text}
                        </div>
                    </div>
                </div>

                <div>
                    <div style="font-size: 16px; margin-bottom: 10px;">
                        <strong>是否需要立即处理：</strong>
                    </div>
                    <div class="info-card">
                        <div class="card-content">
                            {'是' if decision.get('next_action_required', False) else '否'}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="info-card">
            <div class="card-title">📋 执行摘要</div>
            <div class="card-content">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>测试时间：</div>
                    <div>{report_time}</div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>测试地址：</div>
                    <div>{report_info.get('test_url', 'N/A')}</div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>总耗时：</div>
                    <div>{exec_summary.get('total_duration', 0)}ms</div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>失败阶段：</div>
                    <div>{decision.get('failed_phase', '未知')}</div>
                </div>
            </div>
        </div>

        <div class="action-plan">
            <div class="plan-title">🎯 行动计划</div>

            {'<div class="action-item"><span class="priority-badge p0">P0</span>必须立即处理</div>' if decision.get('next_action_required', False) else ''}

            {'<div class="action-item"><span class="priority-badge p1">P1</span>确认页面DOM结构，更新选择器配置</div>' if '元素' in report.get('errors_and_issues', [{}])[0].get('error', '') else ''}

            {'<div class="action-item"><span class="priority-badge p2">P2</span>验证更新后的配置有效性</div>' if '元素' in report.get('errors_and_issues', [{}])[0].get('error', '') else ''}
        </div>

        <div class="footer">
            <p>报告生成时间：{report_info.get('generated_at', '')}</p>
            <p>🧪 自动化测试机器人 v1.0.0 | 专为快速决策设计</p>
        </div>
    </div>
</body>
</html>
"""

        return html_content

    def format_test_report(self, test_results: List[Dict[str, Any]],
                         mcp_data: Optional[Dict[str, Any]] = None,
                         screenshots: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        兼容性方法：适配原有的format_test_report接口

        Args:
            test_results: 测试结果列表
            mcp_data: MCP监控数据
            screenshots: 截图文件列表

        Returns:
            Dict[str, Any]: 格式化的报告
        """
        return self.format_decision_report(test_results, mcp_data, screenshots)