"""
data-testid 覆盖率门禁（基于 required_testids.yaml）

用于主流程结束后做自动化门禁校验，避免 data-testid 覆盖率回退。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

import yaml


_TESTID_RE = re.compile(r"data-testid\\s*=\\s*['\\\"]([^'\\\"]+)['\\\"]")


def load_required_testids_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def extract_hit_testids(locator_metrics: Dict[str, Any]) -> Set[str]:
    hit: Set[str] = set()
    element_details: Dict[str, Any] = locator_metrics.get("element_details") or {}

    for _name, stats in element_details.items():
        if (stats or {}).get("strategy_type") != "data_testid":
            continue
        strategy = (stats or {}).get("successful_strategy")
        if not isinstance(strategy, str) or not strategy.strip():
            continue

        match = _TESTID_RE.search(strategy)
        if match:
            hit.add(match.group(1))
            continue

        # 兜底：与 MetricsHybridLocator 的简化逻辑保持兼容
        if "'" in strategy:
            parts = strategy.split("'")
            if len(parts) >= 2 and parts[1].strip():
                hit.add(parts[1].strip())
        elif '"' in strategy:
            parts = strategy.split('"')
            if len(parts) >= 2 and parts[1].strip():
                hit.add(parts[1].strip())

    return hit


def calculate_required_coverage(required_config: Dict[str, Any],
                                hit_testids: Set[str],
                                categories: Optional[List[str]] = None) -> Dict[str, Any]:
    coverage: Dict[str, Any] = {}

    if categories is None:
        categories = [
            key for key, value in required_config.items()
            if isinstance(value, dict) and isinstance(value.get("required"), list)
        ]

    for category in categories:
        required_list = (required_config.get(category) or {}).get("required") or []
        required_list = [x for x in required_list if isinstance(x, str)]
        missing = [t for t in required_list if t not in hit_testids]
        covered = len(required_list) - len(missing)
        required = len(required_list)
        rate = round(covered / required * 100, 2) if required > 0 else 0
        coverage[category] = {
            "required": required,
            "covered": covered,
            "coverage_rate": rate,
            "missing": missing,
        }

    return coverage


def validate_testid_coverage(locator_metrics: Dict[str, Any],
                             required_config: Dict[str, Any]) -> Dict[str, Any]:
    ci_gates = required_config.get("ci_gates") or {}
    critical_paths = ci_gates.get("critical_paths") or []

    hit_testids = extract_hit_testids(locator_metrics)
    required_coverage = calculate_required_coverage(
        required_config,
        hit_testids,
        categories=[p for p in critical_paths if isinstance(p, str)],
    )

    data_testid_hit_rate = float(locator_metrics.get("data_testid_hit_rate") or 0)
    fallback_rate = float(locator_metrics.get("fallback_rate") or 0)
    failure_rate = float(locator_metrics.get("failure_rate") or 0)

    result = {
        "passed": True,
        "failures": [],
        "warnings": [],
        "required_testids_coverage": required_coverage,
        "hit_testids_count": len(hit_testids),
        "thresholds": {
            "overall_coverage_min": ci_gates.get("overall_coverage_min", 80),
            "fallback_rate_max": ci_gates.get("fallback_rate_max", 20),
            "failure_rate_max": ci_gates.get("failure_rate_max", 5),
            "critical_paths": critical_paths,
        },
    }

    # 整体命中率
    min_coverage = float(ci_gates.get("overall_coverage_min", 80))
    if data_testid_hit_rate < min_coverage:
        result["passed"] = False
        result["failures"].append(
            f"data-testid 命中率 {data_testid_hit_rate}% 低于要求 {min_coverage}%"
        )

    # 回退率
    max_fallback = float(ci_gates.get("fallback_rate_max", 20))
    if fallback_rate > max_fallback:
        result["passed"] = False
        result["failures"].append(
            f"回退率 {fallback_rate}% 超过限制 {max_fallback}%"
        )

    # 失败率
    max_failure = float(ci_gates.get("failure_rate_max", 5))
    if failure_rate > max_failure:
        result["passed"] = False
        result["failures"].append(
            f"定位失败率 {failure_rate}% 超过限制 {max_failure}%"
        )

    # 关键路径必须 100%
    for path in critical_paths:
        if path not in required_coverage:
            continue
        c = required_coverage[path]
        if (c or {}).get("coverage_rate", 0) < 100:
            result["passed"] = False
            missing = (c or {}).get("missing") or []
            result["failures"].append(
                f"{path} 关键路径覆盖率 {c.get('coverage_rate')}% 未达标 "
                f"({c.get('covered')}/{c.get('required')}), 缺失: {', '.join(missing[:10])}"
            )

    # 告警阈值（不影响 passed）
    warning_threshold = ci_gates.get("warning_threshold") or {}
    warn_coverage = float((warning_threshold.get("coverage_fall_below") or 0) or 0)
    warn_fallback = float((warning_threshold.get("fallback_above") or 0) or 0)
    if warn_coverage and data_testid_hit_rate < warn_coverage:
        result["warnings"].append(
            f"data-testid 命中率 {data_testid_hit_rate}% 低于告警阈值 {warn_coverage}%"
        )
    if warn_fallback and fallback_rate > warn_fallback:
        result["warnings"].append(
            f"回退率 {fallback_rate}% 高于告警阈值 {warn_fallback}%"
        )

    return result

