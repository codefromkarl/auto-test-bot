from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .slo import SLOStatus


@dataclass
class Alert:
    slo: str
    message: str
    severity: str = "warning"
    timestamp: str = ""
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slo": self.slo,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp or datetime.now().isoformat(),
            "details": self.details or {},
        }


class AlertManager:
    """
    最小告警生成器（Phase 3 MVP）：
    - 仅负责把 SLO violations 转成结构化告警列表
    """

    def generate_alerts(self, slo_status: SLOStatus) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        for slo, reason in slo_status.violations.items():
            details = slo_status.details.get(slo, {})
            alert = Alert(
                slo=slo,
                message=reason,
                severity="critical" if details.get("type") == "event_ratio" else "warning",
                details=details,
            )
            alerts.append(alert.to_dict())
        return alerts

