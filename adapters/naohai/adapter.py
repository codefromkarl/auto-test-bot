import yaml
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Type

from src.adapters.base import BaseAdapter
from src.models.semantic_action import SemanticAction
from src.adapters.naohai.semantic_actions.actions import (
    EnterAICreationSemanticAction,
    EnsureStoryExistsSemanticAction,
    OpenFirstStoryCardSemanticAction,
    EnterStoryboardManagementSemanticAction,
    BindCharactersSemanticAction,
    ExportResourcePackageSemanticAction,
    SelectFusionGenerationSemanticAction,
    CreateSceneModeSemanticAction,
    SuggestShotCountSemanticAction,
    SelectVideoSegmentsSemanticAction,
    OpenEpisodeMenuSemanticAction,
    CreateCharacterSemanticAction,
    UploadSceneAssetSemanticAction
)

# Preserve core adapter capabilities
import asyncio
from concurrent.futures import Future as ThreadFuture
import threading
from src.core.events.event_bus import EventBus
from src.core.monitoring.metrics_db import MetricsDB
from src.core.monitoring.service import MonitoringService
from src.core.plugins.plugin_manager import PluginManager
from src.core.protocol.scenario_context import ScenarioContext

class _AsyncLoopThread:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="naohai-adapter-loop", daemon=True)
        self._ready = threading.Event()
        self._thread.start()
        self._ready.wait(timeout=2)

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()

    def run(self, coro) -> Any:
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=5)

    def start(self, coro) -> ThreadFuture:
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def stop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=2)
        try:
            self._loop.close()
        except Exception:
            pass

class NaohaiAdapter(BaseAdapter):
    """
    鬧海业务适配器实现
    """

    def __init__(self):
        self._selectors_raw: Dict[str, Any] = {}
        self._selectors_flat: Dict[str, str] = {}
        self._semantic_actions: Dict[str, Type[SemanticAction]] = {}
        self._loop_thread = _AsyncLoopThread()
        self.event_bus: Optional[EventBus] = None
        self._event_bus_future: Optional[ThreadFuture] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.monitoring: Optional[MonitoringService] = None
        self.current_context: Optional[ScenarioContext] = None
        self.context_stack: List[ScenarioContext] = []
        
        self.load_config()
        # Keep backward-compatible side-effect registration on init.
        self.register_actions()

    @staticmethod
    def _flatten_selectors(tree: Any, prefix: str = "") -> Dict[str, str]:
        flat: Dict[str, str] = {}
        if isinstance(tree, dict):
            for key, value in tree.items():
                key = str(key)
                next_prefix = f"{prefix}.{key}" if prefix else key
                flat.update(NaohaiAdapter._flatten_selectors(value, next_prefix))
            return flat
        if tree is None:
            return flat
        flat[prefix] = str(tree)
        return flat

    def load_config(self) -> None:
        config_path = Path(__file__).parent / "selectors.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._selectors_raw = yaml.safe_load(f) or {}
                self._selectors_flat = self._flatten_selectors(self._selectors_raw)

    def register_semantic_actions(self) -> Mapping[str, Type[SemanticAction]]:
        actions: Dict[str, Type[SemanticAction]] = {
            'enter_ai_creation': EnterAICreationSemanticAction,
            'ensure_story_exists': EnsureStoryExistsSemanticAction,
            'open_first_story_card': OpenFirstStoryCardSemanticAction,
            'enter_storyboard_management': EnterStoryboardManagementSemanticAction,
            'bind_characters': BindCharactersSemanticAction,
            'export_resource_package': ExportResourcePackageSemanticAction,
            'select_fusion_generation': SelectFusionGenerationSemanticAction,
            'create_scene_mode': CreateSceneModeSemanticAction,
            'suggest_shot_count': SuggestShotCountSemanticAction,
            'select_video_segments': SelectVideoSegmentsSemanticAction,
            'open_episode_menu': OpenEpisodeMenuSemanticAction,
            'create_character': CreateCharacterSemanticAction,
            'upload_scene_asset': UploadSceneAssetSemanticAction,
        }
        self._semantic_actions = dict(actions)
        return actions

    def register_selectors(self) -> Mapping[str, str]:
        return dict(self._selectors_flat)

    def get_config(self) -> Dict[str, Any]:
        return {
            "selectors": dict(self._selectors_raw),
        }

    # --- Backward-compatible aliases (older code/doc names) ---

    def register_actions(self) -> None:
        for name, cls in self.register_semantic_actions().items():
            SemanticAction.register(name, cls)

    def get_workflow_dir(self) -> str:
        return str(Path(__file__).parent / "workflows")

    # --- Core functionality methods ---

    def init_event_system(self) -> None:
        if self.event_bus is not None:
            return
        self.event_bus = EventBus()
        self._event_bus_future = self._loop_thread.start(self.event_bus.start_processing())

    def init_monitoring(self, **kwargs: Any) -> None:
        if self.monitoring is not None:
            return
        if not self.event_bus:
            raise RuntimeError("Event system not initialized")
        metrics_db = MetricsDB(persist_path=kwargs.get('persist_path'))
        self.monitoring = MonitoringService(metrics_db=metrics_db, slo_definitions=kwargs.get('slo_definitions', {}))
        self.monitoring.attach_event_bus(self.event_bus, **kwargs)

    def subscribe_event(self, event_type: str, callback: Any) -> None:
        if not self.event_bus:
            raise RuntimeError("Event system not initialized")
        self.event_bus.subscribe(event_type, callback)

    def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        source: str = "unknown",
        correlation_id: Optional[str] = None,
    ) -> None:
        if not self.event_bus:
            raise RuntimeError("Event system not initialized")
        self._loop_thread.run(self.event_bus.publish(event_type, data, source=source, correlation_id=correlation_id))

    def create_scenario_context(self, **kwargs: Any) -> str:
        ctx = ScenarioContext(**kwargs)
        self.current_context = ctx
        self.context_stack.append(ctx)
        return ctx.to_json()

    def close(self) -> None:
        if self.plugin_manager:
            try: self._loop_thread.run(self.plugin_manager.unload_plugins())
            except: pass
        self._loop_thread.stop()
