from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional


@dataclass
class PipelineResult:
    success: bool
    files: List[Dict[str, Any]] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class ProcessingStage:
    def get_stage_name(self) -> str:
        raise NotImplementedError

    async def process(self, data: Any, context: Dict[str, Any]) -> Any:
        raise NotImplementedError


class ProcessingPipeline:
    def __init__(self, stages: List[ProcessingStage]):
        self._stages = stages

    async def process(self, input_data: Any, *, config: Dict[str, Any]) -> PipelineResult:
        context: Dict[str, Any] = {"config": config, "metrics": {"stages": []}}
        data = input_data
        start = time.monotonic()

        try:
            for stage in self._stages:
                stage_start = time.monotonic()
                data = await stage.process(data, context)
                context["metrics"]["stages"].append(
                    {"stage": stage.get_stage_name(), "elapsed_seconds": time.monotonic() - stage_start}
                )
            return PipelineResult(
                success=bool(context.get("validation", {}).get("is_valid", True)),
                files=list(context.get("files", []) or []),
                validation=dict(context.get("validation", {}) or {}),
                metrics={"elapsed_seconds": time.monotonic() - start, **context.get("metrics", {})},
            )
        except Exception as exc:
            return PipelineResult(
                success=False,
                files=list(context.get("files", []) or []),
                validation=dict(context.get("validation", {}) or {}),
                metrics={"elapsed_seconds": time.monotonic() - start, **context.get("metrics", {})},
                error=str(exc),
            )

