from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.events.event_bus import EventBus

from .metrics_db import MetricsDB


class EventBusMetricsIngestor:
    """
    把 EventBus 事件写入 MetricsDB（Phase 3 MVP）：
    - 通过 domains_by_event_prefix 把 event_type 前缀映射到 domain
    """

    def __init__(self, *, metrics_db: MetricsDB, domains_by_event_prefix: Dict[str, str]):
        self._db = metrics_db
        self._domains_by_prefix = dict(domains_by_event_prefix)

    def attach(self, event_bus: EventBus, *, event_types: List[str]) -> None:
        for et in event_types:
            event_bus.subscribe(et, self._make_handler(et))

    def _make_handler(self, event_type: str):
        async def handler(evt: Dict[str, Any]) -> None:
            domain = self._resolve_domain(event_type)
            self._db.record(domain, {"event_type": event_type, "event": evt})

        return handler

    def _resolve_domain(self, event_type: str) -> str:
        for prefix, domain in self._domains_by_prefix.items():
            if event_type.startswith(prefix):
                return domain
        return "events"

