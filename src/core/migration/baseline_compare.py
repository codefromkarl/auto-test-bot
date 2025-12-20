from __future__ import annotations

from typing import Any, Dict, List

from core.monitoring.metrics_db import MetricsDB


def _load_db(path: str) -> MetricsDB:
    return MetricsDB(persist_path=path)


def compare_event_ratio_slo(
    *,
    baseline_path: str,
    current_path: str,
    domain: str,
    numerator_event: str,
    denominator_events: List[str],
) -> Dict[str, Any]:
    baseline_db = _load_db(baseline_path)
    current_db = _load_db(current_path)

    b_num = baseline_db.count_event_type(domain, numerator_event)
    b_den = sum(baseline_db.count_event_type(domain, e) for e in denominator_events)
    c_num = current_db.count_event_type(domain, numerator_event)
    c_den = sum(current_db.count_event_type(domain, e) for e in denominator_events)

    b_val = float(b_num) / float(b_den) if b_den > 0 else 1.0
    c_val = float(c_num) / float(c_den) if c_den > 0 else 1.0

    return {
        "baseline_value": b_val,
        "current_value": c_val,
        "baseline_counts": {"numerator": b_num, "denominator": b_den},
        "current_counts": {"numerator": c_num, "denominator": c_den},
        "regressed": c_val < b_val,
    }

