from __future__ import annotations

import asyncio
from asyncio import Queue
from datetime import datetime
import inspect
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from uuid import uuid4


Event = Dict[str, Any]
Subscriber = Callable[[Event], Union[None, Awaitable[None]]]


class EventBus:
    """事件总线：异步 publish + 订阅回调分发。"""

    def __init__(self, *, queue_maxsize: int = 0):
        self._subscribers: Dict[str, List[Subscriber]] = {}
        self._queue: Queue[Event] = Queue(maxsize=queue_maxsize)
        self._running = False

    def subscribe(self, event_type: str, callback: Subscriber) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        source: str = "unknown",
        correlation_id: Optional[str] = None,
    ) -> None:
        event: Event = {
            "event_type": event_type,
            "event_id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "correlation_id": correlation_id,
            "data": data,
        }
        await self._queue.put(event)

    async def start_processing(self) -> None:
        self._running = True
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            try:
                await self._dispatch(event)
            finally:
                self._queue.task_done()

    def stop(self) -> None:
        self._running = False

    async def _dispatch(self, event: Event) -> None:
        event_type = str(event.get("event_type") or "")
        subscribers = list(self._subscribers.get(event_type, []))
        if not subscribers:
            return

        tasks: List[Awaitable[None]] = []
        for callback in subscribers:
            try:
                if inspect.iscoroutinefunction(callback):
                    tasks.append(callback(event))  # type: ignore[arg-type]
                else:
                    result = callback(event)
                    if asyncio.iscoroutine(result):
                        tasks.append(result)  # type: ignore[arg-type]
            except Exception:
                # 订阅者异常不影响其他订阅者
                continue

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

