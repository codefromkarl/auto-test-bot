"""
网络模拟器和错误处理器 - 提供网络条件模拟和异常处理功能
"""

import time
import random
import asyncio
import socket
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from contextlib import contextmanager


class NetworkCondition(Enum):
    """网络条件枚举"""

    NORMAL = "normal"
    SLOW_3G = "slow_3g"
    FAST_3G = "fast_3g"
    SLOW_4G = "slow_4g"
    FAST_4G = "fast_4g"
    OFFLINE = "offline"
    UNSTABLE = "unstable"
    PACKET_LOSS = "packet_loss"


class ErrorType(Enum):
    """错误类型枚举"""

    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class NetworkProfile:
    """网络配置文件"""

    name: str
    download_throughput: float  # Kbps
    upload_throughput: float  # Kbps
    latency: int  # ms
    packet_loss_rate: float  # 0.0-1.0
    jitter: int  # ms


@dataclass
class ErrorScenario:
    """错误场景配置"""

    name: str
    error_type: ErrorType
    trigger_conditions: Dict[str, Any]
    duration: Optional[int] = None
    retry_after: Optional[int] = None
    recovery_actions: List[str] = field(default_factory=list)


# 预定义网络配置
NETWORK_PROFILES = {
    NetworkCondition.NORMAL: NetworkProfile(
        name="Normal",
        download_throughput=10000,  # 10 Mbps
        upload_throughput=5000,  # 5 Mbps
        latency=50,
        packet_loss_rate=0.0,
        jitter=10,
    ),
    NetworkCondition.SLOW_3G: NetworkProfile(
        name="Slow 3G",
        download_throughput=500,  # 500 Kbps
        upload_throughput=500,  # 500 Kbps
        latency=400,
        packet_loss_rate=0.01,
        jitter=200,
    ),
    NetworkCondition.FAST_3G: NetworkProfile(
        name="Fast 3G",
        download_throughput=1600,  # 1.6 Mbps
        upload_throughput=750,  # 750 Kbps
        latency=300,
        packet_loss_rate=0.005,
        jitter=100,
    ),
    NetworkCondition.SLOW_4G: NetworkProfile(
        name="Slow 4G",
        download_throughput=4000,  # 4 Mbps
        upload_throughput=3000,  # 3 Mbps
        latency=150,
        packet_loss_rate=0.002,
        jitter=50,
    ),
    NetworkCondition.FAST_4G: NetworkProfile(
        name="Fast 4G",
        download_throughput=10000,  # 10 Mbps
        upload_throughput=5000,  # 5 Mbps
        latency=50,
        packet_loss_rate=0.001,
        jitter=20,
    ),
    NetworkCondition.OFFLINE: NetworkProfile(
        name="Offline",
        download_throughput=0,
        upload_throughput=0,
        latency=0,
        packet_loss_rate=1.0,
        jitter=0,
    ),
    NetworkCondition.UNSTABLE: NetworkProfile(
        name="Unstable",
        download_throughput=2000,  # 2 Mbps (variable)
        upload_throughput=1000,  # 1 Mbps (variable)
        latency=200,  # (variable)
        packet_loss_rate=0.05,
        jitter=150,
    ),
    NetworkCondition.PACKET_LOSS: NetworkProfile(
        name="Packet Loss",
        download_throughput=8000,  # 8 Mbps
        upload_throughput=4000,  # 4 Mbps
        latency=100,
        packet_loss_rate=0.15,
        jitter=80,
    ),
}


