"""
计时器工具
用于统计执行时间和性能指标
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class Timer:
    """计时器类"""

    def __init__(self, name: str = "timer"):
        """
        初始化计时器

        Args:
            name: 计时器名称
        """
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_time: Optional[float] = None
        self.checkpoints: Dict[str, float] = {}

    def start(self) -> float:
        """
        开始计时

        Returns:
            float: 开始时间戳
        """
        self.start_time = time.time()
        self.end_time = None
        self.elapsed_time = None
        self.checkpoints.clear()

        self.logger.debug(f"计时器开始: {self.name}")
        return self.start_time

    def stop(self) -> float:
        """
        停止计时

        Returns:
            float: 经过的时间（毫秒）
        """
        if self.start_time is None:
            raise RuntimeError("计时器尚未开始")

        self.end_time = time.time()
        self.elapsed_time = (self.end_time - self.start_time) * 1000

        self.logger.debug(f"计时器停止: {self.name}, 耗时: {self.elapsed_time:.2f}ms")
        return self.elapsed_time

    def checkpoint(self, name: str) -> float:
        """
        添加检查点

        Args:
            name: 检查点名称

        Returns:
            float: 从开始到检查点的时间（毫秒）
        """
        if self.start_time is None:
            raise RuntimeError("计时器尚未开始")

        current_time = time.time()
        checkpoint_time = (current_time - self.start_time) * 1000
        self.checkpoints[name] = checkpoint_time

        self.logger.debug(f"检查点 [{name}]: {checkpoint_time:.2f}ms")
        return checkpoint_time

    def get_elapsed_time(self) -> float:
        """
        获取经过的时间（毫秒）

        Returns:
            float: 经过的时间（毫秒）
        """
        if self.elapsed_time is not None:
            return self.elapsed_time
        elif self.start_time is not None:
            return (time.time() - self.start_time) * 1000
        else:
            return 0.0

    def get_elapsed_time_str(self) -> str:
        """
        获取格式化的时间字符串

        Returns:
            str: 格式化的时间字符串
        """
        elapsed_ms = self.get_elapsed_time()

        if elapsed_ms < 1000:
            return f"{elapsed_ms:.2f}ms"
        elif elapsed_ms < 60000:
            return f"{elapsed_ms / 1000:.2f}s"
        else:
            minutes = int(elapsed_ms // 60000)
            seconds = (elapsed_ms % 60000) / 1000
            return f"{minutes}m {seconds:.2f}s"

    def is_running(self) -> bool:
        """
        检查计时器是否正在运行

        Returns:
            bool: 是否正在运行
        """
        return self.start_time is not None and self.end_time is None

    def reset(self):
        """重置计时器"""
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
        self.checkpoints.clear()

    def get_checkpoints(self) -> Dict[str, float]:
        """
        获取所有检查点

        Returns:
            Dict[str, float]: 检查点字典
        """
        return self.checkpoints.copy()

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        """初始化性能指标收集器"""
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, Any] = {}
        self.timers: Dict[str, Timer] = {}

    def get_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要，提供更友好的格式

        Returns:
            Dict[str, Any]: 格式化的性能摘要
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'timers': {}
        }

        for name, timer in self.timers.items():
            elapsed = timer.get_elapsed_time()
            if elapsed > 0:
                summary['timers'][name] = {
                    'elapsed_time': elapsed,
                    'elapsed_time_str': timer.get_elapsed_time_str(),
                    'checkpoints': timer.get_checkpoints()
                }

        return summary

    def start_timer(self, name: str) -> Timer:
        """
        开始一个计时器

        Args:
            name: 计时器名称

        Returns:
            Timer: 计时器实例
        """
        if name in self.timers and self.timers[name].is_running():
            self.logger.warning(f"计时器 {name} 已在运行，将重置")
            self.timers[name].reset()

        timer = Timer(name)
        timer.start()
        self.timers[name] = timer

        return timer

    def stop_timer(self, name: str) -> Optional[float]:
        """
        停止指定计时器

        Args:
            name: 计时器名称

        Returns:
            Optional[float]: 经过的时间（毫秒）
        """
        if name not in self.timers:
            self.logger.warning(f"计时器 {name} 不存在")
            return None

        return self.timers[name].stop()

    def add_metric(self, name: str, value: Any):
        """
        添加性能指标

        Args:
            name: 指标名称
            value: 指标值
        """
        self.metrics[name] = value

    def get_metric(self, name: str, default: Any = None) -> Any:
        """
        获取性能指标

        Args:
            name: 指标名称
            default: 默认值

        Returns:
            Any: 指标值
        """
        return self.metrics.get(name, default)

    def get_timer_time(self, name: str) -> float:
        """
        获取计时器时间

        Args:
            name: 计时器名称

        Returns:
            float: 经过的时间（毫秒）
        """
        if name not in self.timers:
            return 0.0

        return self.timers[name].get_elapsed_time()

    def get_summary(self) -> Dict[str, Any]:
        """
        获取性能指标摘要

        Returns:
            Dict[str, Any]: 性能指标摘要
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.copy(),
            'timers': {}
        }

        for name, timer in self.timers.items():
            summary['timers'][name] = {
                'elapsed_time': timer.get_elapsed_time(),
                'elapsed_time_str': timer.get_elapsed_time_str(),
                'checkpoints': timer.get_checkpoints()
            }

        return summary

    def reset(self):
        """重置所有指标"""
        self.metrics.clear()
        self.timers.clear()

    def log_summary(self):
        """记录性能指标摘要到日志"""
        summary = self.get_summary()
        self.logger.info("性能指标摘要:")

        # 记录计时器
        for name, timer_data in summary['timers'].items():
            self.logger.info(
                f"  {name}: {timer_data['elapsed_time_str']}"
            )

        # 记录检查点
        for name, timer_data in summary['timers'].items():
            if timer_data['checkpoints']:
                self.logger.info(f"  {name} 检查点:")
                for checkpoint_name, checkpoint_time in timer_data['checkpoints'].items():
                    self.logger.info(f"    {checkpoint_name}: {checkpoint_time:.2f}ms")

        # 记录其他指标
        if summary['metrics']:
            self.logger.info("  其他指标:")
            for metric_name, metric_value in summary['metrics'].items():
                self.logger.info(f"    {metric_name}: {metric_value}")

    def get_all_elapsed(self) -> Dict[str, float]:
        """
        获取所有计时器的耗时

        Returns:
            Dict[str, float]: 计时器名称到耗时的映射
        """
        result = {}
        for name, timer in self.timers.items():
            elapsed = timer.get_elapsed_time()
            if elapsed > 0:
                result[name] = elapsed
        return result


