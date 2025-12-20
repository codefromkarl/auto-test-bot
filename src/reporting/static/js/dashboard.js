/**
 * 用户旅程看板交互脚本
 * 处理图表渲染、模态框、导出等功能
 */

// 全局变量
let dashboardData = null;
let charts = {};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    initializeCharts();
    setupKeyboardShortcuts();
});

/**
 * 初始化看板
 */
function initializeDashboard() {
    // 从data属性或全局变量加载数据
    const dataElement = document.getElementById('dashboard-data');
    if (dataElement) {
        dashboardData = JSON.parse(dataElement.textContent);
    }

    // 初始化工具提示
    initializeTooltips();

    // 添加加载动画
    document.querySelectorAll('.timeline-item, .score-card, .screenshot-item').forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        setTimeout(() => {
            el.style.transition = 'all 0.5s ease-out';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 截图点击事件
    document.querySelectorAll('.screenshot-item').forEach(item => {
        item.addEventListener('click', function() {
            const imgPath = this.dataset.imgPath;
            const title = this.dataset.title;
            showScreenshotModal(imgPath, title);
        });
    });

    // 模态框关闭事件
    const modal = document.getElementById('screenshot-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeScreenshotModal();
            }
        });
    }

    // 打印按钮
    const printBtn = document.getElementById('print-btn');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // PDF导出按钮
    const pdfBtn = document.getElementById('pdf-btn');
    if (pdfBtn) {
        pdfBtn.addEventListener('click', exportToPDF);
    }

    // 分享按钮
    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', shareReport);
    }

    // 展开/折叠详情
    document.querySelectorAll('.toggle-details').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const target = document.getElementById(targetId);
            if (target) {
                target.classList.toggle('expanded');
                this.textContent = target.classList.contains('expanded') ? '收起' : '展开';
            }
        });
    });
}

/**
 * 初始化图表
 */
function initializeCharts() {
    // 体验评分雷达图
    const radarCanvas = document.getElementById('score-radar-chart');
    if (radarCanvas && dashboardData && dashboardData.experience_score) {
        charts.radar = createRadarChart(radarCanvas, dashboardData.experience_score);
    }

    // 体验评分柱状图
    const barCanvas = document.getElementById('score-bar-chart');
    if (barCanvas && dashboardData && dashboardData.experience_score) {
        charts.bar = createBarChart(barCanvas, dashboardData.experience_score);
    }

    // 问题分布图
    const issueCanvas = document.getElementById('issue-chart');
    if (issueCanvas && dashboardData && dashboardData.issues_summary) {
        charts.issues = createDoughnutChart(issueCanvas, dashboardData.issues_summary);
    }

    // 时间轴进度图
    const timelineCanvas = document.getElementById('timeline-chart');
    if (timelineCanvas && dashboardData && dashboardData.timeline) {
        charts.timeline = createTimelineChart(timelineCanvas, dashboardData.timeline);
    }
}

/**
 * 创建雷达图
 */