class NetworkSimulator:
    """网络模拟器"""

    def __init__(self):
        self.current_profile = NETWORK_PROFILES[NetworkCondition.NORMAL]
        self.simulation_active = False
        self.request_count = 0
        self.error_count = 0
        self.latency_history: List[int] = []
        self.throughput_history: List[float] = []
        self.packet_loss_history: List[bool] = []

        # 自定义错误场景
        self.error_scenarios: List[ErrorScenario] = []
        self.active_scenario: Optional[ErrorScenario] = None

        # 监控回调
        self.monitoring_callbacks: List[Callable] = []

        self.logger = logging.getLogger(__name__)

    def set_network_condition(self, condition: NetworkCondition) -> None:
        """设置网络条件"""
        self.current_profile = NETWORK_PROFILES[condition]
        self.logger.info(f"Network condition set to: {condition.value}")
        self._notify_monitors(
            "network_condition_changed",
            {"condition": condition, "profile": self.current_profile},
        )

    def add_error_scenario(self, scenario: ErrorScenario) -> None:
        """添加错误场景"""
        self.error_scenarios.append(scenario)
        self.logger.info(f"Added error scenario: {scenario.name}")

    def check_error_trigger(self, request_info: Dict[str, Any]) -> bool:
        """检查是否触发错误场景"""
        for scenario in self.error_scenarios:
            if self._should_trigger_scenario(scenario, request_info):
                self.active_scenario = scenario
                self.logger.warning(f"Error scenario triggered: {scenario.name}")
                return True
        return False

    def _should_trigger_scenario(
        self, scenario: ErrorScenario, request_info: Dict[str, Any]
    ) -> bool:
        """判断是否应该触发错误场景"""
        conditions = scenario.trigger_conditions

        # 检查请求次数触发
        if "request_count" in conditions:
            if self.request_count >= conditions["request_count"]:
                return True

        # 检查随机概率触发
        if "probability" in conditions:
            if random.random() < conditions["probability"]:
                return True

        # 检查特定URL触发
        if "url_pattern" in conditions:
            url = request_info.get("url", "")
            if conditions["url_pattern"] in url:
                return True

        # 检查时间间隔触发
        if "time_interval" in conditions:
            interval = conditions["time_interval"]
            if self.request_count % interval == 0:
                return True

        return False

    def simulate_request(self, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """模拟网络请求"""
        self.request_count += 1
        start_time = time.time()

        # 检查错误场景触发
        if self.check_error_trigger(request_info):
            return self._generate_error_response()

        # 模拟网络延迟
        latency = self._calculate_latency()
        time.sleep(latency / 1000.0)  # 转换为秒

        # 模拟丢包
        if self._should_drop_packet():
            self.error_count += 1
            self.packet_loss_history.append(True)
            return self._generate_packet_loss_response()

        # 模拟正常响应
        response_time = (time.time() - start_time) * 1000
        throughput = self._calculate_throughput()

        # 记录历史数据
        self.latency_history.append(latency)
        self.throughput_history.append(throughput)
        self.packet_loss_history.append(False)

        response = {
            "success": True,
            "response_time": response_time,
            "throughput": throughput,
            "latency": latency,
            "packet_loss": False,
            "request_info": request_info,
        }

        self._notify_monitors("request_completed", response)
        return response

    def _calculate_latency(self) -> int:
        """计算网络延迟"""
        base_latency = self.current_profile.latency
        jitter = self.current_profile.jitter

        if self.current_profile.name == "Unstable":
            # 不稳定网络：延迟变化更大
            jitter_variation = random.uniform(0, jitter * 3)
        else:
            jitter_variation = random.uniform(-jitter, jitter)

        return max(0, int(base_latency + jitter_variation))

    def _calculate_throughput(self) -> float:
        """计算吞吐量"""
        if self.current_profile.name == "Unstable":
            # 不稳定网络：吞吐量变化较大
            base_throughput = self.current_profile.download_throughput
            variation = random.uniform(-base_throughput * 0.5, base_throughput * 0.5)
            return max(0, base_throughput + variation)
        else:
            return self.current_profile.download_throughput

    def _should_drop_packet(self) -> bool:
        """判断是否应该丢包"""
        return random.random() < self.current_profile.packet_loss_rate

    def _generate_error_response(self) -> Dict[str, Any]:
        """生成错误响应"""
        if not self.active_scenario:
            return self._generate_generic_error()

        error_type = self.active_scenario.error_type

        if error_type == ErrorType.NETWORK_ERROR:
            return {
                "success": False,
                "error_type": "network_error",
                "error_message": "Network connection failed",
                "status_code": 503,
            }
        elif error_type == ErrorType.SERVER_ERROR:
            return {
                "success": False,
                "error_type": "server_error",
                "error_message": "Internal server error",
                "status_code": 500,
            }
        elif error_type == ErrorType.TIMEOUT_ERROR:
            return {
                "success": False,
                "error_type": "timeout_error",
                "error_message": "Request timeout",
                "status_code": 408,
            }
        elif error_type == ErrorType.RATE_LIMIT_ERROR:
            return {
                "success": False,
                "error_type": "rate_limit_error",
                "error_message": "Rate limit exceeded",
                "status_code": 429,
                "retry_after": self.active_scenario.retry_after,
            }
        else:
            return self._generate_generic_error()

    def _generate_packet_loss_response(self) -> Dict[str, Any]:
        """生成丢包响应"""
        return {
            "success": False,
            "error_type": "packet_loss",
            "error_message": "Packet loss detected",
            "status_code": None,
        }

    def _generate_generic_error(self) -> Dict[str, Any]:
        """生成通用错误响应"""
        return {
            "success": False,
            "error_type": "unknown_error",
            "error_message": "Unknown error occurred",
            "status_code": 500,
        }

    def add_monitoring_callback(self, callback: Callable) -> None:
        """添加监控回调"""
        self.monitoring_callbacks.append(callback)

    def _notify_monitors(self, event_type: str, data: Dict[str, Any]) -> None:
        """通知监控器"""
        for callback in self.monitoring_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                self.logger.error(f"Monitor callback error: {e}")

    def get_network_statistics(self) -> Dict[str, Any]:
        """获取网络统计信息"""
        if not self.latency_history:
            return {}

        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(1, self.request_count),
            "average_latency": sum(self.latency_history) / len(self.latency_history),
            "max_latency": max(self.latency_history),
            "min_latency": min(self.latency_history),
            "average_throughput": sum(self.throughput_history)
            / len(self.throughput_history),
            "packet_loss_count": sum(self.packet_loss_history),
            "packet_loss_rate": sum(self.packet_loss_history)
            / len(self.packet_loss_history),
            "current_profile": self.current_profile.name,
        }

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.request_count = 0
        self.error_count = 0
        self.latency_history.clear()
        self.throughput_history.clear()
        self.packet_loss_history.clear()
        self.active_scenario = None


