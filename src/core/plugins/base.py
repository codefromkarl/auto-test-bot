from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.protocol.scenario_context import ScenarioContext


@dataclass
class PluginResult:
    status: str  # completed/failed/timeout
    data: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class AIGCPlugin(ABC):
    """
    插件基类：只定义最小协议。
    Phase 1 目标：可动态加载、可执行、可释放资源。
    """

    name: str = ""
    capabilities: List[str] = []
    dependencies: List[str] = []

    async def setup(self) -> None:
        return None

    @abstractmethod
    async def execute(self, context: ScenarioContext, params: Dict[str, Any]) -> PluginResult:
        raise NotImplementedError

    async def cleanup(self) -> None:
        return None

    def health_check(self) -> bool:
        return True
