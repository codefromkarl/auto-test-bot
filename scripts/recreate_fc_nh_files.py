#!/usr/bin/env python3
"""重新创建FC-NH系列测试用例文件，确保内容正确"""

import os
import re
import yaml
import shutil
from pathlib import Path

def create_fc_nh_file(fc_nh_number, phase_data):
    """创建单个FC-NH测试文件"""
    filename = f"naohai_FC_NH_{fc_nh_number:03d}.yaml"
    filepath = Path("workflows") / filename

    # 基础的前置步骤（进入AI创作、剧本列表等）
    base_steps = [
        {"action": "open_page", "url": "${test.url}", "timeout": "${test.timeout.page_load}"},
        {"action": "wait_for", "condition": {"selector": "body", "visible": True}, "timeout": "${test.timeout.element_load}"},
        {"action": "assert_logged_in"},
        {"action": "click", "selector": '.nav-routerTo-item:has-text("AI创作")', "timeout": "${test.timeout.element_load}"},
        {"action": "wait_for", "condition": {"selector": "text=剧本列表", "visible": True}, "timeout": "${test.timeout.page_load}"}
    ]

    # 根据FC-NH编号调整内容
    if fc_nh_number in ['002', '003']:
        # Step 1的基础步骤
        steps = base_steps + [
            {"action": "screenshot", "name": f"fc_nh_{fc_nh_number}_setup", "save_path": f"screenshots/naohai/fc_nh_{fc_nh_number}_setup.png"}
        ]

        if fc_nh_number == '002':
            steps.extend([
                {"action": "wait_for", "condition": {"selector": "div.list-item:not(.add-item)", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": "story_cards_display", "save_path": f"screenshots/naohai/fc_nh_{fc_nh_number}_story_cards_display.png"}
            ])

        if fc_nh_number == '003':
            steps.extend([
                {"action": "wait_for", "condition": {"selector": "div.list-item:not(.add-item) .menu, div.list-item:not(.add-item) .more, div.list-item:not(.add-item) .ellipsis, div.list-item:not(.add-item) .dropdown", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "click", "selector": "div.list-item:not(.add-item) .menu, div.list-item:not(.add-item) .more, div.list-item:not(.add-item) .ellipsis, div.list-item:not(.add-item) .dropdown", "timeout": "${test.timeout.element_load}"},
                {"action": "wait_for", "condition": {"selector": ".dropdown-menu, .menu-list", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": f"fc_nh_{fc_nh_number}_menu_open", "save_path": f"screenshots/naohai/fc_nh_{fc_nh_number}_menu_open.png"}
            ])

    elif fc_nh_number == '012':
        # 创建剧本的完整流程
        steps = base_steps + [
            {"action": "click", "selector": "div.list-item.add-item", "timeout": "${test.timeout.element_load}"},
            {"action": "wait_for", "condition": {"selector": "text=基础信息", "visible": True}, "timeout": "${test.timeout.element_load}"},
            {"action": "screenshot", "name": f"fc_nh_{fc_nh_number}_modal_open", "save_path": f"screenshots/naohai/fc_nh_{fc_nh_number}_modal_open.png"},
            {"action": "input", "selector": "input[placeholder*=\"剧本名称\"], input[placeholder*=\"名称\"]", "text": "测试剧本_${timestamp}", "clear": True},
            {"action": "input", "selector": "textarea", "text": "这是一个自动化测试创建的剧本，用于验证完整创建流程。", "clear": True},
            {"action": "click", "selector": "text=16:9", "timeout": "${test.timeout.element_load}"},
            {"action": "screenshot", "name": f"fc_nh_{fc_nh_number}_basic_filled", "save_path": f"screenshots/naohai/fc_nh_{fc_nh_number}_basic_filled.png"},
            {"action": "click", "selector": "text=下一步", "timeout": "${test.timeout.element_load}"},
            {"action": "wait_for", "condition": {"selector": "text=画风", "visible": True}, "timeout": "${test.timeout.page_load}"},
            {"action": "click", "selector": ".style-card:first-child, .style-option:first-child, .art-style-item:first-child", "timeout": "${test.timeout.element_load}"},
            {"action": "screenshot", "name": f"fc_nh_{fc_nh_number}_style_selected", "save_path": f"screenshots/naohai/fc_nh_{fc_nh_number}_style_selected.png"},
            {"action": "click", "selector": "text=创建剧本, text=创建, text=提交", "timeout": "${test.timeout.element_load}"}
        ]

    else:
        # 其他功能点使用传入的数据
        steps = base_steps + phase_data.get('steps', [])

    # 创建workflow
    workflow = {
        "name": f"naohai_FC_NH_{fc_nh_number:03d}",
        "description": f"FC-NH-{fc_nh_number}: {phase_data.get('description', '')}",
        "phases": [{
            "name": phase_data.get('name', ''),
            "description": phase_data.get('description', ''),
            "steps": steps
        }]
    }

    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(workflow, f, default_flow_style=False, allow_unicode=True, indent=2)

    print(f"Created: {filename}")
    return filepath

def main():
    """主函数"""
    # 删除已有的FC-NH文件，重新创建
    workflows_dir = Path("workflows")

    # 创建backup
    backup_dir = Path("workflows/backup_v2")
    backup_dir.mkdir(exist_ok=True)

    # 备份现有FC-NH文件
    for file in workflows_dir.glob("naohai_FC_NH_[0-9]*.yaml"):
        if file.exists():
            backup_file = backup_dir / file.name
            shutil.copy2(file, backup_file)
            print(f"Backed up: {file.name}")
            os.remove(file)

    # Phase mapping with detailed steps
    phase_configs = {
        # Step 1
        '002': {
            'name': 'verify_story_cards',
            'description': 'FC-NH-002: 剧本卡片展示测试'
        },
        '003': {
            'name': 'test_menu_operations',
            'description': 'FC-NH-003: 剧本卡片菜单操作测试'
        },
        '012': {
            'name': 'create_story_complete',
            'description': 'FC-NH-012: 完整创建剧本测试'
        },

        # Step 2 - 简化版（只保留前5个）
        '013': {
            'name': 'add_episode_entry',
            'description': 'FC-NH-013: 新增分集入口',
            'steps': [
                {"action": "wait_for", "condition": {"selector": "text=添加片段, text=新增片段, text=添加分集, text=新增分集, button:has-text('+'), .add-episode", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": "fc_nh_013_add_entry", "save_path": "screenshots/naohai/fc_nh_013_add_entry.png"}
            ]
        },
        '018': {
            'name': 'test_character_creation',
            'description': 'FC-NH-018: 角色创建测试',
            'steps': [
                {"action": "wait_for", "condition": {"selector": "text=创建角色, button:has-text('+角色'), .add-character", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "click", "selector": "text=创建角色, button:has-text('+角色'), .add-character", "timeout": "${test.timeout.element_load}"},
                {"action": "wait_for", "condition": {"selector": ".character-form, .modal, .dialog", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "wait_for", "condition": {"selector": "text=模型生成, input[type='radio'][value*='model']", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "click", "selector": "text=模型生成, input[type='radio'][value*='model']", "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": "fc_nh_018_creation_methods", "save_path": "screenshots/naohai/fc_nh_018_creation_methods.png"}
            ]
        },

        # Step 3
        '026': {
            'name': 'add_storyboard_entry',
            'description': 'FC-NH-026: 新增分镜测试',
            'steps': [
                {"action": "wait_for", "condition": {"selector": "text=新增分镜, button:has-text('+分镜'), .add-storyboard", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "click", "selector": "text=新增分镜, button:has-text('+分镜'), .add-storyboard", "timeout": "${test.timeout.element_load}"},
                {"action": "wait_for", "condition": {"selector": ".storyboard-form, .modal, .dialog", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": "fc_nh_026_form", "save_path": "screenshots/naohai/fc_nh_026_form.png"}
            ]
        },
        '030': {
            'name': 'test_script_input',
            'description': 'FC-NH-030: 测试剧本输入',
            'steps': [
                {"action": "wait_for", "condition": {"selector": "textarea[placeholder*='剧本'], .script-input, .analysis-input", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": "fc_nh_030_script_input", "save_path": "screenshots/naohai/fc_nh_030_script_input.png"}
            ]
        },

        # Step 4
        '037': {
            'name': 'test_character_binding',
            'description': 'FC-NH-037: 测试分镜绑定多个角色',
            'steps': [
                {"action": "wait_for", "condition": {"selector": ".binding-panel, .character-binding", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": "fc_nh_037_binding_panel", "save_path": "screenshots/naohai/fc_nh_037_binding_panel.png"}
            ]
        },

        # Step 5
        '039': {
            'name': 'test_image_upload',
            'description': 'FC-NH-039: 测试图片上传',
            'steps': [
                {"action": "wait_for", "condition": {"selector": "text=上传图片, .upload-image, button:has-text('上传')", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "screenshot", "name": "fc_nh_039_upload_interface", "save_path": "screenshots/naohai/fc_nh_039_upload_interface.png"}
            ]
        },

        # Step 6
        '042': {
            'name': 'enter_video_creation',
            'description': 'FC-NH-042: 进入视频创作',
            'steps': [
                {"action": "wait_for", "condition": {"selector": "text=视频创作, .video-create, button:has-text('视频')", "visible": True}, "timeout": "${test.timeout.element_load}"},
                {"action": "click", "selector": "text=视频创作, .video-create, button:has-text('视频')", "timeout": "${test.timeout.element_load}"},
                {"action": "wait_for", "condition": {"selector": "text=视频创作, .video-creation-page", "visible": True}, "timeout": "${test.timeout.page_load}"},
                {"action": "screenshot", "name": "fc_nh_042_video_page", "save_path": "screenshots/naohai/fc_nh_042_video_page.png"}
            ]
        }
    }

    # 创建主要FC-NH文件
    created_count = 0
    for fc_nh_number, config in phase_configs.items():
        if create_fc_nh_file(fc_nh_number, config):
            created_count += 1

    print(f"\n{'='*50}")
    print(f"Created {created_count} FC-NH test files")

    # 统计总数
    at_nh_files = list(workflows_dir.glob("naohai_[0-9][0-9]*.yaml"))
    fc_nh_files = [f for f in at_nh_files if 'FC-NH_' in f.name]
    other_files = [f for f in at_nh_files if 'FC-NH_' not in f.name]

    print(f"\nExisting AT-NH files: {len(other_files)}")
    print(f"FC-NH files: {len(fc_nh_files)}")
    print(f"Total test files: {len(fc_nh_files) + created_count}")

if __name__ == "__main__":
    main()