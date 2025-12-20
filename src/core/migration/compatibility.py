from __future__ import annotations

from typing import List


def validate_v2_components() -> List[str]:
    """
    Phase4 兼容性矩阵的最小自动化校验：
    - 核心模块可 import（协议/事件/插件/监控/三大插件）
    返回问题列表；为空表示通过。
    """
    checks = [
        "core.protocol.scenario_context",
        "core.events.event_bus",
        "core.plugins.plugin_manager",
        "core.monitoring.metrics_db",
        "core.monitoring.slo",
        "core.monitoring.alerts",
        "core.monitoring.service",
        "plugins.async_task",
        "plugins.file_processing",
        "plugins.api_mixing",
    ]

    problems: List[str] = []
    for mod in checks:
        try:
            __import__(mod)
        except Exception as exc:
            problems.append(f"{mod}: {exc}")
    return problems

