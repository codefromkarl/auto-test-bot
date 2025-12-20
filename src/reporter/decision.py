"""Decision-oriented reporting system"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class DecisionReporter:
    """
    Generates decision-oriented reports focused on task completion.
    Follows MVP freeze specifications with JSON format.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize decision reporter

        Args:
            config: System configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(config.get('reporting', {}).get('output_dir', 'reports'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate decision-oriented report with all required fields

        Args:
            execution_result: Workflow execution result

        Returns:
            Report data with summary and MCP analysis
        """
        # Get execution data with defaults
        phase_results = execution_result.get('phase_results', [])
        mcp_observations = execution_result.get('mcp_observations', [])
        success_criteria = execution_result.get('success_criteria') or []
        if not isinstance(success_criteria, list):
            success_criteria = [str(success_criteria)]

        # Calculate summary statistics (兼容 steps_executed 为 list 或 int 的情况)
        def _count_steps_executed(value: Any) -> int:
            if value is None:
                return 0
            if isinstance(value, int):
                return int(value)
            if isinstance(value, list):
                return len(value)
            return 0

        total_steps = sum(_count_steps_executed(phase.get('steps_executed')) for phase in phase_results)

        duration_seconds = execution_result.get('duration_seconds', 0)
        try:
            total_duration = float(duration_seconds) if duration_seconds is not None else 0.0
        except Exception:
            total_duration = 0.0

        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'format_version': '1.0',
                'workflow_name': execution_result.get('workflow_name', 'unknown')
            },
            'summary': {
                'workflow_name': execution_result.get('workflow_name', 'unknown'),
                'overall_success': execution_result.get('overall_success', False),
                'total_duration': total_duration,
                'total_phases': len(phase_results),
                'total_steps': total_steps,
                'phases_completed': len([p for p in phase_results if p.get('success', False)]),
                'errors_detected': len(execution_result.get('error_history', []))
            },
            'decision_summary': {
                'task_completed': execution_result.get('overall_success', False),
                'success_criterion': str(success_criteria[0]) if success_criteria else '用户能够完成关键任务',
                'success_criteria': [str(x) for x in success_criteria],
                'focus': '决策导向，非质量评估'
            },
            'execution_summary': {
                'workflow_name': execution_result.get('workflow_name', 'unknown'),
                'overall_success': execution_result.get('overall_success', False),
                'total_phases': len(phase_results),
                'execution_history': execution_result.get('execution_history', [])
            },
            'phases': phase_results,
            'failure_analysis': self._analyze_failure(execution_result),
            'mcp_analysis': {
                'observations_count': len(mcp_observations),
                'performance_metrics': self._extract_performance_metrics(mcp_observations),
                'observations_by_type': self._group_observations_by_type(mcp_observations)
            },
            'mcp_evidence': execution_result.get('mcp_evidence', {}),
            'recommendations': self._generate_recommendations(execution_result)
        }

        # Classify failure type if present
        if execution_result.get('error'):
            report['failure_analysis']['type'] = self._classify_error(execution_result['error'])

        return report

    def _analyze_failure(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze failure for explainability

        Args:
            execution_result: Execution result with error

        Returns:
            Failure analysis
        """
        error = execution_result.get('error', {})

        analysis = {
            'occurred': bool(error),
            'summary': '无失败' if not error else '检测到失败',
            'impact': '任务完成受阻'
        }

        if not error:
            return analysis

        # Analyze error based on type and context
        error_type = error.get('type', 'UNKNOWN')
        error_message = error.get('error', 'Unknown error')

        analysis.update({
            'type': error_type,
            'error_message': error_message,
            'explainability': self._explain_error(error_type, error_message),
            'mitigation': self._suggest_mitigation(error_type, error_message)
        })

        # Extract context from error
        if 'phase' in error:
            analysis['failure_phase'] = error['phase']
        if 'step' in error:
            analysis['failure_step'] = error['step']

        return analysis

    def _classify_error(self, error: Dict[str, Any]) -> str:
        """
        Classify error into four categories

        Args:
            error: Error information

        Returns:
            Error type classification
        """
        error_type = error.get('type', '').upper()
        error_message = error.get('error', '').lower()

        # Known types
        if error_type in ['TEST_CONFIG_ERROR', 'SYSTEM_FUNCTIONAL_ERROR', 'SYSTEM_PERFORMANCE_ERROR', 'ENVIRONMENT_ERROR']:
            return error_type

        # Classify based on message patterns
        if any(keyword in error_message for keyword in ['config', 'yaml', 'file not found']):
            return 'TEST_CONFIG_ERROR'
        elif any(keyword in error_message for keyword in ['timeout', 'element not found', 'click failed', 'input failed']):
            return 'SYSTEM_FUNCTIONAL_ERROR'
        elif any(keyword in error_message for keyword in ['slow', 'performance', 'memory', 'cpu']):
            return 'SYSTEM_PERFORMANCE_ERROR'
        else:
            return 'ENVIRONMENT_ERROR'

    def _explain_error(self, error_type: str, error_message: str) -> str:
        """
        Generate explainable error description

        Args:
            error_type: Classified error type
            error_message: Original error message

        Returns:
            Human-readable explanation
        """
        explanations = {
            'TEST_CONFIG_ERROR': '配置或设置问题阻止了测试执行',
            'SYSTEM_FUNCTIONAL_ERROR': '系统功能未能按预期运行',
            'SYSTEM_PERFORMANCE_ERROR': '系统性能问题阻碍了及时完成',
            'ENVIRONMENT_ERROR': '外部环境因素影响了测试执行'
        }

        base_explanation = explanations.get(error_type, 'Unknown error type')
        return f"{base_explanation}: {error_message}"

    def _suggest_mitigation(self, error_type: str, error_message: str) -> str:
        """
        Suggest mitigation based on error type

        Args:
            error_type: Classified error type
            error_message: Original error message

        Returns:
            Mitigation suggestion
        """
        mitigations = {
            'TEST_CONFIG_ERROR': '检查配置文件格式和必需参数',
            'SYSTEM_FUNCTIONAL_ERROR': '验证选择器是否正确且元素存在',
            'SYSTEM_PERFORMANCE_ERROR': '增加超时值或检查系统资源',
            'ENVIRONMENT_ERROR': '检查网络连接和目标可用性'
        }

        return mitigations.get(error_type, 'Review error details and system logs')

    def _generate_recommendations(self, execution_result: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations

        Args:
            execution_result: Execution result

        Returns:
            List of recommendations
        """
        recommendations = []

        if execution_result.get('overall_success'):
            recommendations.append('任务成功完成 - 持续监控一致性')
            return recommendations

        # Failure recommendations based on error
        error = execution_result.get('error', {})
        error_type = error.get('type', '')

        if error_type == 'TEST_CONFIG_ERROR':
            recommendations.extend([
                '验证工作流YAML语法',
                '检查所有必需参数是否已提供',
                '验证文件路径和权限'
            ])
        elif error_type == 'SYSTEM_FUNCTIONAL_ERROR':
            recommendations.extend([
                '更新当前UI的元素选择器',
                '为动态内容增加等待超时',
                '验证目标应用可访问性'
            ])
        elif error_type == 'SYSTEM_PERFORMANCE_ERROR':
            recommendations.extend([
                '增加配置中的超时值',
                '检查系统资源可用性',
                '考虑禁用非必要监控'
            ])
        elif error_type == 'ENVIRONMENT_ERROR':
            recommendations.extend([
                '检查网络连接',
                '验证目标应用可用性',
                '在环境问题解决后重试执行'
            ])

        return recommendations

    def _extract_performance_metrics(self, mcp_observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract performance metrics from MCP observations

        Args:
            mcp_observations: List of MCP observations

        Returns:
            Performance metrics dictionary
        """
        metrics = {
            'avg_response_time': 0,
            'total_requests': 0,
            'error_count': 0,
            'load_times': []
        }

        if not mcp_observations:
            return metrics

        network_observations = [obs for obs in mcp_observations if obs.get('type') == 'network']
        performance_observations = [obs for obs in mcp_observations if obs.get('type') == 'performance']

        # Extract network metrics
        if network_observations:
            response_times = []
            for obs in network_observations:
                data = obs.get('data', {})
                if 'load_time' in data:
                    response_times.append(data['load_time'])
                    metrics['load_times'].append(data['load_time'])

            if response_times:
                metrics['avg_response_time'] = sum(response_times) / len(response_times)
            metrics['total_requests'] = len(network_observations)

        # Extract performance metrics
        if performance_observations:
            for obs in performance_observations:
                data = obs.get('data', {})
                if data.get('memory_usage'):
                    metrics['peak_memory'] = data['memory_usage']
                if data.get('cpu_usage'):
                    metrics['peak_cpu'] = data['cpu_usage']

        return metrics

    def _group_observations_by_type(self, mcp_observations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group MCP observations by type

        Args:
            mcp_observations: List of MCP observations

        Returns:
            Observations grouped by type
        """
        grouped = {}
        for obs in mcp_observations:
            obs_type = obs.get('type', 'unknown')
            if obs_type not in grouped:
                grouped[obs_type] = []
            grouped[obs_type].append(obs)
        return grouped

    def save_report(self, report: Dict[str, Any], filename_prefix: str = None) -> Dict[str, str]:
        """
        Save report to files with workflow-based directory structure

        Args:
            report: Report data to save

        Returns:
            Dictionary of saved file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_name = report.get('report_metadata', {}).get('workflow_name', 'unknown')

        # Create workflow-specific subdirectory: workflow_name + timestamp
        subdir_name = f"{workflow_name}_{timestamp}"
        workflow_dir = self.output_dir / subdir_name
        workflow_dir.mkdir(parents=True, exist_ok=True)

        base_filename = filename_prefix or f"workflow_report_{timestamp}"

        saved_files = {}

        # Save JSON report
        json_path = workflow_dir / "report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        saved_files['json'] = str(json_path)

        # Save human-readable summary
        summary_path = workflow_dir / "summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(self._format_summary(report))
        saved_files['summary'] = str(summary_path)

        # Save HTML report
        html_path = workflow_dir / "report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self._format_html_report(report))
        saved_files['html'] = str(html_path)

        self.logger.info(f"Report saved to: {workflow_dir}")
        return saved_files

    def _format_summary(self, report: Dict[str, Any]) -> str:
        """
        Format human-readable summary in Chinese

        Args:
            report: Report data

        Returns:
            Formatted summary text in Chinese
        """
        summary = []
        summary.append(f"工作流: {report['report_metadata']['workflow_name']}")
        summary.append(f"生成时间: {report['report_metadata']['generated_at']}")

        # Decision section
        decision = report['decision_summary']
        summary.append(f"\n决策摘要:")
        summary.append(f"  任务完成: {'✅ 是' if decision['task_completed'] else '❌ 否'}")
        summary.append(f"  成功标准: {decision['success_criterion']}")

        # Failure analysis if applicable
        failure = report['failure_analysis']
        if failure['occurred']:
            summary.append(f"\n失败分析:")
            summary.append(f"  类型: {failure['type']}")
            summary.append(f"  说明: {failure['explainability']}")
            summary.append(f"  缓解措施: {failure['mitigation']}")

        # Recommendations
        if report['recommendations']:
            summary.append(f"\n建议:")
            for rec in report['recommendations']:
                summary.append(f"  • {rec}")

        return '\n'.join(summary)

    def _format_html_report(self, report: Dict[str, Any]) -> str:
        """
        Format report as HTML

        Args:
            report: Report data

        Returns:
            HTML formatted report
        """
        summary = report.get('summary') or {}
        try:
            total_duration = float(summary.get('total_duration')) if summary.get('total_duration') is not None else 0.0
        except Exception:
            total_duration = 0.0

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>工作流执行报告 - {report['report_metadata']['workflow_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .metadata {{ background: #e9ecef; padding: 15px; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
        .observation {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>工作流执行报告</h1>
        <p><strong>工作流:</strong> {report['report_metadata']['workflow_name']}</p>
        <p><strong>生成时间:</strong> {report['report_metadata']['generated_at']}</p>
        <p><strong>状态:</strong> {'<span class="success">✅ 成功</span>' if report['summary']['overall_success'] else '<span class="failure">❌ 失败</span>'}</p>
    </div>

	    <div class="section">
	        <h2>概要</h2>
	        <table>
	            <tr><th>总耗时</th><td>{total_duration:.2f}秒</td></tr>
	            <tr><th>总阶段数</th><td>{report['summary']['total_phases']}</td></tr>
	            <tr><th>总步骤数</th><td>{report['summary']['total_steps']}</td></tr>
	            <tr><th>已完成阶段</th><td>{report['summary']['phases_completed']}</td></tr>
	            <tr><th>检测到错误</th><td>{report['summary']['errors_detected']}</td></tr>
	        </table>
	    </div>

    <div class="section">
        <h2>执行阶段</h2>
"""

        # Add phases
        for phase in report.get('phases', []):
            status_class = 'success' if phase.get('success', False) else 'failure'
            status_icon = '✅' if phase.get('success', False) else '❌'
            steps_executed = phase.get('steps_executed', [])
            if isinstance(steps_executed, int):
                steps_count = int(steps_executed)
            elif isinstance(steps_executed, list):
                steps_count = len(steps_executed)
            else:
                steps_count = 0
            html += f"""
        <div class="metadata">
            <h3>{phase.get('name', '未知阶段')} {status_icon}</h3>
            <p><strong>状态:</strong> <span class="{status_class}">{'成功' if phase.get('success', False) else '失败'}</span></p>
	            <p><strong>耗时:</strong> {float(phase.get('duration_seconds') or 0.0):.2f}秒</p>
	            <p><strong>已执行步骤:</strong> {steps_count}</p>
	        </div>
"""

        html += """
    </div>

    <div class="section">
        <h2>MCP分析</h2>
        <p><strong>观察数量:</strong> """ + str(report.get('mcp_analysis', {}).get('observations_count', 0)) + """</p>
"""

        # Add observations by type
        observations_by_type = report.get('mcp_analysis', {}).get('observations_by_type', {})
        for obs_type, observations in observations_by_type.items():
            html += f"""
        <div class="observation">
            <h4>{obs_type.title()}观察记录 ({len(observations)})</h4>
"""
            for obs in observations[:3]:  # Show first 3 observations
                data = obs.get('data', {})
                html += f"<p><strong>数据:</strong> {data}</p>"
            html += "</div>"

        html += """
    </div>

    <div class="section">
        <h2>决策摘要</h2>
        <div class="metadata">
            <p><strong>任务完成:</strong> """ + ('✅ 是' if report['decision_summary']['task_completed'] else '❌ 否') + """</p>
            <p><strong>成功标准:</strong> """ + report['decision_summary']['success_criterion'] + """</p>
            <p><strong>重点:</strong> """ + report['decision_summary']['focus'] + """</p>
        </div>
    </div>

</body>
</html>
"""
        return html
