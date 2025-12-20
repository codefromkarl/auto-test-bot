from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict, Optional

from core.events.event_bus import EventBus
from core.plugins.base import AIGCPlugin, PluginResult
from core.protocol.scenario_context import ScenarioContext
from core.tasks.task_observer import TaskObserver


def _get_sla(params: Dict[str, Any]) -> Dict[str, Any]:
    sla = params.get("sla") or {}
    if not isinstance(sla, dict):
        raise ValueError("sla 必须是对象(dict)")
    return sla


class AsyncTaskPlugin(AIGCPlugin):
    """
    通用异步任务等待插件（Phase 2 MVP）：
    - 通过 TaskObserver 轮询获取任务状态
    - 支持超时、指数退避、最大轮询间隔
    - 可选发布 task.* 事件到 EventBus
    """

    name = "async_task"
    capabilities = ["async_task.wait"]

    def __init__(
        self,
        observer: Optional[TaskObserver] = None,
        sleep_fn: Optional[Callable[[float], Awaitable[None]]] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self._observer = observer
        self._sleep = sleep_fn
        self._event_bus = event_bus

    async def execute(self, context: ScenarioContext, params: Dict[str, Any]) -> PluginResult:
        task_id = params.get("task_id")
        task_type = params.get("task_type") or "unknown"
        task_params = params.get("task_params") or {}

        if not isinstance(task_id, str) or not task_id.strip():
            return PluginResult(status="failed", error="task_id 必须是非空字符串")
        if not isinstance(task_type, str) or not task_type.strip():
            return PluginResult(status="failed", error="task_type 必须是非空字符串")
        if not isinstance(task_params, dict):
            return PluginResult(status="failed", error="task_params 必须是对象(dict)")

        observer = self._observer
        if observer is None:
            observer = self._build_observer_from_params(params)
        if observer is None:
            return PluginResult(status="failed", error="observer 未配置（可通过 params.observer 配置）")

        sla = _get_sla(params)
        timeout_seconds = float(sla.get("timeout_seconds", 300))
        poll_interval_seconds = float(sla.get("poll_interval_seconds", 1))
        backoff_factor = float(sla.get("backoff_factor", 1.5))
        max_interval_seconds = float(sla.get("max_interval_seconds", 10))

        if poll_interval_seconds <= 0:
            poll_interval_seconds = 0.1
        if backoff_factor < 1:
            backoff_factor = 1.0
        if max_interval_seconds <= 0:
            max_interval_seconds = poll_interval_seconds

        sleep = self._sleep
        if sleep is None:
            import asyncio

            sleep = asyncio.sleep

        start = time.monotonic()
        attempts = 0
        interval = poll_interval_seconds

        await self._emit("task.started", {"task_id": task_id, "task_type": task_type})

        while True:
            attempts += 1
            status = await observer.get_status(task_id=task_id, task_type=task_type, task_params=task_params)
            state = str(status.get("state") or "").lower()

            if state == "completed":
                data = status.get("result") or {}
                if not isinstance(data, dict):
                    data = {"result": data}
                metrics = {
                    "attempts": attempts,
                    "elapsed_seconds": time.monotonic() - start,
                    "final_state": "completed",
                }
                await self._emit("task.completed", {"task_id": task_id, "task_type": task_type, "metrics": metrics})
                return PluginResult(status="completed", data=data, metrics=metrics)

            if state == "failed":
                err = status.get("error") or "task failed"
                await self._emit("task.failed", {"task_id": task_id, "task_type": task_type, "error": str(err)})
                return PluginResult(status="failed", error=str(err), metrics={"attempts": attempts})

            elapsed = time.monotonic() - start
            if elapsed >= timeout_seconds:
                await self._emit(
                    "task.timeout",
                    {"task_id": task_id, "task_type": task_type, "attempts": attempts, "elapsed_seconds": elapsed},
                )
                return PluginResult(
                    status="timeout",
                    error=f"任务超时: {task_id}",
                    metrics={"attempts": attempts, "elapsed_seconds": elapsed, "final_state": "timeout"},
                )

            await sleep(interval)
            interval = min(max_interval_seconds, interval * backoff_factor)

    async def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            await self._event_bus.publish(event_type, data, source="plugin.async_task")
        except Exception:
            return

    def _build_observer_from_params(self, params: Dict[str, Any]) -> Optional[TaskObserver]:
        observer_cfg = params.get("observer")
        if observer_cfg is None:
            return None
        if not isinstance(observer_cfg, dict):
            raise ValueError("observer 必须是对象(dict)")
        obs_type = str(observer_cfg.get("type") or "").strip().lower()
        if obs_type == "sequence":
            from core.tasks.task_observer import SequenceTaskObserver

            statuses = observer_cfg.get("statuses")
            if not isinstance(statuses, list) or not statuses:
                raise ValueError("observer.statuses 必须是非空数组(list)")
            for s in statuses:
                if not isinstance(s, dict):
                    raise ValueError("observer.statuses 每项必须是对象(dict)")
            return SequenceTaskObserver(statuses=statuses)
        return None


def create_plugin(config: dict, services: dict) -> AsyncTaskPlugin:
    """
    PluginManager 工厂入口：
    - 可通过 services 注入 observer/event_bus/sleep_fn
    - 运行期也可通过 params.observer 传入测试/模拟 observer
    """
    observer = services.get("task_observer")
    event_bus = services.get("event_bus")
    sleep_fn = services.get("sleep_fn")
    return AsyncTaskPlugin(observer=observer, sleep_fn=sleep_fn, event_bus=event_bus)
