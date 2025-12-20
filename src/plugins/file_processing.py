from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from core.events.event_bus import EventBus
from core.file_processing.pipeline import ProcessingPipeline
from core.file_processing.stages import CleanupStage, DownloadStage, ValidationStage
from core.plugins.base import AIGCPlugin, PluginResult
from core.protocol.scenario_context import ScenarioContext


class FileProcessingPlugin(AIGCPlugin):
    """
    文件处理插件（Phase 2 MVP）：
    - DownloadStage: 将 content_bytes/source_path/local_path 统一成 local_path
    - ValidationStage: size_equals / sha256
    - CleanupStage: keep_temp 控制是否清理临时文件
    """

    name = "file_processing"
    capabilities = ["file.download", "file.validate", "file.cleanup"]

    def __init__(self, *, base_temp_dir: Optional[str] = None, event_bus: Optional[EventBus] = None):
        self._event_bus = event_bus
        self._base_temp_dir = base_temp_dir
        self._pipeline = ProcessingPipeline([DownloadStage(), ValidationStage(), CleanupStage()])

    async def execute(self, context: ScenarioContext, params: Dict[str, Any]) -> PluginResult:
        file_info = params.get("file_info")
        if not isinstance(file_info, dict):
            return PluginResult(status="failed", error="file_info 必须是对象(dict)")

        max_size = int(params.get("max_size", 500 * 1024 * 1024))
        keep_temp = bool(params.get("keep_temp", False))
        validation_rules = params.get("validation_rules", {}) or {}

        base_temp_dir = self._base_temp_dir or str(Path("temp"))
        config = {
            "max_size": max_size,
            "keep_temp": keep_temp,
            "validation_rules": validation_rules,
            "base_temp_dir": base_temp_dir,
        }

        await self._emit("file.download_started", {"filename": file_info.get("filename"), "base_temp_dir": base_temp_dir})

        pipeline_result = await self._pipeline.process(file_info, config=config)

        if pipeline_result.files:
            await self._emit(
                "file.download_completed",
                {
                    "local_path": pipeline_result.files[0].get("local_path"),
                    "size": pipeline_result.files[0].get("size"),
                },
            )

        status = "completed" if pipeline_result.success else "failed"
        if status == "failed" and pipeline_result.error:
            await self._emit("file.processing_failed", {"error": pipeline_result.error})

        return PluginResult(
            status=status,
            data={
                "files": pipeline_result.files,
                "validation_report": pipeline_result.validation,
                "processing_metrics": pipeline_result.metrics,
            },
            error=pipeline_result.error,
            metrics=pipeline_result.metrics,
        )

    async def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            await self._event_bus.publish(event_type, data, source="plugin.file_processing")
        except Exception:
            return


def create_plugin(config: dict, services: dict) -> FileProcessingPlugin:
    """
    PluginManager 工厂入口：支持从 config/ services 注入 base_temp_dir 与 event_bus。
    """
    base_temp_dir = config.get("base_temp_dir") if isinstance(config, dict) else None
    event_bus = services.get("event_bus")
    return FileProcessingPlugin(base_temp_dir=base_temp_dir, event_bus=event_bus)
