from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.events.event_bus import EventBus

from .alerts import AlertManager
from .event_ingest import EventBusMetricsIngestor
from .metrics_db import MetricsDB
from .notifiers import AlertNotifier
from .slo import SLOEvaluator, SLOStatus


@dataclass
class MonitoringSnapshot:
    slo_status: SLOStatus
    alerts: List[Dict[str, Any]]


class MonitoringService:
    """
    监控服务（Phase 3 MVP）：
    - 事件采集：EventBus -> MetricsDB
    - SLO 评估：SLOEvaluator
    - 告警生成：AlertManager
    """

    def __init__(
        self,
        *,
        metrics_db: MetricsDB,
        slo_definitions: Dict[str, Dict[str, Any]],
        alert_manager: Optional[AlertManager] = None,
        notifier: Optional[AlertNotifier] = None,
    ):
        self.metrics_db = metrics_db
        self._evaluator = SLOEvaluator(definitions=slo_definitions)
        self._alerts = alert_manager or AlertManager()
        self._notifier = notifier
        self._ingestor: Optional[EventBusMetricsIngestor] = None

    def attach_event_bus(
        self,
        event_bus: EventBus,
        *,
        domains_by_event_prefix: Dict[str, str],
        event_types: List[str],
    ) -> None:
        self._ingestor = EventBusMetricsIngestor(
            metrics_db=self.metrics_db,
            domains_by_event_prefix=domains_by_event_prefix,
        )
        self._ingestor.attach(event_bus, event_types=event_types)

    def evaluate_now(self) -> Dict[str, Any]:
        slo_status = self._evaluator.evaluate(self.metrics_db)
        alerts = self._alerts.generate_alerts(slo_status)
        return {"slo_status": slo_status, "alerts": alerts}

    def evaluate_and_dispatch(self) -> Dict[str, Any]:
        snapshot = self.evaluate_now()
        if self._notifier:
            try:
                self._notifier.send(snapshot["alerts"])
            except Exception:
                pass
        return snapshot
