from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models import Workflow


@dataclass(frozen=True)
class GoldenPathCoverageItem:
    key: str
    required_phase: str
    present: bool
    screenshot_steps: int


REQUIRED_PHASES: list[str] = [
    "create_script_and_outline",
    "setup_episode_assets",
    "analyze_and_create_storyboard",
    "bind_storyboard_assets",
    "generate_image_assets",
    "generate_video_segments",
    "export_final_video",
]


def _count_screenshot_steps(phase) -> int:
    count = 0
    for step in getattr(phase, "steps", []) or []:
        try:
            if step.get_step_name() == "screenshot":
                count += 1
        except Exception:
            continue
    return count


def validate_golden_path_workflow(workflow: Workflow) -> list[str]:
    """
    对黄金路径 E2E workflow 做静态结构校验。

    目标：
    - 能被 `Workflow.from_yaml` 成功解析（调用方保证）
    - 必须包含 7 个关键阶段（Phase 1.1）
    - 每个阶段至少包含 1 个截图步骤作为证据（best-effort）
    """
    errors: list[str] = []

    phases = list(getattr(workflow, "phases", []) or [])
    phase_names = [getattr(p, "name", None) for p in phases]

    if len(phases) != 7:
        errors.append(f"phase 数量应为 7，实际为 {len(phases)}")

    missing = [name for name in REQUIRED_PHASES if name not in phase_names]
    if missing:
        errors.append(f"缺少关键 phase: {', '.join(missing)}")

    duplicated = sorted({n for n in phase_names if phase_names.count(n) > 1 and n is not None})
    if duplicated:
        errors.append(f"phase name 重复: {', '.join(duplicated)}")

    for phase in phases:
        phase_name = getattr(phase, "name", "unknown_phase")
        screenshots = _count_screenshot_steps(phase)
        if screenshots <= 0:
            errors.append(f"phase '{phase_name}' 缺少 screenshot 证据步骤")

    criteria = list(getattr(workflow, "success_criteria", []) or [])
    if len(criteria) < 7:
        errors.append(f"success_criteria 建议至少 7 条（当前 {len(criteria)}）")

    return errors


def evaluate_golden_path_coverage(workflow: Workflow) -> dict[str, Any]:
    """
    覆盖度评估（静态）：以“7阶段是否存在 + 是否有截图证据”为判断依据。
    """
    phases = list(getattr(workflow, "phases", []) or [])
    by_name = {getattr(p, "name", ""): p for p in phases}

    items: list[GoldenPathCoverageItem] = []
    for phase_name in REQUIRED_PHASES:
        phase = by_name.get(phase_name)
        present = phase is not None
        screenshots = _count_screenshot_steps(phase) if phase is not None else 0
        items.append(
            GoldenPathCoverageItem(
                key=phase_name,
                required_phase=phase_name,
                present=present,
                screenshot_steps=screenshots,
            )
        )

    covered = [i for i in items if i.present]
    covered_with_evidence = [i for i in items if i.present and i.screenshot_steps > 0]

    return {
        "required_phases": list(REQUIRED_PHASES),
        "items": [i.__dict__ for i in items],
        "present_count": len(covered),
        "present_with_screenshot_count": len(covered_with_evidence),
        "coverage_ratio": (len(covered) / 7.0) if 7 else 0.0,
        "evidence_ratio": (len(covered_with_evidence) / 7.0) if 7 else 0.0,
    }