class RecoveryHandler:
    """恢复处理器"""

    def __init__(self, network_simulator: NetworkSimulator):
        self.network_simulator = network_simulator
        self.recovery_strategies: Dict[str, Callable] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

        # 注册默认恢复策略
        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """注册默认恢复策略"""
        self.recovery_strategies.update(
            {
                "exponential_backoff": self._exponential_backoff_recovery,
                "linear_backoff": self._linear_backoff_recovery,
                "circuit_breaker": self._circuit_breaker_recovery,
                "fallback_to_cache": self._fallback_to_cache_recovery,
                "degrade_service": self._degrade_service_recovery,
                "retry_with_limit": self._retry_with_limit_recovery,
            }
        )

    def register_recovery_strategy(self, name: str, strategy: Callable) -> None:
        """注册恢复策略"""
        self.recovery_strategies[name] = strategy
        self.logger.info(f"Registered recovery strategy: {name}")

    def handle_error(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理错误"""
        error_type = error_response.get("error_type", "unknown_error")

        # 选择恢复策略
        strategy_name = self._select_recovery_strategy(error_type, context)

        if strategy_name not in self.recovery_strategies:
            return self._default_error_handling(error_response, context)

        strategy = self.recovery_strategies[strategy_name]

        # 记录恢复尝试
        recovery_attempt = {
            "timestamp": time.time(),
            "error_type": error_type,
            "strategy": strategy_name,
            "context": context,
        }

        try:
            result = strategy(error_response, context)
            recovery_attempt["success"] = True
            recovery_attempt["result"] = result
        except Exception as e:
            recovery_attempt["success"] = False
            recovery_attempt["error"] = str(e)
            result = self._default_error_handling(error_response, context)

        self.recovery_history.append(recovery_attempt)
        return result

    def _select_recovery_strategy(
        self, error_type: str, context: Dict[str, Any]
    ) -> str:
        """选择恢复策略"""
        retry_count = context.get("retry_count", 0)

        if error_type == "timeout_error":
            return "exponential_backoff"
        elif error_type == "rate_limit_error":
            return "linear_backoff"
        elif error_type == "network_error":
            if retry_count < 3:
                return "retry_with_limit"
            else:
                return "fallback_to_cache"
        elif error_type == "server_error":
            return "circuit_breaker"
        elif error_type == "packet_loss":
            return "retry_with_limit"
        else:
            return "retry_with_limit"

    def _exponential_backoff_recovery(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """指数退避恢复"""
        retry_count = context.get("retry_count", 0)
        delay = min(300, (2**retry_count))  # 最大5分钟

        self.logger.info(
            f"Exponential backoff: waiting {delay}s before retry {retry_count + 1}"
        )
        time.sleep(delay)

        return {"action": "retry", "delay": delay, "retry_count": retry_count + 1}

    def _linear_backoff_recovery(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """线性退避恢复"""
        retry_count = context.get("retry_count", 0)
        delay = min(60, retry_count * 10)  # 最大1分钟

        self.logger.info(
            f"Linear backoff: waiting {delay}s before retry {retry_count + 1}"
        )
        time.sleep(delay)

        return {"action": "retry", "delay": delay, "retry_count": retry_count + 1}

    def _circuit_breaker_recovery(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """熔断器恢复"""
        return {
            "action": "circuit_breaker_open",
            "message": "Circuit breaker opened due to server errors",
            "fallback_to_cache": True,
        }

    def _fallback_to_cache_recovery(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """回退到缓存恢复"""
        return {
            "action": "use_cache",
            "message": "Using cached data due to network issues",
        }

    def _degrade_service_recovery(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """服务降级恢复"""
        return {
            "action": "degrade_service",
            "message": "Service degraded due to errors",
            "available_features": ["basic_functionality"],
        }

    def _retry_with_limit_recovery(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """有限重试恢复"""
        retry_count = context.get("retry_count", 0)
        max_retries = context.get("max_retries", 3)

        if retry_count >= max_retries:
            return {
                "action": "give_up",
                "message": f"Max retries ({max_retries}) exceeded",
            }

        delay = min(30, retry_count * 5)  # 最大30秒
        self.logger.info(f"Retry {retry_count + 1}/{max_retries} after {delay}s")
        time.sleep(delay)

        return {"action": "retry", "delay": delay, "retry_count": retry_count + 1}

    def _default_error_handling(
        self, error_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """默认错误处理"""
        return {
            "action": "error",
            "message": "Unable to recover from error",
            "original_error": error_response,
        }

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """获取恢复统计信息"""
        if not self.recovery_history:
            return {}

        total_attempts = len(self.recovery_history)
        successful_recoveries = sum(
            1 for r in self.recovery_history if r.get("success", False)
        )

        strategy_usage = {}
        for attempt in self.recovery_history:
            strategy = attempt.get("strategy", "unknown")
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1

        return {
            "total_recovery_attempts": total_attempts,
            "successful_recoveries": successful_recoveries,
            "recovery_success_rate": successful_recoveries / total_attempts,
            "strategy_usage": strategy_usage,
            "most_used_strategy": max(strategy_usage.items(), key=lambda x: x[1])[0]
            if strategy_usage
            else None,
        }


@contextmanager
def network_simulation_context(
    simulator: NetworkSimulator, condition: NetworkCondition
):
    """网络模拟上下文管理器"""
    original_profile = simulator.current_profile
    simulator.set_network_condition(condition)

    try:
        yield simulator
    finally:
        simulator.current_profile = original_profile


# 预定义错误场景
PREDEFINED_ERROR_SCENARIOS = [
    ErrorScenario(
        name="Frequent Timeouts",
        error_type=ErrorType.TIMEOUT_ERROR,
        trigger_conditions={"probability": 0.1},
        duration=30,
    ),
    ErrorScenario(
        name="Rate Limit",
        error_type=ErrorType.RATE_LIMIT_ERROR,
        trigger_conditions={"request_count": 10},
        retry_after=60,
    ),
    ErrorScenario(
        name="Network Unstable",
        error_type=ErrorType.NETWORK_ERROR,
        trigger_conditions={"probability": 0.05},
        recovery_actions=["retry", "fallback"],
    ),
    ErrorScenario(
        name="Server Overload",
        error_type=ErrorType.SERVER_ERROR,
        trigger_conditions={"time_interval": 20},
        recovery_actions=["circuit_breaker", "degrade_service"],
    ),
]


# 全局实例
network_simulator = NetworkSimulator()
recovery_handler = RecoveryHandler(network_simulator)

# 添加预定义错误场景
for scenario in PREDEFINED_ERROR_SCENARIOS:
    network_simulator.add_error_scenario(scenario)
