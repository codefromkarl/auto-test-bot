"""
性能监控模块

为闹海测试系统提供全面的性能监控功能，包括：
- AI生成各阶段的耗时监控
- 性能阈值告警
- 性能报告生成
- 资源使用监控
"""

import time
import psutil
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.timer import Timer, performance


@dataclass
class PerformanceThreshold:
    """性能阈值配置"""
    name: str
    max_duration_ms: float
    warning_threshold: float = 0.8  # 80%时发出警告
    critical_threshold: float = 1.0  # 100%时发出严重警告


@dataclass
class AIGenerationMetrics:
    """AI生成指标"""
    phase: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    resource_usage: Optional[Dict[str, float]] = None


@dataclass
class SystemResourceMetrics:
    """系统资源指标"""
    cpu_percent: float
    memory_percent: float
    memory_usage_mb: float
    disk_usage_percent: float
    network_io: Optional[Dict[str, int]] = None
    timestamp: float = None


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化性能监控器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics: List[AIGenerationMetrics] = []
        self.system_metrics: List[SystemResourceMetrics] = []
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.active_timers: Dict[str, Timer] = {}

        # 初始化性能阈值
        self._init_thresholds()

        # 系统监控间隔（秒）
        self.system_monitor_interval = 5
        self._system_monitor_active = False

    def _init_thresholds(self):
        """初始化性能阈值"""
        perf_config = self.config.get('performance_monitoring', {})
        thresholds_config = perf_config.get('thresholds', {})

        # AI生成阶段阈值
        ai_thresholds = {
            'script_analysis': PerformanceThreshold(
                'script_analysis',
                thresholds_config.get('script_analysis', 30) * 1000
            ),
            'image_generation': PerformanceThreshold(
                'image_generation',
                thresholds_config.get('image_generation', 120) * 1000
            ),
            'video_generation': PerformanceThreshold(
                'video_generation',
                thresholds_config.get('video_generation', 300) * 1000
            ),
        }

        self.thresholds.update(ai_thresholds)

    def start_ai_generation_monitoring(self, phase: str) -> str:
        """
        开始AI生成阶段监控

        Args:
            phase: 生成阶段名称

        Returns:
            str: 监控ID
        """
        monitor_id = f"{phase}_{int(time.time())}"

        timer = Timer(monitor_id)
        timer.start()
        self.active_timers[monitor_id] = timer

        metrics = AIGenerationMetrics(
            phase=phase,
            start_time=time.time()
        )
        self.metrics.append(metrics)

        self.logger.info(f"开始性能监控: {phase} (ID: {monitor_id})")
        return monitor_id

    def stop_ai_generation_monitoring(
        self,
        monitor_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        quality_score: Optional[float] = None
    ) -> Optional[AIGenerationMetrics]:
        """
        停止AI生成阶段监控

        Args:
            monitor_id: 监控ID
            success: 是否成功
            error_message: 错误消息
            quality_score: 质量评分

        Returns:
            Optional[AIGenerationMetrics]: 生成的指标
        """
        if monitor_id not in self.active_timers:
            self.logger.warning(f"监控ID不存在: {monitor_id}")
            return None

        timer = self.active_timers[monitor_id]
        duration_ms = timer.stop()

        # 更新对应的指标
        for metrics in reversed(self.metrics):
            if metrics.start_time == timer.start_time:
                metrics.end_time = time.time()
                metrics.duration_ms = duration_ms
                metrics.success = success
                metrics.error_message = error_message
                metrics.quality_score = quality_score
                metrics.resource_usage = self._get_current_resource_usage()
                break

        # 性能阈值检查
        self._check_threshold(timer, monitor_id)

        del self.active_timers[monitor_id]

        self.logger.info(f"停止性能监控: {monitor_id}, 耗时: {duration_ms:.2f}ms")
        return metrics

    def _get_current_resource_usage(self) -> Dict[str, float]:
        """获取当前资源使用情况"""
        try:
            process = psutil.Process()
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
            }
        except Exception as e:
            self.logger.warning(f"获取资源使用情况失败: {e}")
            return {}

    def _check_threshold(self, timer: Timer, monitor_id: str):
        """检查性能阈值"""
        duration_ms = timer.get_elapsed_time()

        # 从监控ID中提取阶段名称
        phase = monitor_id.split('_')[0]

        if phase in self.thresholds:
            threshold = self.thresholds[phase]
            ratio = duration_ms / threshold.max_duration_ms

            if ratio >= threshold.critical_threshold:
                self.logger.error(
                    f"🚨 性能严重警告: {phase} 耗时 {duration_ms:.2f}ms "
                    f"(阈值: {threshold.max_duration_ms:.2f}ms)"
                )
            elif ratio >= threshold.warning_threshold:
                self.logger.warning(
                    f"⚠️ 性能警告: {phase} 耗时 {duration_ms:.2f}ms "
                    f"(阈值: {threshold.max_duration_ms:.2f}ms)"
                )

    def start_system_monitoring(self):
        """开始系统资源监控"""
        if self._system_monitor_active:
            return

        self._system_monitor_active = True
        self.logger.info("开始系统资源监控")

    def stop_system_monitoring(self):
        """停止系统资源监控"""
        self._system_monitor_active = False
        self.logger.info("停止系统资源监控")

    def collect_system_metrics(self):
        """收集系统资源指标"""
        if not self._system_monitor_active:
            return

        try:
            # CPU和内存
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # 磁盘使用
            disk = psutil.disk_usage('/')

            # 网络IO
            network = psutil.net_io_counters()

            metrics = SystemResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_usage_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                } if network else None,
                timestamp=time.time()
            )

            self.system_metrics.append(metrics)

            # 限制历史记录数量
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-500:]

        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")

    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(),
            'ai_generation_metrics': [asdict(m) for m in self.metrics],
            'system_metrics': [asdict(m) for m in self.system_metrics],
            'threshold_violations': self._get_threshold_violations(),
            'recommendations': self._generate_recommendations()
        }

        return report

    def _generate_summary(self) -> Dict[str, Any]:
        """生成性能摘要"""
        if not self.metrics:
            return {}

        successful_metrics = [m for m in self.metrics if m.success]
        failed_metrics = [m for m in self.metrics if not m.success]

        # 按阶段分组统计
        phase_stats = {}
        for metrics in self.metrics:
            phase = metrics.phase
            if phase not in phase_stats:
                phase_stats[phase] = {
                    'count': 0,
                    'success_count': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'min_duration': float('inf'),
                    'max_duration': 0
                }

            stats = phase_stats[phase]
            stats['count'] += 1

            if metrics.success:
                stats['success_count'] += 1

            if metrics.duration_ms:
                stats['total_duration'] += metrics.duration_ms
                stats['min_duration'] = min(stats['min_duration'], metrics.duration_ms)
                stats['max_duration'] = max(stats['max_duration'], metrics.duration_ms)

        # 计算平均值
        for stats in phase_stats.values():
            if stats['count'] > 0:
                stats['avg_duration'] = stats['total_duration'] / stats['count']
                stats['success_rate'] = stats['success_count'] / stats['count']

        return {
            'total_tests': len(self.metrics),
            'successful_tests': len(successful_metrics),
            'failed_tests': len(failed_metrics),
            'success_rate': len(successful_metrics) / len(self.metrics) if self.metrics else 0,
            'phase_statistics': phase_stats
        }

    def _get_threshold_violations(self) -> List[Dict[str, Any]]:
        """获取阈值违规列表"""
        violations = []

        for metrics in self.metrics:
            if metrics.duration_ms and metrics.phase in self.thresholds:
                threshold = self.thresholds[metrics.phase]
                if metrics.duration_ms > threshold.max_duration_ms:
                    violations.append({
                        'phase': metrics.phase,
                        'duration_ms': metrics.duration_ms,
                        'threshold_ms': threshold.max_duration_ms,
                        'violation_ratio': metrics.duration_ms / threshold.max_duration_ms,
                        'timestamp': metrics.start_time
                    })

        return violations

    def _generate_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []

        # 分析慢速阶段
        slow_phases = {}
        for metrics in self.metrics:
            if metrics.duration_ms and metrics.phase in self.thresholds:
                threshold = self.thresholds[metrics.phase]
                ratio = metrics.duration_ms / threshold.max_duration_ms

                if ratio > 0.7:  # 超过70%阈值
                    if metrics.phase not in slow_phases:
                        slow_phases[metrics.phase] = []
                    slow_phases[metrics.phase].append(ratio)

        # 生成建议
        for phase, ratios in slow_phases.items():
            avg_ratio = sum(ratios) / len(ratios)
            if avg_ratio > 1.0:
                recommendations.append(
                    f"{phase} 阶段性能严重超标（平均超标 {avg_ratio-1:.1%}），"
                    "建议优化算法或增加超时时间"
                )
            elif avg_ratio > 0.8:
                recommendations.append(
                    f"{phase} 阶段接近性能上限（平均使用率 {avg_ratio:.1%}），"
                    "建议关注性能波动"
                )

        # 系统资源建议
        if self.system_metrics:
            avg_cpu = sum(m.cpu_percent for m in self.system_metrics) / len(self.system_metrics)
            avg_memory = sum(m.memory_percent for m in self.system_metrics) / len(self.system_metrics)

            if avg_cpu > 80:
                recommendations.append("系统CPU使用率过高，建议优化计算密集型操作")
            if avg_memory > 85:
                recommendations.append("系统内存使用率过高，建议优化内存管理")

        if not recommendations:
            recommendations.append("性能表现良好，无特别建议")

        return recommendations

    def save_report(self, output_path: str):
        """保存性能报告到文件"""
        report = self.generate_performance_report()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"性能报告已保存到: {output_path}")

    def reset(self):
        """重置监控数据"""
        self.metrics.clear()
        self.system_metrics.clear()
        self.active_timers.clear()
        self._system_monitor_active = False
        self.logger.info("性能监控数据已重置")


# 全局性能监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(config: Dict[str, Any]) -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(config)
    return _global_monitor


def reset_performance_monitor():
    """重置全局性能监控器"""
    global _global_monitor
    _global_monitor = None