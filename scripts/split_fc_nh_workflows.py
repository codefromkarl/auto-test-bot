#!/usr/bin/env python3
"""
Split Naohai FC-NH workflows into one-file-per-FC-number.

This repo contains several merged workflows (e.g. FC-NH-013~017 in one file),
and also partially-split placeholder files missing the `workflow:` root key.
This script generates/overwrites `workflows/naohai_FC_NH_XXX.yaml` for:
  - FC-NH-004 ~ FC-NH-011 (from a minimal create-modal flow)
  - FC-NH-013 ~ FC-NH-050 (from existing merged workflows)

It is safe to run multiple times.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


WORKFLOWS_DIR = Path("workflows")


def _dump_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            indent=2,
        )


def _load_workflow(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "workflow" not in data:
        raise ValueError(f"Invalid workflow file (missing workflow root): {path}")
    wf = data["workflow"]
    if not isinstance(wf, dict):
        raise ValueError(f"Invalid workflow root type: {path}")
    return wf


def _selector_candidates(selector: str) -> List[str]:
    return [p.strip() for p in str(selector).split(",") if p.strip()]


def _phase(name: str, description: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"name": name, "description": description, "steps": steps}


def _workflow(
    name: str,
    description: str,
    phases: List[Dict[str, Any]],
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    wf: Dict[str, Any] = {"name": name, "description": description, "phases": phases}
    if metadata:
        wf.update(metadata)
    return {"workflow": wf}


def _minimal_enter_story_list_phase() -> Dict[str, Any]:
    return _phase(
        name="enter_story_list",
        description="进入剧本列表页",
        steps=[
            {"action": "open_page", "url": "${test.url}", "timeout": "${test.timeout.page_load}"},
            {
                "action": "wait_for",
                "condition": {"selector": "body", "visible": True},
                "timeout": "${test.timeout.element_load}",
            },
            {"action": "assert_logged_in"},
            {
                "action": "click",
                "selector": '.nav-routerTo-item:has-text("AI创作")',
                "timeout": "${test.timeout.element_load}",
            },
            {
                "action": "wait_for",
                "condition": {"selector": "text=剧本列表", "visible": True},
                "timeout": "${test.timeout.page_load}",
            },
        ],
    )


def _minimal_open_create_modal_phase() -> Dict[str, Any]:
    return _phase(
        name="open_create_modal",
        description="打开新建剧本弹窗",
        steps=[
            {"action": "click", "selector": "div.list-item.add-item", "timeout": "${test.timeout.element_load}"},
            {
                "action": "wait_for",
                "condition": {"selector": "text=基础信息", "visible": True},
                "timeout": "${test.timeout.element_load}",
            },
            {
                "action": "screenshot",
                "name": "create_modal_open",
                "save_path": "screenshots/naohai/fc_nh_004_modal_open.png",
            },
        ],
    )


def generate_fc_004_to_011() -> None:
    enter_story_list = _minimal_enter_story_list_phase()
    open_modal = _minimal_open_create_modal_phase()

    cover_path = "tests/assets/cover.png"

    def write(num: int, desc: str, extra_phase: Dict[str, Any]) -> None:
        name = f"naohai_FC_NH_{num:03d}"
        out = WORKFLOWS_DIR / f"{name}.yaml"
        phases = [copy.deepcopy(enter_story_list), copy.deepcopy(open_modal), extra_phase]
        _dump_yaml(out, _workflow(name=name, description=desc, phases=phases))

    # FC-NH-004: 打开新建弹窗（已由 open_modal 截图覆盖），再补一个轻量的存在性断言
    write(
        4,
        "FC-NH-004: 打开新建弹窗",
        _phase(
            "fc_nh_004",
            "FC-NH-004: 打开新建弹窗",
            [
                {"action": "assert_element_exists", "selector": "text=基础信息, .modal, .dialog", "optional": True},
                {"action": "screenshot", "name": "fc_nh_004", "save_path": "screenshots/naohai/fc_nh_004.png"},
            ],
        ),
    )

    write(
        5,
        "FC-NH-005: 填写剧本名称",
        _phase(
            "fc_nh_005",
            "FC-NH-005: 填写剧本名称",
            [
                {
                    "action": "assert_element_exists",
                    "selector": "input[placeholder*='剧本名称'], input[placeholder*='名称']",
                    "optional": True,
                },
                {
                    "action": "input",
                    "selector": "input[placeholder*='剧本名称'], input[placeholder*='名称']",
                    "text": "测试剧本_${timestamp}",
                    "clear": True,
                    "optional": True,
                },
                {"action": "screenshot", "name": "fc_nh_005", "save_path": "screenshots/naohai/fc_nh_005_name.png"},
            ],
        ),
    )

    write(
        6,
        "FC-NH-006: 编写项目说明/大纲",
        _phase(
            "fc_nh_006",
            "FC-NH-006: 编写项目说明/大纲",
            [
                {"action": "assert_element_exists", "selector": "textarea", "optional": True},
                {
                    "action": "input",
                    "selector": "textarea",
                    "text": "这是自动化测试输入的项目说明/大纲内容。",
                    "clear": True,
                    "optional": True,
                },
                {"action": "screenshot", "name": "fc_nh_006", "save_path": "screenshots/naohai/fc_nh_006_desc.png"},
            ],
        ),
    )

    write(
        7,
        "FC-NH-007: 上传封面",
        _phase(
            "fc_nh_007",
            "FC-NH-007: 上传封面",
            [
                {"action": "assert_element_exists", "selector": "input[type='file']", "optional": True},
                {"action": "upload_file", "selector": "input[type='file']", "file_path": cover_path, "optional": True},
                {"action": "screenshot", "name": "fc_nh_007", "save_path": "screenshots/naohai/fc_nh_007_cover.png"},
            ],
        ),
    )

    write(
        8,
        "FC-NH-008: 选择画幅比例",
        _phase(
            "fc_nh_008",
            "FC-NH-008: 选择画幅比例",
            [
                {
                    "action": "assert_element_exists",
                    "selector": "text=16:9, text=9:16, text=1:1, text=4:3, text=3:4",
                    "optional": True,
                },
                {"action": "click", "selector": "text=16:9", "timeout": "${test.timeout.element_load}", "optional": True},
                {"action": "screenshot", "name": "fc_nh_008", "save_path": "screenshots/naohai/fc_nh_008_ratio.png"},
            ],
        ),
    )

    write(
        9,
        "FC-NH-009: 下一步进入画风与预览",
        _phase(
            "fc_nh_009",
            "FC-NH-009: 下一步进入画风与预览",
            [
                {"action": "assert_element_exists", "selector": "text=下一步", "optional": True},
                {"action": "click", "selector": "text=下一步", "timeout": "${test.timeout.element_load}", "optional": True},
                {
                    "action": "wait_for",
                    "condition": {"selector": "text=画风", "visible": True},
                    "timeout": "${test.timeout.page_load}",
                    "optional": True,
                },
                {"action": "screenshot", "name": "fc_nh_009", "save_path": "screenshots/naohai/fc_nh_009_style.png"},
            ],
        ),
    )

    write(
        10,
        "FC-NH-010: 选择画风",
        _phase(
            "fc_nh_010",
            "FC-NH-010: 选择画风",
            [
                {"action": "click", "selector": ".style-card:first-child, .style-option:first-child, .art-style-item:first-child", "timeout": "${test.timeout.element_load}", "optional": True},
                {"action": "screenshot", "name": "fc_nh_010", "save_path": "screenshots/naohai/fc_nh_010_style_selected.png"},
            ],
        ),
    )

    write(
        11,
        "FC-NH-011: 预览效果区",
        _phase(
            "fc_nh_011",
            "FC-NH-011: 预览效果区",
            [
                {"action": "assert_element_exists", "selector": "text=预览, .preview, .style-preview, .preview-area", "optional": True},
                {"action": "screenshot", "name": "fc_nh_011", "save_path": "screenshots/naohai/fc_nh_011_preview.png"},
            ],
        ),
    )


def _metadata_without_name_desc_phases(wf: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in wf.items() if k not in ("name", "description", "phases")}


def generate_from_episode_management() -> None:
    src = _load_workflow(WORKFLOWS_DIR / "naohai_FC_NH_013_episode_management.yaml")
    meta = _metadata_without_name_desc_phases(src)
    phases_by_name = {p["name"]: p for p in src.get("phases", [])}
    setup = copy.deepcopy(phases_by_name["enter_story_detail"])

    create_steps = phases_by_name["create_new_episode"]["steps"]
    menu_steps = phases_by_name["test_episode_menu"]["steps"]

    # 013
    ph_013 = copy.deepcopy(phases_by_name["add_episode_entry"])
    _dump_yaml(
        WORKFLOWS_DIR / "naohai_FC_NH_013.yaml",
        _workflow(
            "naohai_FC_NH_013",
            "FC-NH-013: 新增分集入口",
            [copy.deepcopy(setup), _phase("add_episode_entry", "FC-NH-013: 新增分集入口", copy.deepcopy(ph_013["steps"]))],
            metadata=meta,
        ),
    )

    # 014: slice before save
    steps_014 = copy.deepcopy(create_steps[:7])
    _dump_yaml(
        WORKFLOWS_DIR / "naohai_FC_NH_014.yaml",
        _workflow(
            "naohai_FC_NH_014",
            "FC-NH-014: 新增分集字段",
            [copy.deepcopy(setup), _phase("create_new_episode", "FC-NH-014: 新增分集字段", steps_014)],
            metadata=meta,
        ),
    )

    # 015: full create+save
    _dump_yaml(
        WORKFLOWS_DIR / "naohai_FC_NH_015.yaml",
        _workflow(
            "naohai_FC_NH_015",
            "FC-NH-015: 新增分集提交",
            [copy.deepcopy(setup), _phase("create_new_episode", "FC-NH-015: 新增分集提交", copy.deepcopy(create_steps))],
            metadata=meta,
        ),
    )

    # 016: menu only
    steps_016 = copy.deepcopy(menu_steps[:6])
    _dump_yaml(
        WORKFLOWS_DIR / "naohai_FC_NH_016.yaml",
        _workflow(
            "naohai_FC_NH_016",
            "FC-NH-016: 分集卡片菜单",
            [copy.deepcopy(setup), _phase("episode_menu", "FC-NH-016: 分集卡片菜单", steps_016)],
            metadata=meta,
        ),
    )

    # 017: statistics only (menu open as setup)
    steps_017 = [copy.deepcopy(menu_steps[i]) for i in [0, 1, 6, 7, 8, 9, 10, 11, 12]]
    _dump_yaml(
        WORKFLOWS_DIR / "naohai_FC_NH_017.yaml",
        _workflow(
            "naohai_FC_NH_017",
            "FC-NH-017: 分集统计弹窗",
            [copy.deepcopy(setup), _phase("episode_statistics", "FC-NH-017: 分集统计弹窗", steps_017)],
            metadata=meta,
        ),
    )


def _generate_simple_split(
    src_filename: str,
    setup_phase_name: str,
    mapping: List[Tuple[int, str, str, str]],
) -> None:
    src = _load_workflow(WORKFLOWS_DIR / src_filename)
    meta = _metadata_without_name_desc_phases(src)
    phases_by_name = {p["name"]: p for p in src.get("phases", [])}
    setup = copy.deepcopy(phases_by_name[setup_phase_name])

    for num, out_name, desc, phase_key in mapping:
        steps = copy.deepcopy(phases_by_name[phase_key]["steps"])
        out = WORKFLOWS_DIR / f"naohai_FC_NH_{num:03d}.yaml"
        _dump_yaml(out, _workflow(out_name, desc, [copy.deepcopy(setup), _phase(phase_key, desc, steps)], metadata=meta))


def generate_from_character_management() -> None:
    _generate_simple_split(
        "naohai_FC_NH_018_character_management.yaml",
        "enter_character_section",
        [
            (18, "naohai_FC_NH_018", "FC-NH-018: 角色创建方式单选", "test_creation_method"),
            (19, "naohai_FC_NH_019", "FC-NH-019: 角色模型选择", "create_character_with_model"),
            (20, "naohai_FC_NH_020", "FC-NH-020: 角色卡片展示", "verify_character_card"),
            (21, "naohai_FC_NH_021", "FC-NH-021: 删除角色", "test_character_deletion"),
        ],
    )


def generate_from_scene_management() -> None:
    _generate_simple_split(
        "naohai_FC_NH_022_scene_management.yaml",
        "enter_scene_section",
        [
            (22, "naohai_FC_NH_022", "FC-NH-022: 场景创建方式单选", "test_scene_creation_method"),
            (23, "naohai_FC_NH_023", "FC-NH-023: 场景模型选择", "create_scene_with_model"),
            (24, "naohai_FC_NH_024", "FC-NH-024: 场景卡片展示", "verify_scene_card"),
            (25, "naohai_FC_NH_025", "FC-NH-025: 删除场景", "test_scene_deletion"),
        ],
    )


def generate_from_storyboard_management() -> None:
    _generate_simple_split(
        "naohai_FC_NH_026_storyboard_management.yaml",
        "enter_storyboard_page",
        [
            (26, "naohai_FC_NH_026", "FC-NH-026: 新增分镜", "add_storyboard_entry"),
            (27, "naohai_FC_NH_027", "FC-NH-027: 编辑分镜入口", "test_edit_storyboard"),
            (28, "naohai_FC_NH_028", "FC-NH-028: 编辑提示词入口", "test_edit_prompt"),
            (29, "naohai_FC_NH_029", "FC-NH-029: 分镜删除入口", "test_delete_storyboard"),
        ],
    )


def generate_from_ai_script_analysis() -> None:
    src = _load_workflow(WORKFLOWS_DIR / "naohai_FC_NH_030_ai_script_analysis.yaml")
    meta = _metadata_without_name_desc_phases(src)
    phases_by_name = {p["name"]: p for p in src.get("phases", [])}
    setup = copy.deepcopy(phases_by_name["enter_analysis_section"])

    script_input_steps = copy.deepcopy(phases_by_name["test_script_input"]["steps"])
    param_steps = phases_by_name["test_analysis_parameters"]["steps"]
    prompt_steps = phases_by_name["test_prompt_generation"]["steps"]

    def write(num: int, phase_name: str, desc: str, steps: List[Dict[str, Any]], include_script_input: bool = False) -> None:
        phases = [copy.deepcopy(setup)]
        if include_script_input:
            phases.append(_phase("script_input", "FC-NH-030: 剧本输入", copy.deepcopy(script_input_steps)))
        phases.append(_phase(phase_name, desc, steps))
        _dump_yaml(WORKFLOWS_DIR / f"naohai_FC_NH_{num:03d}.yaml", _workflow(f"naohai_FC_NH_{num:03d}", desc, phases, metadata=meta))

    write(30, "script_input", "FC-NH-030: 剧本输入", copy.deepcopy(script_input_steps))

    # 031: duration
    steps_031 = [copy.deepcopy(param_steps[i]) for i in [0, 1, 2]]
    steps_031.append({"action": "screenshot", "name": "duration_selected", "save_path": "screenshots/naohai/fc_nh_031_duration.png"})
    write(31, "analysis_duration", "FC-NH-031: 分析参数：目标时长", steps_031, include_script_input=True)

    # 032: suggested shots
    steps_032 = [copy.deepcopy(param_steps[i]) for i in [1, 2, 3, 4, 5]]
    steps_032.append({"action": "screenshot", "name": "suggested_shots", "save_path": "screenshots/naohai/fc_nh_032_suggest.png"})
    write(32, "suggested_shots", "FC-NH-032: 建议分镜数量", steps_032, include_script_input=True)

    # 033: start analysis (keep original phase steps)
    write(33, "start_analysis", "FC-NH-033: 开始分析按钮", copy.deepcopy(phases_by_name["start_analysis"]["steps"]), include_script_input=True)
    write(34, "analysis_result", "FC-NH-034: 分析产出", copy.deepcopy(phases_by_name["verify_analysis_result"]["steps"]), include_script_input=True)

    # 035: prompt generation
    steps_035 = [copy.deepcopy(prompt_steps[i]) for i in [0, 1, 2, 3]]
    steps_035.append({"action": "screenshot", "name": "prompt_list", "save_path": "screenshots/naohai/fc_nh_035_prompt_list.png"})
    write(35, "prompt_generation", "FC-NH-035: 提示词生成", steps_035, include_script_input=True)

    # 036: prompt edit (includes generation as setup)
    write(36, "prompt_editing", "FC-NH-036: 提示词展示与编辑", copy.deepcopy(prompt_steps), include_script_input=True)


def generate_from_binding() -> None:
    src = _load_workflow(WORKFLOWS_DIR / "naohai_FC_NH_037_character_scene_binding.yaml")
    meta = _metadata_without_name_desc_phases(src)
    phases_by_name = {p["name"]: p for p in src.get("phases", [])}
    setup = copy.deepcopy(phases_by_name["prepare_assets"])

    def write(num: int, phase_key: str, desc: str) -> None:
        steps = copy.deepcopy(phases_by_name[phase_key]["steps"])
        _dump_yaml(
            WORKFLOWS_DIR / f"naohai_FC_NH_{num:03d}.yaml",
            _workflow(f"naohai_FC_NH_{num:03d}", desc, [copy.deepcopy(setup), _phase(phase_key, desc, steps)], metadata=meta),
        )

    write(37, "test_character_binding", "FC-NH-037: 绑定多个角色（≤3）")
    write(38, "test_scene_binding", "FC-NH-038: 绑定1个场景")


def generate_from_image_material() -> None:
    _generate_simple_split(
        "naohai_FC_NH_039_image_material.yaml",
        "enter_material_section",
        [
            (39, "naohai_FC_NH_039", "FC-NH-039: 上传图片", "test_image_upload"),
            (40, "naohai_FC_NH_040", "FC-NH-040: 融合生图", "test_fusion_generation"),
            (41, "naohai_FC_NH_041", "FC-NH-041: 当前/历史 Tabs", "test_tab_switching"),
        ],
    )


def generate_from_video_creation() -> None:
    src = _load_workflow(WORKFLOWS_DIR / "naohai_FC_NH_042_video_creation.yaml")
    meta = _metadata_without_name_desc_phases(src)
    phases_by_name = {p["name"]: p for p in src.get("phases", [])}
    enter = copy.deepcopy(phases_by_name["enter_video_creation"])

    # 042
    _dump_yaml(
        WORKFLOWS_DIR / "naohai_FC_NH_042.yaml",
        _workflow("naohai_FC_NH_042", "FC-NH-042: 进入视频创作", [copy.deepcopy(enter)], metadata=meta),
    )

    # 043
    _dump_yaml(
        WORKFLOWS_DIR / "naohai_FC_NH_043.yaml",
        _workflow(
            "naohai_FC_NH_043",
            "FC-NH-043: 制作模式",
            [copy.deepcopy(enter), _phase("production_mode", "FC-NH-043: 制作模式", copy.deepcopy(phases_by_name["test_production_mode"]["steps"]))],
            metadata=meta,
        ),
    )

    # 044-048: slice configure_video_parameters into single focus steps
    cfg_steps = phases_by_name["configure_video_parameters"]["steps"]

    def write(num: int, phase_name: str, desc: str, steps: List[Dict[str, Any]]) -> None:
        _dump_yaml(
            WORKFLOWS_DIR / f"naohai_FC_NH_{num:03d}.yaml",
            _workflow(f"naohai_FC_NH_{num:03d}", desc, [copy.deepcopy(enter), _phase(phase_name, desc, steps)], metadata=meta),
        )

    write(
        44,
        "model_selection",
        "FC-NH-044: 模型选择",
        [copy.deepcopy(cfg_steps[i]) for i in [0, 1, 2, 3]]
        + [{"action": "screenshot", "name": "fc_nh_044", "save_path": "screenshots/naohai/fc_nh_044_model.png"}],
    )
    write(
        45,
        "video_name",
        "FC-NH-045: 视频名称",
        [copy.deepcopy(cfg_steps[i]) for i in [4, 5]]
        + [{"action": "screenshot", "name": "fc_nh_045", "save_path": "screenshots/naohai/fc_nh_045_name.png"}],
    )
    write(
        46,
        "video_description",
        "FC-NH-046: 描述",
        [copy.deepcopy(cfg_steps[i]) for i in [6, 7]]
        + [{"action": "screenshot", "name": "fc_nh_046", "save_path": "screenshots/naohai/fc_nh_046_desc.png"}],
    )
    write(
        47,
        "resolution",
        "FC-NH-047: 分辨率",
        [copy.deepcopy(cfg_steps[i]) for i in [8, 9]]
        + [{"action": "screenshot", "name": "fc_nh_047", "save_path": "screenshots/naohai/fc_nh_047_resolution.png"}],
    )
    write(
        48,
        "generation_count",
        "FC-NH-048: 生成数量",
        [copy.deepcopy(cfg_steps[i]) for i in [10, 11]]
        + [{"action": "screenshot", "name": "fc_nh_048", "save_path": "screenshots/naohai/fc_nh_048_quantity.png"}],
    )

    # 049/050: keep original test phases (avoid long waits)
    write(49, "video_selection", "FC-NH-049: 选择视频片段", copy.deepcopy(phases_by_name["test_video_selection"]["steps"]))
    write(50, "resource_export", "FC-NH-050: 导出资源包", copy.deepcopy(phases_by_name["test_resource_export"]["steps"]))


def main() -> None:
    generate_fc_004_to_011()
    generate_from_episode_management()
    generate_from_character_management()
    generate_from_scene_management()
    generate_from_storyboard_management()
    generate_from_ai_script_analysis()
    generate_from_binding()
    generate_from_image_material()
    generate_from_video_creation()


if __name__ == "__main__":
    main()

