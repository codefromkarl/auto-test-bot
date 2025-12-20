"""
可视化报告生成器
生成HTML格式的用户旅程看板报告，支持交互式图表和响应式设计
"""

import os
import json
import logging
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
import markdown


class VisualReporter:
    """可视化报告生成器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化可视化报告生成器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 配置路径
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.static_dir = os.path.join(os.path.dirname(__file__), 'static')
        self.output_dir = config.get('output_dir', 'reports/dashboard')

        # 确保目录存在
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )

        # 添加自定义过滤器
        self.jinja_env.filters['format_duration'] = self._format_duration
        self.jinja_env.filters['format_timestamp'] = self._format_timestamp
        self.jinja_env.filters['status_color'] = self._get_status_color
        self.jinja_env.filters['severity_color'] = self._get_severity_color

    def generate_html_report(self, dashboard_data: Dict[str, Any]) -> str:
        """
        生成HTML报告

        Args:
            dashboard_data: 看板数据

        Returns:
            str: 生成的HTML文件路径
        """
        # 生成文件名
        journey_id = dashboard_data.get('journey_info', {}).get('id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = os.path.join(self.output_dir, f"{journey_id}_{timestamp}.html")

        # 渲染HTML模板
        html_content = self._render_template('journey_dashboard.html', dashboard_data)

        # 保存文件
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"📄 HTML报告已生成: {html_filename}")
        return html_filename

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        渲染Jinja2模板

        Args:
            template_name: 模板文件名
            data: 模板数据

        Returns:
            str: 渲染后的内容
        """
        # 如果模板不存在，创建默认模板
        if not os.path.exists(os.path.join(self.template_dir, template_name)):
            self._create_default_template(template_name)

        template = self.jinja_env.get_template(template_name)
        return template.render(**data)

    def _create_default_template(self, template_name: str):
        """
        创建默认模板文件

        Args:
            template_name: 模板名称
        """
        if template_name == 'journey_dashboard.html':
            template_content = self._get_dashboard_template()
        else:
            template_content = self._get_base_template()

        template_path = os.path.join(self.template_dir, template_name)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

    def _get_dashboard_template(self) -> str:
        """获取看板模板内容"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户旅程看板 - {{ journey_info.test_name }}</title>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <!-- Custom CSS -->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .timeline-connector {
            background: linear-gradient(180deg, #e5e7eb 0%, #d1d5db 100%);
        }

        .timeline-dot {
            transition: all 0.3s ease;
        }

        .timeline-dot:hover {
            transform: scale(1.2);
        }

        .screenshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
        }

        .screenshot-item {
            position: relative;
            overflow: hidden;
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }

        .screenshot-item:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }

        .status-badge {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }

        .score-ring {
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
        }

        .issue-marker {
            animation: bounce 1s infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }

        .step-card {
            transition: all 0.3s ease;
        }

        .step-card:hover {
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }

        /* 打印样式 */
        @media print {
            .no-print {
                display: none !important;
            }

            .timeline-connector {
                background: #000 !important;
            }
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200 no-print">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center">
                    <i class="fas fa-route text-2xl text-indigo-600 mr-3"></i>
                    <h1 class="text-xl font-semibold text-gray-900">用户旅程看板</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <button onclick="window.print()" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                        <i class="fas fa-print mr-2"></i>打印报告
                    </button>
                    <button onclick="exportPDF()" class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">
                        <i class="fas fa-file-pdf mr-2"></i>导出PDF
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Journey Info -->
        <section class="bg-white rounded-lg shadow-sm p-6 mb-8">
            <div class="flex justify-between items-start">
                <div>
                    <h2 class="text-2xl font-bold text-gray-900 mb-2">{{ journey_info.test_name }}</h2>
                    <div class="flex items-center space-x-6 text-sm text-gray-600">
                        <span><i class="fas fa-calendar mr-1"></i>{{ journey_info.start_time | format_timestamp }}</span>
                        <span><i class="fas fa-clock mr-1"></i>总耗时: {{ journey_info.total_duration_formatted }}</span>
                        <span><i class="fas fa-hashtag mr-1"></i>ID: {{ journey_info.id }}</span>
                    </div>
                </div>
                {% if experience_score %}
                <div class="text-center">
                    <div class="relative inline-flex items-center justify-center">
                        <svg class="w-32 h-32">
                            <circle cx="64" cy="64" r="56" stroke="#e5e7eb" stroke-width="12" fill="none"></circle>
                            <circle class="score-ring" cx="64" cy="64" r="56" stroke="#10b981" stroke-width="12" fill="none"
                                    stroke-dasharray="{{ experience_score.overall_score * 3.52 }} 352"
                                    stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute">
                            <span class="text-3xl font-bold text-gray-900">{{ "%.0f"|format(experience_score.overall_score) }}</span>
                            <span class="text-sm text-gray-500 block">分</span>
                        </div>
                    </div>
                    <p class="mt-2 text-sm text-gray-600">体验评分</p>
                </div>
                {% endif %}
            </div>
        </section>

        <!-- Statistics Grid -->
        <section class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow-sm p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-tasks text-blue-600"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">总步骤</p>
                        <p class="text-2xl font-semibold text-gray-900">{{ statistics.total_steps }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-check-circle text-green-600"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">成功率</p>
                        <p class="text-2xl font-semibold text-gray-900">{{ "%.1f"|format(statistics.success_rate) }}%</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-exclamation-triangle text-yellow-600"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">问题数</p>
                        <p class="text-2xl font-semibold text-gray-900">{{ statistics.total_issues }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-camera text-purple-600"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">截图数</p>
                        <p class="text-2xl font-semibold text-gray-900">{{ statistics.total_screenshots }}</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Timeline -->
        <section class="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h3 class="text-lg font-semibold text-gray-900 mb-6">
                <i class="fas fa-stream mr-2"></i>执行时间轴
            </h3>
            <div class="relative">
                <div class="absolute left-8 top-0 bottom-0 w-0.5 timeline-connector"></div>
                {% for step in timeline %}
                <div class="relative flex items-start mb-8">
                    <div class="flex-shrink-0">
                        <div class="w-16 h-16 rounded-full bg-{{ step.status | status_color }}-100 flex items-center justify-center timeline-dot">
                            {% if step.status == 'success' %}
                                <i class="fas fa-check text-{{ step.status | status_color }}-600 text-xl"></i>
                            {% elif step.status == 'failed' or step.status == 'blocked' %}
                                <i class="fas fa-times text-{{ step.status | status_color }}-600 text-xl"></i>
                            {% else %}
                                <i class="fas fa-exclamation text-{{ step.status | status_color }}-600 text-xl"></i>
                            {% endif %}
                        </div>
                    </div>
                    <div class="ml-6 flex-1">
                        <div class="step-card bg-{{ step.status | status_color }}-50 rounded-lg p-4 border border-{{ step.status | status_color }}-200">
                            <div class="flex justify-between items-start mb-2">
                                <h4 class="text-base font-semibold text-gray-900">{{ step.step_name }}</h4>
                                <span class="status-badge px-2 py-1 text-xs font-medium bg-{{ step.status | status_color }}-100 text-{{ step.status | status_color }}-800 rounded-full">
                                    {{ step.status }}
                                </span>
                            </div>
                            {% if step.description %}
                            <p class="text-sm text-gray-600 mb-2">{{ step.description }}</p>
                            {% endif %}
                            <div class="flex items-center space-x-4 text-xs text-gray-500">
                                <span><i class="fas fa-clock mr-1"></i>{{ step.duration_formatted }}</span>
                                {% if step.has_screenshots %}
                                <span><i class="fas fa-camera mr-1"></i>有截图</span>
                                {% endif %}
                                {% if step.has_artifacts %}
                                <span><i class="fas fa-file mr-1"></i>有产物</span>
                                {% endif %}
                                {% if step.issues_count > 0 %}
                                <span class="text-red-600"><i class="fas fa-bug mr-1"></i>{{ step.issues_count }}个问题</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>

        <!-- Experience Score Details -->
        {% if experience_score %}
        <section class="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h3 class="text-lg font-semibold text-gray-900 mb-6">
                <i class="fas fa-chart-bar mr-2"></i>体验评分详情
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <canvas id="scoreRadarChart"></canvas>
                </div>
                <div>
                    <canvas id="scoreBarChart"></canvas>
                </div>
            </div>
            <div class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-600 mb-1">可用性</p>
                    <p class="text-xl font-semibold text-gray-900">{{ "%.0f"|format(experience_score.usability_score) }}分</p>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-600 mb-1">性能</p>
                    <p class="text-xl font-semibold text-gray-900">{{ "%.0f"|format(experience_score.performance_score) }}分</p>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-600 mb-1">可靠性</p>
                    <p class="text-xl font-semibold text-gray-900">{{ "%.0f"|format(experience_score.reliability_score) }}分</p>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-600 mb-1">满意度</p>
                    <p class="text-xl font-semibold text-gray-900">{{ "%.0f"|format(experience_score.satisfaction_score) }}分</p>
                </div>
            </div>
        </section>
        {% endif %}

        <!-- Issues Summary -->
        {% if issues_summary.total_issues > 0 %}
        <section class="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h3 class="text-lg font-semibold text-gray-900 mb-6">
                <i class="fas fa-bug mr-2"></i>问题汇总
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h4 class="text-base font-medium text-gray-900 mb-4">严重程度分布</h4>
                    <canvas id="issuesSeverityChart"></canvas>
                </div>
                <div>
                    <h4 class="text-base font-medium text-gray-900 mb-4">关键问题</h4>
                    <div class="space-y-3">
                        {% for issue in issues_summary.critical_issues %}
                        <div class="p-3 bg-{{ issue.severity | severity_color }}-50 border border-{{ issue.severity | severity_color }}-200 rounded-lg">
                            <div class="flex items-start">
                                <i class="fas fa-exclamation-circle text-{{ issue.severity | severity_color }}-600 mt-0.5 mr-2"></i>
                                <div class="flex-1">
                                    <p class="text-sm font-medium text-gray-900">{{ issue.message }}</p>
                                    <p class="text-xs text-gray-500 mt-1">{{ issue.step_name }} - {{ issue.timestamp | format_timestamp }}</p>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </section>
        {% endif %}

        <!-- Screenshots -->
        {% if screenshots %}
        <section class="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h3 class="text-lg font-semibold text-gray-900 mb-6">
                <i class="fas fa-images mr-2"></i>截图预览
            </h3>
            <div class="screenshot-grid">
                {% for screenshot in screenshots %}
                <div class="screenshot-item cursor-pointer" onclick="showScreenshotModal('{{ screenshot.path }}', '{{ screenshot.step_name }}')">
                    <img src="{{ screenshot.path }}" alt="{{ screenshot.step_name }} - 截图{{ screenshot.index + 1 }}"
                         class="w-full h-40 object-cover rounded-lg">
                    <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white p-2 rounded-b-lg">
                        <p class="text-xs truncate">{{ screenshot.step_name }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}

        <!-- Artifacts -->
        {% if artifacts %}
        <section class="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h3 class="text-lg font-semibold text-gray-900 mb-6">
                <i class="fas fa-folder-open mr-2"></i>产物文件
            </h3>
            <div class="space-y-3">
                {% for artifact in artifacts %}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div class="flex items-center">
                        <i class="fas fa-file text-gray-400 mr-3"></i>
                        <div>
                            <p class="text-sm font-medium text-gray-900">{{ artifact.name or artifact.filename }}</p>
                            <p class="text-xs text-gray-500">{{ artifact.step_name }}</p>
                        </div>
                    </div>
                    <a href="{{ artifact.path }}" target="_blank" class="px-3 py-1 text-sm font-medium text-indigo-600 bg-indigo-50 rounded hover:bg-indigo-100">
                        查看
                    </a>
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}
    </main>

    <!-- Screenshot Modal -->
    <div id="screenshotModal" class="fixed inset-0 bg-black bg-opacity-75 z-50 hidden flex items-center justify-center p-4 no-print">
        <div class="relative max-w-4xl w-full">
            <button onclick="closeScreenshotModal()" class="absolute top-4 right-4 text-white text-2xl z-10 hover:text-gray-300">
                <i class="fas fa-times"></i>
            </button>
            <img id="modalImage" src="" alt="" class="w-full h-auto rounded-lg">
            <p id="modalCaption" class="text-white text-center mt-4"></p>
        </div>
    </div>

    <!-- JavaScript -->
    <script>
        // Chart.js 配置
        Chart.defaults.font.family = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

        // 体验评分雷达图
        {% if experience_score %}
        const scoreRadarCtx = document.getElementById('scoreRadarChart').getContext('2d');
        new Chart(scoreRadarCtx, {
            type: 'radar',
            data: {
                labels: ['可用性', '性能', '可靠性', '满意度'],
                datasets: [{
                    label: '体验评分',
                    data: [
                        {{ experience_score.usability_score }},
                        {{ experience_score.performance_score }},
                        {{ experience_score.reliability_score }},
                        {{ experience_score.satisfaction_score }}
                    ],
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(99, 102, 241, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(99, 102, 241, 1)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

        // 体验评分柱状图
        const scoreBarCtx = document.getElementById('scoreBarChart').getContext('2d');
        new Chart(scoreBarCtx, {
            type: 'bar',
            data: {
                labels: ['可用性', '性能', '可靠性', '满意度'],
                datasets: [{
                    label: '评分',
                    data: [
                        {{ experience_score.usability_score }},
                        {{ experience_score.performance_score }},
                        {{ experience_score.reliability_score }},
                        {{ experience_score.satisfaction_score }}
                    ],
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(251, 146, 60, 0.8)',
                        'rgba(168, 85, 247, 0.8)'
                    ],
                    borderWidth: 0,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        {% endif %}

        // 问题严重程度分布图
        {% if issues_summary.total_issues > 0 %}
        const issuesCtx = document.getElementById('issuesSeverityChart').getContext('2d');
        new Chart(issuesCtx, {
            type: 'doughnut',
            data: {
                labels: ['低', '中', '高', '严重'],
                datasets: [{
                    data: [
                        {{ issues_summary.severity_breakdown.low or 0 }},
                        {{ issues_summary.severity_breakdown.medium or 0 }},
                        {{ issues_summary.severity_breakdown.high or 0 }},
                        {{ issues_summary.severity_breakdown.critical or 0 }}
                    ],
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(249, 115, 22, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        {% endif %}

        // 截图模态框功能
        function showScreenshotModal(imagePath, stepName) {
            const modal = document.getElementById('screenshotModal');
            const modalImage = document.getElementById('modalImage');
            const modalCaption = document.getElementById('modalCaption');

            modalImage.src = imagePath;
            modalCaption.textContent = stepName;
            modal.classList.remove('hidden');
        }

        function closeScreenshotModal() {
            const modal = document.getElementById('screenshotModal');
            modal.classList.add('hidden');
        }

        // PDF导出功能
        function exportPDF() {
            // 这里可以使用 jsPDF 或其他库来实现PDF导出
            window.print();
        }

        // ESC键关闭模态框
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeScreenshotModal();
            }
        });

        // 点击模态框背景关闭
        document.getElementById('screenshotModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeScreenshotModal();
            }
        });
    </script>
</body>
</html>
        '''

    def _get_base_template(self) -> str:
        """获取基础模板内容"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div class="container mx-auto p-4">
        {{ content }}
    </div>
