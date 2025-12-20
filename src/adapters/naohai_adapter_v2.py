from __future__ import annotations

import asyncio
from concurrent.futures import Future as ThreadFuture
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.events.event_bus import EventBus
from core.monitoring.metrics_db import MetricsDB
from core.monitoring.service import MonitoringService
from core.plugins.plugin_manager import PluginManager
from core.protocol.scenario_context import ScenarioContext


class _AsyncLoopThread:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="naohai-adapter-v2-loop", daemon=True)
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


class NaohaiAdapterV2:
    """
    Phase 1 版本：提供 ScenarioContext + EventBus 的基础能力，并桥接同步调用到 asyncio。
    """

    def __init__(self):
        self._loop_thread = _AsyncLoopThread()
        self.event_bus: Optional[EventBus] = None
        self._event_bus_future: Optional[ThreadFuture] = None

        self.plugin_manager: Optional[PluginManager] = None
        self.monitoring: Optional[MonitoringService] = None

        self.current_context: Optional[ScenarioContext] = None
        self.context_stack: List[ScenarioContext] = []

    def init_event_system(self) -> None:
        if self.event_bus is not None:
            return
        self.event_bus = EventBus()
        self._event_bus_future = self._loop_thread.start(self.event_bus.start_processing())

    def init_monitoring(
        self,
        *,
        slo_definitions: Dict[str, Dict[str, Any]],
        domains_by_event_prefix: Dict[str, str],
        event_types: List[str],
        persist_path: Optional[str] = None,
    ) -> None:
        if self.monitoring is not None:
            return
        if not self.event_bus:
            raise RuntimeError("Event system not initialized; call init_event_system() first")
        metrics_db = MetricsDB(persist_path=persist_path)
        self.monitoring = MonitoringService(metrics_db=metrics_db, slo_definitions=slo_definitions)
        self.monitoring.attach_event_bus(self.event_bus, domains_by_event_prefix=domains_by_event_prefix, event_types=event_types)

    def subscribe_event(self, event_type: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        if not self.event_bus:
            raise RuntimeError("Event system not initialized; call init_event_system() first")
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
            raise RuntimeError("Event system not initialized; call init_event_system() first")
        self._loop_thread.run(self.event_bus.publish(event_type, data, source=source, correlation_id=correlation_id))

    def create_scenario_context(
        self,
        *,
        test_id: str,
        business_flow: str,
        test_name: str,
        **kwargs: Any,
    ) -> str:
        ctx = ScenarioContext(
            test_id=test_id,
            business_flow=business_flow,
            test_name=test_name,
            **kwargs,
        )
        self.current_context = ctx
        self.context_stack.append(ctx)
        return ctx.to_json()

    def init_plugins(self, plugin_dir: Optional[str] = None) -> None:
        if self.plugin_manager is not None:
            return
        if plugin_dir is None:
            plugin_dir = str(Path(__file__).resolve().parent.parent / "plugins")
        self.plugin_manager = PluginManager(plugin_dir)
        self._loop_thread.run(self.plugin_manager.load_plugins())

    def init_plugins_from_config(self, config: Dict[str, Any], services: Optional[Dict[str, Any]] = None) -> None:
        plugins_cfg = (config or {}).get("plugins", {}) or {}
        plugin_dir = plugins_cfg.get("dir") or str(Path(__file__).resolve().parent.parent / "plugins")
        enabled = plugins_cfg.get("enabled") or []
        if not isinstance(enabled, list):
            enabled = []

        plugin_configs: Dict[str, Dict[str, Any]] = {}
        for name in enabled:
            if isinstance(name, str) and name.strip():
                plugin_configs[name.strip()] = plugins_cfg.get(name.strip(), {}) or {}

        svc = dict(services or {})
        if self.event_bus and "event_bus" not in svc:
            svc["event_bus"] = self.event_bus

        if self.plugin_manager is None:
            self.plugin_manager = PluginManager(plugin_dir)
        self._loop_thread.run(
            self.plugin_manager.load_plugins(enabled_modules=list(plugin_configs.keys()), plugin_configs=plugin_configs, services=svc)
        )

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        if not self.plugin_manager:
            return {}
        return self.plugin_manager.list_plugins()

    def execute_plugin(self, plugin_name: str, params: Dict[str, Any]) -> Any:
        if not self.plugin_manager:
            raise RuntimeError("Plugin system not initialized; call init_plugins() first")
        if not self.current_context:
            raise RuntimeError("No active scenario context; call create_scenario_context() first")
        return self._loop_thread.run(self.plugin_manager.execute_plugin(plugin_name, self.current_context, params))

    def close(self) -> None:
        if self.plugin_manager:
            try:
                self._loop_thread.run(self.plugin_manager.unload_plugins())
            except Exception:
                pass
            self.plugin_manager = None

        self.monitoring = None

        if self.event_bus:
            self.event_bus.stop()
            if self._event_bus_future:
                try:
                    self._event_bus_future.result(timeout=2)
                except Exception:
                    pass
        self._loop_thread.stop()
