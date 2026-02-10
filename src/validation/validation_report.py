"""
Validation Report Module
验证报告模块

负责生成和管理验证结果报告
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available. Report thumbnails will be limited.")


@dataclass
class ValidationResult:
    """
    验证结果数据类

    Attributes:
        item_id: 项目ID/名称
        validation_type: 验证类型
        status: 状态 (pending, passed, failed, error, warning)
        score: 评分 (0-100)
        details: 详细信息字典
        timestamp: 时间戳
    """
    item_id: str
    validation_type: str
    status: str = "pending"
    score: float = 0.0
    details: Dict[str, Any] = None
    timestamp: str = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class ValidationReport:
    """
    验证报告类

    负责收集、组织和输出验证结果

    Architecture: Presentation Layer (表现层)
    - 格式化验证结果
    - 生成报告文档
    - 提供可视化输出
    """

    def __init__(self):
        """初始化验证报告"""
        self.logger = logging.getLogger(__name__)
        self.results: Dict[str, List[ValidationResult]] = {}
        self.timestamp = datetime.now().isoformat()
        self.context: Dict[str, Any] = {}
        self.overall_score: float = 0.0
        self.status: str = "pending"

    @property
    def image_results(self) -> List[ValidationResult]:
        return self.results.get("images", [])

    @property
    def video_results(self) -> List[ValidationResult]:
        return self.results.get("videos", [])

    @property
    def consistency_results(self) -> List[ValidationResult]:
        return self.results.get("consistency", [])

    def add_result(self, category: str, result: ValidationResult):
        """
        添加验证结果

        Args:
            category: 结果类别（如 'images', 'videos', 'consistency'）
            result: 验证结果
        """
        if category not in self.results:
            self.results[category] = []
        self.results[category].append(result)
        self.logger.debug(f"Added {result.validation_type} result for {result.item_id} to {category}")

    def add_results(self, category: str, results: List[ValidationResult]):
        """
        批量添加验证结果

        Args:
            category: 结果类别
            results: 验证结果列表
        """
        for result in results:
            self.add_result(category, result)

    def calculate_overall_score(self):
        """计算总体评分"""
        all_scores = []
        all_statuses = []

        for category, results in self.results.items():
            for result in results:
                all_scores.append(result.score)
                all_statuses.append(result.status)

        if all_scores:
            self.overall_score = sum(all_scores) / len(all_scores)

            # 确定总体状态
            if any(s == 'error' for s in all_statuses):
                self.status = 'error'
            elif any(s == 'failed' for s in all_statuses):
                self.status = 'failed'
            elif any(s == 'warning' for s in all_statuses):
                self.status = 'warning'
            elif all(s == 'passed' for s in all_statuses):
                self.status = 'passed'
            else:
                self.status = 'pending'

            self.logger.info(f"Overall validation score: {self.overall_score:.2f}, status: {self.status}")

    def get_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        total_items = sum(len(results) for results in self.results.values())
        passed_items = sum(
            len([r for r in results if r.status == 'passed'])
            for results in self.results.values()
        )
        failed_items = sum(
            len([r for r in results if r.status == 'failed'])
            for results in self.results.values()
        )
        error_items = sum(
            len([r for r in results if r.status == 'error'])
            for results in self.results.values()
        )
        summary = {
            'timestamp': self.timestamp,
            'overall_score': self.overall_score,
            'status': self.status,
            'total_items': total_items,
            'passed_items': passed_items,
            'failed_items': failed_items,
            'error_items': error_items,
            'categories': {}
        }

        for category, results in self.results.items():
            category_summary = {
                'count': len(results),
                'avg_score': sum(r.score for r in results) / len(results) if results else 0,
                'passed': len([r for r in results if r.status == 'passed']),
                'failed': len([r for r in results if r.status == 'failed']),
                'error': len([r for r in results if r.status == 'error']),
                'warning': len([r for r in results if r.status == 'warning'])
            }
            summary['categories'][category] = category_summary

        return summary

    def get_key_issues(self) -> List[Dict[str, Any]]:
        """获取关键问题列表"""
        issues = []

        for category, results in self.results.items():
            for result in results:
                if result.status in ['failed', 'error']:
                    issue = {
                        'category': category,
                        'item_id': result.item_id,
                        'type': result.validation_type,
                        'status': result.status,
                        'score': result.score,
                        'reason': result.details.get('reason', 'No reason provided'),
                        'error': result.details.get('error', 'No error details')
                    }
                    issues.append(issue)

        # 按评分排序（最严重的在前）
        issues.sort(key=lambda x: x['score'])
        return issues[:10]  # 返回前10个问题

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp,
            'context': self.context,
            'overall_score': self.overall_score,
            'status': self.status,
            'summary': self.get_summary(),
            'results': {
                category: [r.to_dict() for r in results]
                for category, results in self.results.items()
            },
            'key_issues': self.get_key_issues()
        }

    def save_json(self, file_path: str):
        """
        保存为JSON格式

        Args:
            file_path: 输出文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            self.logger.info(f"Validation report saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving JSON report: {str(e)}")

    def save_html(self, file_path: str):
        """
        保存为HTML格式

        Args:
            file_path: 输出文件路径
        """
        try:
            html_content = self.to_html()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"HTML report saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving HTML report: {str(e)}")

    def to_json(self) -> str:
        """返回 JSON 字符串（兼容旧测试接口）"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_html(self) -> str:
        """返回 HTML 字符串（兼容旧测试接口）"""
        summary = self.get_summary()
        categories = []
        for category, info in summary.get("categories", {}).items():
            categories.append(
                f"<li>{category}: count={info.get('count', 0)}, avg={info.get('avg_score', 0):.1f}, "
                f"passed={info.get('passed', 0)}, failed={info.get('failed', 0)}, error={info.get('error', 0)}</li>"
            )
        categories_html = "".join(categories) or "<li>no categories</li>"
        return (
            "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Validation Report</title></head>"
            "<body>"
            f"<h1>Validation Report</h1>"
            f"<p>timestamp: {self.timestamp}</p>"
            f"<p>overall_score: {self.overall_score:.2f}</p>"
            f"<p>status: {self.status}</p>"
            f"<p>total_items: {summary.get('total_items', 0)}</p>"
            f"<p>passed_items: {summary.get('passed_items', 0)}</p>"
            f"<ul>{categories_html}</ul>"
            "</body></html>"
        )

    def _generate_html(self) -> str:
        """生成HTML报告内容"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>内容验证报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #666;
        }
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        .status-passed { color: #4CAF50; }
        .status-failed { color: #f44336; }
        .status-error { color: #ff9800; }
        .status-warning { color: #ff9800; }
        .section {
            margin: 30px 0;
        }
        .section h2 {
            color: #333;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
        }
        .progress-good { background-color: #4CAF50; }
        .progress-warning { background-color: #ff9800; }
        .progress-bad { background-color: #f44336; }
        .issue-card {
            background: #fff3cd;
            border: 1px solid #ffeeba;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .details-toggle {
            cursor: pointer;
            color: #007bff;
            user-select: none;
        }
        .details-content {
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>内容验证报告</h1>
        <p>生成时间: {timestamp}</p>

        <div class="summary">
            <div class="summary-card">
                <h3>总体评分</h3>
                <div class="value status-{status_class}">{overall_score:.1f}</div>
            </div>
            <div class="summary-card">
                <h3>验证状态</h3>
                <div class="value status-{status_class}">{status}</div>
            </div>
            <div class="summary-card">
                <h3>验证项目</h3>
                <div class="value">{total_items}</div>
            </div>
            <div class="summary-card">
                <h3>通过率</h3>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
        </div>

        {categories_html}

        <div class="section">
            <h2>关键问题</h2>
            {issues_html}
        </div>
    </div>

    <script>
        function toggleDetails(element) {
            const content = element.nextElementSibling;
            content.style.display = content.style.display === 'block' ? 'none' : 'block';
        }
    </script>
</body>
</html>
        """

        # 生成类别HTML
        categories_html = ""
        for category, results in self.results.items():
            categories_html += f"""
            <div class="section">
                <h2>{category}</h2>
                <table>
                    <tr>
                        <th>项目</th>
                        <th>类型</th>
                        <th>状态</th>
                        <th>评分</th>
                        <th>详情</th>
                    </tr>
            """

            for result in results:
                status_class = result.status.lower()
                progress_class = "progress-good" if result.score >= 80 else "progress-warning" if result.score >= 60 else "progress-bad"

                categories_html += f"""
                    <tr>
                        <td>{result.item_id}</td>
                        <td>{result.validation_type}</td>
                        <td class="status-{status_class}">{result.status}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill {progress_class}" style="width: {result.score}%"></div>
                            </div>
                            {result.score:.1f}
                        </td>
                        <td>
                            <span class="details-toggle" onclick="toggleDetails(this)">查看详情</span>
                            <div class="details-content">
                                <pre>{json.dumps(result.details, ensure_ascii=False, indent=2)}</pre>
                            </div>
                        </td>
                    </tr>
                """

            categories_html += "</table></div>"

        # 生成问题HTML
        issues_html = ""
        key_issues = self.get_key_issues()
        if key_issues:
            for issue in key_issues:
                issues_html += f"""
                <div class="issue-card">
                    <strong>{issue['category']} - {issue['item_id']}</strong>
                    <br>Type: {issue['type']}, Score: {issue['score']:.1f}
                    <br>Reason: {issue['reason']}
                    {f"<br>Error: {issue['error']}" if issue['error'] else ""}
                </div>
                """
        else:
            issues_html = "<p>没有发现关键问题</p>"

        # 计算统计信息
        total_items = sum(len(results) for results in self.results.values())
        passed_items = sum(
            len([r for r in results if r.status == 'passed'])
            for results in self.results.values()
        )
        pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0

        return html_template.format(
            timestamp=self.timestamp,
            overall_score=self.overall_score,
            status=self.status,
            status_class=self.status.lower(),
            total_items=total_items,
            pass_rate=pass_rate,
            categories_html=categories_html,
            issues_html=issues_html
        )

    def print_summary(self):
        """打印验证摘要到控制台"""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("内容验证报告摘要")
        print("="*60)
        print(f"时间: {self.timestamp}")
        print(f"总体评分: {self.overall_score:.2f}")
        print(f"状态: {self.status.upper()}")
        print("-"*60)

        for category, info in summary['categories'].items():
            print(f"\n{category}:")
            print(f"  项目数: {info['count']}")
            print(f"  平均分: {info['avg_score']:.2f}")
            print(f"  通过: {info['passed']}")
            print(f"  失败: {info['failed']}")
            print(f"  错误: {info['error']}")

        # 显示关键问题
        issues = self.get_key_issues()
        if issues:
            print("\n关键问题:")
            print("-"*60)
            for i, issue in enumerate(issues[:5], 1):
                print(f"{i}. [{issue['category']}] {issue['item_id']} - {issue['status']}")
                print(f"   {issue['reason']}")

        print("="*60 + "\n")