</body>
</html>
        '''

    def _format_duration(self, duration_seconds: float) -> str:
        """格式化持续时间"""
        if duration_seconds < 60:
            return f"{duration_seconds:.1f}秒"
        elif duration_seconds < 3600:
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            return f"{minutes}分{seconds}秒"
        else:
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            return f"{hours}小时{minutes}分钟"

    def _format_timestamp(self, timestamp: str) -> str:
        """格式化时间戳"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp

    def _get_status_color(self, status: str) -> str:
        """获取状态颜色"""
        color_map = {
            'success': 'green',
            'failed': 'red',
            'warning': 'yellow',
            'blocked': 'red',
            'running': 'blue',
            'pending': 'gray'
        }
        return color_map.get(status, 'gray')

    def _get_severity_color(self, severity: str) -> str:
        """获取严重程度颜色"""
        color_map = {
            'low': 'green',
            'medium': 'yellow',
            'high': 'orange',
            'critical': 'red'
        }
        return color_map.get(severity, 'gray')

    def generate_embedded_html(self, dashboard_data: Dict[str, Any]) -> str:
        """
        生成嵌入式HTML报告（包含所有内联资源）

        Args:
            dashboard_data: 看板数据

        Returns:
            str: 嵌入式HTML内容
        """
        # 获取模板内容
        template_content = self._get_dashboard_template()
        template = Template(template_content)

        # 注册自定义过滤器
        template.environment.filters['format_duration'] = self._format_duration
        template.environment.filters['format_timestamp'] = self._format_timestamp
        template.environment.filters['status_color'] = self._get_status_color
        template.environment.filters['severity_color'] = self._get_severity_color

        # 渲染模板
        html_content = template.render(**dashboard_data)

        # 内联CSS和JS
        html_content = self._inline_resources(html_content)

        return html_content

    def _inline_resources(self, html: str) -> str:
        """
        将外部资源内联到HTML中

        Args:
            html: HTML内容

        Returns:
            str: 内联后的HTML
        """
        # 这里可以实现CSS和JS的内联
        # 为了简化，暂时返回原始HTML
        return html

    def generate_share_report(self, dashboard_data: Dict[str, Any]) -> str:
        """
        生成可分享的报告链接

        Args:
            dashboard_data: 看板数据

        Returns:
            str: 分享链接
        """
        # 生成嵌入式HTML
        html_content = self.generate_embedded_html(dashboard_data)

        # 对内容进行Base64编码
        encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')

        # 生成分享链接（这里需要根据实际的部署环境调整）
        share_url = f"https://your-domain.com/share?content={encoded_content}"

        return share_url