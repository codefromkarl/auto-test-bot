"""
Data-TestId 覆盖率报告生成器

生成详细的 data-testid 覆盖率报告，用于 CI 和持续改进。
"""

import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class TestIdCoverageReporter:
    """Data-TestId 覆盖率报告生成器"""

    def __init__(self, config_path: str = None):
        """
        初始化报告生成器

        Args:
            config_path: 契约配置文件路径
        """
        self.config_path = config_path or "config/required_testids.yaml"
        self.required_config = self._load_required_config()

    def _load_required_config(self) -> Dict[str, Any]:
        """加载必需的 testid 配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"无法加载契约配置: {e}")

    def generate_coverage_report(self, locator_metrics: Dict[str, Any],
                           test_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成覆盖率报告

        Args:
            locator_metrics: 定位器度量数据
            test_context: 测试上下文信息

        Returns:
            Dict[str, Any]: 完整的覆盖率报告
        """
        report = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'testid_coverage',
                'version': '1.0.0'
            },
            'summary': self._generate_summary(locator_metrics),
            'detailed_metrics': locator_metrics,
            'coverage_analysis': self._analyze_coverage(locator_metrics),
            'recommendations': self._generate_recommendations(locator_metrics),
            'test_context': test_context or {}
        }

        return report

    def _generate_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要信息"""
        total_locations = metrics.get('total_locations', 0)
        data_testid_hits = metrics.get('data_testid_hits', 0)
        fallback_hits = metrics.get('fallback_hits', 0)
        failures = metrics.get('location_failures', 0)

        summary = {
            'total_element_attempts': total_locations,
            'data_testid_successes': data_testid_hits,
            'fallback_successes': fallback_hits,
            'location_failures': failures,
            'success_rate': round((data_testid_hits + fallback_hits) / total_locations * 100, 2) if total_locations > 0 else 0,
            'data_testid_hit_rate': round(data_testid_hits / total_locations * 100, 2) if total_locations > 0 else 0,
            'fallback_rate': round(fallback_hits / total_locations * 100, 2) if total_locations > 0 else 0,
            'failure_rate': round(failures / total_locations * 100, 2) if total_locations > 0 else 0
        }

        # 计算等级
        hit_rate = summary['data_testid_hit_rate']
        if hit_rate >= 95:
            summary['quality_grade'] = 'A'
            summary['quality_description'] = '优秀 - data-testid 覆盖率很高'
        elif hit_rate >= 85:
            summary['quality_grade'] = 'B'
            summary['quality_description'] = '良好 - data-testid 覆盖率较高'
        elif hit_rate >= 70:
            summary['quality_grade'] = 'C'
            summary['quality_description'] = '一般 - data-testid 覆盖率中等'
        else:
            summary['quality_grade'] = 'D'
            summary['quality_description'] = '需要改进 - data-testid 覆盖率偏低'

        return summary

    def _analyze_coverage(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """分析覆盖率详情"""
        element_details = metrics.get('element_details', {})
        required_coverage = metrics.get('required_testids_coverage', {})

        analysis = {
            'by_strategy': self._analyze_by_strategy(element_details),
            'by_category': required_coverage,
            'problem_elements': self._identify_problem_elements(element_details),
            'trending_data': self._calculate_trends(element_details)
        }

        return analysis

    def _analyze_by_strategy(self, element_details: Dict[str, Any]) -> Dict[str, Any]:
        """按策略分析"""
        strategy_stats = {
            'data_testid': {'count': 0, 'elements': []},
            'fallback': {'count': 0, 'elements': []},
            'failed': {'count': 0, 'elements': []}
        }

        for element_name, stats in element_details.items():
            strategy_type = stats.get('strategy_type', 'unknown')
            strategy_stats[strategy_type]['count'] += 1
            strategy_stats[strategy_type]['elements'].append(element_name)

        return strategy_stats

    def _identify_problem_elements(self, element_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别问题元素"""
        problems = []

        for element_name, stats in element_details.items():
            element_problems = []

            # 检查高失败率元素
            if stats.get('attempts', 0) > 3 and stats.get('strategy_type') == 'failed':
                element_problems.append('定位频繁失败')

            # 检查总是回退的元素
            if stats.get('attempts', 0) > 1 and stats.get('strategy_type') == 'fallback':
                element_problems.append('总是使用回退策略')

            # 检查匹配数量异常
            match_count = stats.get('match_count', 0)
            if match_count > 1:
                element_problems.append(f'匹配多个元素({match_count}个)')

            if element_problems:
                problems.append({
                    'element_name': element_name,
                    'problems': element_problems,
                    'stats': stats
                })

        return problems

    def _calculate_trends(self, element_details: Dict[str, Any]) -> Dict[str, Any]:
        """计算趋势数据"""
        # 这里可以实现历史数据对比，目前返回基础统计
        total_elements = len(element_details)
        successful_elements = sum(1 for stats in element_details.values()
                               if stats.get('strategy_type') in ['data_testid', 'fallback'])

        return {
            'total_unique_elements': total_elements,
            'successfully_located_elements': successful_elements,
            'unresolved_elements': total_elements - successful_elements,
            'improvement_potential': round((total_elements - successful_elements) / total_elements * 100, 2) if total_elements > 0 else 0
        }

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        hit_rate = metrics.get('data_testid_hit_rate', 0)
        fallback_rate = metrics.get('fallback_rate', 0)
        required_coverage = metrics.get('required_testids_coverage', {})

        # 基于命中率的建议
        if hit_rate < 80:
            recommendations.append("🎯 优先级：立即提高 data-testid 覆盖率")
            recommendations.append("   - 为关键交互元素添加 data-testid")
            recommendations.append("   - 建立 data-testid 添加的 Code Review 检查")
        elif hit_rate < 90:
            recommendations.append("📈 继续优化：进一步提升覆盖率")
            recommendations.append("   - 覆盖剩余的回退元素")
            recommendations.append("   - 定期检查新增功能的数据属性")

        # 基于回退率的建议
        if fallback_rate > 20:
            recommendations.append("⚠️ 风险控制：回退率过高")
            recommendations.append("   - 设置回退率监控告警")
            recommendations.append("   - 分析回退模式找出根本原因")

        # 基于必需元素覆盖率的建议
        critical_paths = ['navigation', 'text_image_flow', 'video_flow']
        for path in critical_paths:
            if path in required_coverage:
                coverage = required_coverage[path].get('coverage_rate', 0)
                if coverage < 100:
                    recommendations.append(f"🔴 关键路径：{path} 覆盖率仅 {coverage}%")
                    recommendations.append(f"   - 必须达到 100% 覆盖率")
                    missing = self._get_missing_testids(path, required_coverage[path])
                    if missing:
                        recommendations.append(f"   - 缺失元素: {', '.join(missing[:3])}")

        # 基于问题元素的建议
        problem_elements = self._identify_problem_elements(metrics.get('element_details', {}))
        if problem_elements:
            recommendations.append("🔍 问题元素：需要特别关注")
            for problem in problem_elements[:3]:  # 只显示前3个
                element_name = problem['element_name']
                issues = ', '.join(problem['problems'])
                recommendations.append(f"   - {element_name}: {issues}")

        return recommendations

    def _get_missing_testids(self, category: str, coverage_data: Dict[str, Any]) -> List[str]:
        """获取缺失的 testid"""
        required = self.required_config.get(category, {}).get('required', [])
        covered = coverage_data.get('covered', 0)

        # 这里简化处理，实际应该根据具体的命中情况判断
        missing_count = len(required) - covered
        return [f"约{missing_count}个元素" for _ in range(min(missing_count, 3))]

    def generate_html_report(self, coverage_report: Dict[str, Any], output_path: str):
        """
        生成 HTML 格式的报告

        Args:
            coverage_report: 覆盖率报告数据
            output_path: 输出文件路径
        """
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data-TestId 覆盖率报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #e0e0e0; padding-bottom: 20px; }
        .grade-{grade} { font-size: 48px; font-weight: bold; margin: 20px 0; }
        .grade-A { color: #52c41a; }
        .grade-B { color: #1890ff; }
        .grade-C { color: #faad14; }
        .grade-D { color: #ff4d4f; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .metric { background: #fafafa; padding: 20px; border-radius: 6px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #1890ff; }
        .metric-label { color: #666; margin-top: 8px; }
        .section { margin: 30px 0; }
        .section h2 { border-left: 4px solid #1890ff; padding-left: 15px; margin-bottom: 20px; }
        .recommendations { background: #fff7e6; border: 1px solid #ffd591; padding: 20px; border-radius: 6px; }
        .recommendations h3 { color: #fa8c16; margin-top: 0; }
        .recommendations ul { margin: 0; padding-left: 20px; }
        .recommendations li { margin: 8px 0; }
        .coverage-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .coverage-item { background: #f0f9ff; border: 1px solid #91d5ff; padding: 15px; border-radius: 6px; }
        .coverage-rate { font-size: 18px; font-weight: bold; color: #1890ff; }
        .coverage-details { color: #666; font-size: 14px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Data-TestId 覆盖率报告</h1>
            <p>生成时间: {generated_at}</p>
            <div class="grade-{grade}">
                等级: {grade} ({description})
            </div>
        </div>

        <div class="section">
            <h2>📊 关键指标</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{hit_rate}%</div>
                    <div class="metric-label">Data-TestId 命中率</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{fallback_rate}%</div>
                    <div class="metric-label">回退率</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{success_rate}%</div>
                    <div class="metric-label">总体成功率</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{total_attempts}</div>
                    <div class="metric-label">总定位尝试</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🎯 关键路径覆盖率</h2>
            <div class="coverage-grid">
                {coverage_items}
            </div>
        </div>

        <div class="section recommendations">
            <h3>🛠️ 改进建议</h3>
            <ul>
                {recommendations}
            </ul>
        </div>
    </div>
</body>
</html>
        """

        # 准备模板数据
        summary = coverage_report['summary']
        coverage_analysis = coverage_report['coverage_analysis']
        recommendations = coverage_report['recommendations']

        # 生成覆盖率项目 HTML
        coverage_items = []
        for category, data in coverage_analysis['by_category'].items():
            coverage_rate = data.get('coverage_rate', 0)
            covered = data.get('covered', 0)
            required = data.get('required', 0)

            color = '#52c41a' if coverage_rate == 100 else '#faad14' if coverage_rate >= 80 else '#ff4d4f'

            coverage_items.append(f"""
                <div class="coverage-item">
                    <div class="coverage-rate" style="color: {color}">{coverage_rate}%</div>
                    <div class="coverage-details">{category} ({covered}/{required})</div>
                </div>
            """)

        # 生成建议列表 HTML
        rec_items = []
        for rec in recommendations:
            rec_items.append(f"<li>{rec}</li>")

        # 填充模板
        #
        # 注意：模板内包含大量 CSS 花括号，直接使用 str.format 会把它们当作占位符导致 KeyError。
        # 这里先整体转义，再把需要的占位符恢复出来。
        template = html_template.replace("{", "{{").replace("}", "}}")
        for key in [
            "generated_at",
            "grade",
            "description",
            "hit_rate",
            "fallback_rate",
            "success_rate",
            "total_attempts",
            "coverage_items",
            "recommendations",
        ]:
            template = template.replace("{{" + key + "}}", "{" + key + "}")

        html_content = template.format(
            generated_at=coverage_report['report_info']['generated_at'],
            grade=summary['quality_grade'],
            description=summary['quality_description'],
            hit_rate=summary['data_testid_hit_rate'],
            fallback_rate=summary['fallback_rate'],
            success_rate=summary['success_rate'],
            total_attempts=summary['total_element_attempts'],
            coverage_items=''.join(coverage_items),
            recommendations=''.join(rec_items)
        )

        # 保存文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📄 HTML 报告已生成: {output_path}")
        except Exception as e:
            print(f"❌ 生成 HTML 报告失败: {e}")

    def save_json_report(self, coverage_report: Dict[str, Any], output_path: str):
        """
        保存 JSON 格式报告

        Args:
            coverage_report: 覆盖率报告数据
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(coverage_report, f, indent=2, ensure_ascii=False)
            print(f"📄 JSON 报告已保存: {output_path}")
        except Exception as e:
            print(f"❌ 保存 JSON 报告失败: {e}")