# 全局性能指标实例
performance = PerformanceMetrics()


class ExtendedTimer(Timer):
    """扩展计时器，支持性能监控集成"""

    def __init__(self, name: str, monitor=None):
        """
        初始化扩展计时器

        Args:
            name: 计时器名称
            monitor: 性能监控器实例
        """
        super().__init__(name)
        self.monitor = monitor
        self.quality_score = None

    def set_quality_score(self, score: float):
        """
        设置质量评分

        Args:
            score: 质量评分 (0-1)
        """
        self.quality_score = score

    def stop(self) -> float:
        """
        停止计时并记录到性能监控器

        Returns:
            float: 经过的时间（毫秒）
        """
        elapsed = super().stop()

        # 如果有性能监控器，记录指标
        if self.monitor and hasattr(self.monitor, 'stop_ai_generation_monitoring'):
            self.monitor.stop_ai_generation_monitoring(
                self.name,
                success=True,
                quality_score=self.quality_score
            )

        return elapsed

    def stop_with_error(self, error_message: str) -> float:
        """
        停止计时并记录错误

        Args:
            error_message: 错误消息

        Returns:
            float: 经过的时间（毫秒）
        """
        elapsed = super().stop()

        # 如果有性能监控器，记录错误
        if self.monitor and hasattr(self.monitor, 'stop_ai_generation_monitoring'):
            self.monitor.stop_ai_generation_monitoring(
                self.name,
                success=False,
                error_message=error_message
            )

        return elapsed


def create_monitored_timer(name: str, monitor=None) -> ExtendedTimer:
    """
    创建受监控的计时器

    Args:
        name: 计时器名称
        monitor: 性能监控器实例

    Returns:
        ExtendedTimer: 扩展计时器实例
    """
    return ExtendedTimer(name, monitor)