function createRadarChart(canvas, scoreData) {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['可用性', '性能', '可靠性', '满意度'],
            datasets: [{
                label: '体验评分',
                data: [
                    scoreData.usability_score,
                    scoreData.performance_score,
                    scoreData.reliability_score,
                    scoreData.satisfaction_score
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
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    pointLabels: {
                        font: {
                            size: 14,
                            weight: '500'
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed.r.toFixed(1) + '分';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 创建柱状图
 */
function createBarChart(canvas, scoreData) {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['可用性', '性能', '可靠性', '满意度'],
            datasets: [{
                label: '评分',
                data: [
                    scoreData.usability_score,
                    scoreData.performance_score,
                    scoreData.reliability_score,
                    scoreData.satisfaction_score
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
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '分';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toFixed(1) + '分';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 创建环形图
 */
function createDoughnutChart(canvas, issueSummary) {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['低', '中', '高', '严重'],
            datasets: [{
                data: [
                    issueSummary.severity_breakdown.low || 0,
                    issueSummary.severity_breakdown.medium || 0,
                    issueSummary.severity_breakdown.high || 0,
                    issueSummary.severity_breakdown.critical || 0
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
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return label + ': ' + value + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 创建时间轴图表
 */
function createTimelineChart(canvas, timelineData) {
    const ctx = canvas.getContext('2d');
    const labels = timelineData.map(item => item.step_name);
    const durations = timelineData.map(item => item.duration);

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '执行时间',
                data: durations,
                backgroundColor: labels.map((_, index) => {
                    const status = timelineData[index].status;
                    switch (status) {
                        case 'success': return 'rgba(34, 197, 94, 0.8)';
                        case 'failed': return 'rgba(239, 68, 68, 0.8)';
                        case 'warning': return 'rgba(251, 191, 36, 0.8)';
                        default: return 'rgba(156, 163, 175, 0.8)';
                    }
                }),
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '时间 (秒)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatDuration(value);
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const duration = context.parsed.x;
                            return '耗时: ' + formatDuration(duration);
                        }
                    }
                }
            }
        }
    });
}

/**
 * 显示截图模态框
 */
function showScreenshotModal(imagePath, title) {
    const modal = document.getElementById('screenshot-modal');
    const modalImage = document.getElementById('modal-image');
    const modalCaption = document.getElementById('modal-caption');
    const modalLoader = document.getElementById('modal-loader');

    if (modal && modalImage) {
        // 显示加载状态
        modalLoader.style.display = 'block';
        modalImage.style.display = 'none';

        // 加载图片
        const img = new Image();
        img.onload = function() {
            modalImage.src = imagePath;
            modalImage.style.display = 'block';
            modalLoader.style.display = 'none';
        };
        img.onerror = function() {
            modalLoader.textContent = '图片加载失败';
        };
        img.src = imagePath;

        // 设置标题
        if (modalCaption) {
            modalCaption.textContent = title;
        }

        // 显示模态框
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * 关闭截图模态框
 */
function closeScreenshotModal() {
    const modal = document.getElementById('screenshot-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * 导出为PDF
 */
function exportToPDF() {
    const btn = document.getElementById('pdf-btn');
    const originalText = btn.textContent;

    btn.textContent = '生成中...';
    btn.disabled = true;

    // 这里可以使用第三方库如jsPDF或html2canvas
    // 简单起见，使用浏览器的打印功能
    setTimeout(() => {
        window.print();
        btn.textContent = originalText;
        btn.disabled = false;
    }, 1000);
}

/**
 * 分享报告
 */
function shareReport() {
    const shareUrl = window.location.href;

    if (navigator.share) {
        navigator.share({
            title: '用户旅程看板报告',
            text: '查看测试执行结果',
            url: shareUrl
        }).catch(err => {
            console.log('分享失败:', err);
            copyToClipboard(shareUrl);
        });
    } else {
        copyToClipboard(shareUrl);
    }
}

/**
 * 复制到剪贴板
 */
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();

    try {
        document.execCommand('copy');
        showToast('链接已复制到剪贴板');
    } catch (err) {
        showToast('复制失败，请手动复制链接', 'error');
    }

    document.body.removeChild(textarea);
}

/**
 * 显示提示消息
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: ${type === 'success' ? 'var(--success-color)' : 'var(--error-color)'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

/**
 * 初始化工具提示
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.dataset.tooltip;
            tooltip.style.cssText = `
                position: absolute;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: 0.25rem;
                font-size: 0.875rem;
                z-index: 1000;
                pointer-events: none;
                white-space: nowrap;
            `;

            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        });

        element.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) {
                document.body.removeChild(tooltip);
            }
        });
    });
}

/**
 * 设置键盘快捷键
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // ESC关闭模态框
        if (e.key === 'Escape') {
            closeScreenshotModal();
        }

        // Ctrl/Cmd + P 打印
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            window.print();
        }

        // Ctrl/Cmd + S 保存/导出
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            exportToPDF();
        }
    });
}

/**
 * 格式化持续时间
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return seconds.toFixed(1) + '秒';
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}分${remainingSeconds}秒`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const remainingMinutes = Math.floor((seconds % 3600) / 60);
        return `${hours}小时${remainingMinutes}分`;
    }
}

/**
 * 下载报告数据
 */
function downloadReportData() {
    if (!dashboardData) return;

    const dataStr = JSON.stringify(dashboardData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

    const exportFileDefaultName = `dashboard-report-${Date.now()}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .toast {
        animation: slideInRight 0.3s ease-out;
    }
`;
document.head.appendChild(style);

// 导出全局函数供HTML调用
window.dashboardUtils = {
    showScreenshotModal,
    closeScreenshotModal,
    exportToPDF,
    shareReport,
    downloadReportData,
    formatDuration
};