from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .metrics_db import MetricsDB


@dataclass
class SLOStatus:
    all_compliant: bool
    details: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    violations: Dict[str, str] = field(default_factory=dict)


class SLOEvaluator:
    """
    最小 SLO 评估器（Phase 3 MVP）：
    - 仅支持基于事件计数的比例型指标（event_ratio）
    """

    def __init__(self, *, definitions: Dict[str, Dict[str, Any]]):
        self._definitions = definitions

    def evaluate(self, metrics_db: MetricsDB) -> SLOStatus:
        details: Dict[str, Dict[str, Any]] = {}
        violations: Dict[str, str] = {}

        for name, spec in self._definitions.items():
            slo_type = spec.get("type")
            if slo_type != "event_ratio":
                violations[name] = f"unsupported slo type: {slo_type}"
                continue

            domain = str(spec.get("domain") or "")
            numerator_event = str(spec.get("numerator_event") or "")
            denom_events = spec.get("denominator_events") or []
            min_value = float(spec.get("min", 0))

            if not domain or not numerator_event or not isinstance(denom_events, list) or not denom_events:
                violations[name] = "invalid slo spec"
                continue

            numerator = metrics_db.count_event_type(domain, numerator_event)
            denominator = sum(metrics_db.count_event_type(domain, str(e)) for e in denom_events)
            value = float(numerator) / float(denominator) if denominator > 0 else 1.0

            details[name] = {
                "type": slo_type,
                "domain": domain,
                "numerator_event": numerator_event,
                "denominator_events": list(denom_events),
                "numerator": numerator,
                "denominator": denominator,
                "value": value,
                "min": min_value,
            }

            if value < min_value:
                violations[name] = f"value {value} < min {min_value}"

        return SLOStatus(all_compliant=(len(violations) == 0), details=details, violations=violations)

