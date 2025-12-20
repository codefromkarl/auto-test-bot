#!/usr/bin/env python3
"""拆分FC-NH系列测试用例文件 - 修正版本（处理YAML格式问题）"""

import os
import re
import yaml
import shutil
from pathlib import Path

def map_phase_name(fc_nh_number):
    """根据FC-NH编号返回对应的phase名称和描述"""
    mapping = {
        # Step 1: 剧本列表
        '002': ('story_card_display', 'FC-NH-002: 剧本卡片展示测试'),
        '003': ('story_card_menu', 'FC-NH-003: 剧本卡片菜单操作测试'),
        '012': ('create_story_complete', 'FC-NH-012: 完整创建剧本测试'),

        # Step 2: 分集、角色和场景
        '013': ('add_episode_entry', 'FC-NH-013: 新增分集入口'),
        '014': ('create_new_episode', 'FC-NH-014: 新增分集字段'),
        '015': ('save_episode', 'FC-NH-015: 新增分集提交'),
        '016': ('episode_menu', 'FC-NH-016: 分集卡片菜单'),
        '017': ('episode_statistics', 'FC-NH-017: 分集统计弹窗'),

        '018': ('character_creation_method', 'FC-NH-018: 角色创建方式单选'),
        '019': ('create_character_with_model', 'FC-NH-019: 角色模型选择'),
        '020': ('verify_character_card', 'FC-NH-020: 角色卡片展示'),
        '021': ('delete_character', 'FC-NH-021: 删除角色'),

        '022': ('scene_creation_method', 'FC-NH-022: 场景创建方式单选'),
        '023': ('create_scene_with_model', 'FC-NH-023: 场景模型选择'),
        '024': ('verify_scene_card', 'FC-NH-024: 场景卡片展示'),
        '025': ('delete_scene', 'FC-NH-025: 删除场景'),

        # Step 3: 分镜管理
        '026': ('add_storyboard_entry', 'FC-NH-026: 新增分镜'),
        '027': ('edit_storyboard', 'FC-NH-027: 编辑分镜入口'),
        '028': ('edit_prompt', 'FC-NH-028: 编辑提示词入口'),
        '029': ('delete_storyboard', 'FC-NH-029: 分镜删除入口'),

        '030': ('script_input', 'FC-NH-030: 剧本输入'),
        '031': ('analysis_parameters', 'FC-NH-031: 分析参数：目标时长'),
        '032': ('suggested_shots', 'FC-NH-032: 建议分镜数量'),
        '033': ('start_analysis', 'FC-NH-033: 开始分析按钮'),
        '034': ('analysis_result', 'FC-NH-034: 分析产出'),
        '035': ('prompt_generation', 'FC-NH-035: 提示词生成'),
        '036': ('prompt_editing', 'FC-NH-036: 提示词展示与编辑'),

        # Step 4: 分镜绑定
        '037': ('character_binding', 'FC-NH-037: 绑定多个角色'),
        '038': ('scene_binding', 'FC-NH-038: 绑定场景'),

        # Step 5: 图片素材
        '039': ('image_upload', 'FC-NH-039: 上传图片'),
        '040': ('fusion_generation', 'FC-NH-040: 融合生图'),
        '041': ('tab_switching', 'FC-NH-041: 当前/历史标签切换'),

        # Step 6: 视频创作
        '042': ('enter_video_creation', 'FC-NH-042: 进入视频创作'),
        '043': ('production_mode', 'FC-NH-043: 制作模式'),
        '044': ('model_selection', 'FC-NH-044: 模型选择'),
        '045': ('video_name', 'FC-NH-045: 视频名称'),
        '046': ('video_description', 'FC-NH-046: 描述'),
        '047': ('resolution', 'FC-NH-047: 分辨率'),
        '048': ('generation_count', 'FC-NH-048: 生成数量'),
        '049': ('video_selection', 'FC-NH-049: 选择视频片段'),
        '050': ('resource_export', 'FC-NH-050: 导出资源包'),
    }

    return mapping.get(fc_nh_number, (f'fc_nh_{fc_nh_number}', f'FC-NH-{fc_nh_number}'))

def extract_phase_steps(original_workflow, fc_nh_number):
    """从原始workflow中提取特定FC-NH编号对应的steps"""
    phases = original_workflow.get('phases', [])
    target_steps = []

    for phase in phases:
        desc = phase.get('description', '')
        phase_name = phase.get('name', '')
        steps = phase.get('steps', [])

        # 如果phase描述或名称包含目标FC-NH编号
        if f'FC-NH-{fc_nh_number}' in desc or f'FC-NH-0{fc_nh_number}' in desc:
            target_steps = steps
            break
        # 或者steps中包含相关描述
        for step in steps:
            step_str = str(step)
            if f'FC-NH-{fc_nh_number}' in step_str or f'FC-NH-0{fc_nh_number}' in step_str:
                target_steps = steps
                break

    return target_steps

def create_single_test_file(fc_nh_number, phase_name, phase_desc, steps):
    """创建单个FC-NH测试文件"""
    filename = f"naohai_FC_NH_{fc_nh_number:03d}.yaml"
    filepath = Path("workflows") / filename

    # 创建新的workflow
    workflow = {
        'name': f"naohai_FC_NH_{fc_nh_number:03d}",
        'description': phase_desc,
        'phases': [{
            'name': phase_name,
            'description': phase_desc,
            'steps': steps
        }]
    }

    # 写入新文件
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(workflow, f, default_flow_style=False, allow_unicode=True, indent=2)

    print(f"Created: {filename}")
    return filepath

def split_workflow(filepath):
    """拆分一个包含多个FC-NH编号的文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        original_workflow = yaml.safe_load(f)

    # 提取文件中的所有FC-NH编号
    content = str(original_workflow)
    matches = re.findall(r'FC-NH-(\d+)', content)
    fc_nh_numbers = sorted(set(int(m) for m in matches))

    if not fc_nh_numbers:
        print(f"No FC-NH numbers found in {filepath.name}")
        return []

    print(f"Splitting {filepath.name} with FC-NH numbers: {fc_nh_numbers}")
    created_files = []

    # 为每个FC-NH编号创建独立文件
    for fc_nh_number in fc_nh_numbers:
        phase_name, phase_desc = map_phase_name(fc_nh_number)

        # 提取对应的steps
        steps = extract_phase_steps(original_workflow, fc_nh_number)

        if steps:
            created_file = create_single_test_file(fc_nh_number, phase_name, phase_desc, steps)
            created_files.append(created_file)
        else:
            print(f"Warning: Could not find steps for FC-NH-{fc_nh_number:03d}")

    return created_files

def main():
    """主函数"""
    workflows_dir = Path("workflows")

    # 需要拆分的文件（带_fixed后缀）
    files_to_split = [
        "naohai_FC_NH_013_episode_management_fixed.yaml",
        "naohai_FC_NH_018_character_management_fixed.yaml",
        "naohai_FC_NH_022_scene_management_fixed.yaml",
        "naohai_FC_NH_026_storyboard_management_fixed.yaml",
        "naohai_FC_NH_030_ai_script_analysis_fixed.yaml",
        "naohai_FC_NH_037_character_scene_binding_fixed.yaml",
        "naohai_FC_NH_039_image_material_fixed.yaml",
        "naohai_FC_NH_042_video_creation_fixed.yaml"
    ]

    # 创建backup目录
    backup_dir = Path("workflows/backup")
    backup_dir.mkdir(exist_ok=True)

    total_created = 0

    for filename in files_to_split:
        filepath = workflows_dir / filename

        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue

        print(f"\n{'='*50}")
        print(f"Processing: {filename}")
        print(f"{'='*50}")

        # 备份原文件
        backup_file = backup_dir / filename
        if not backup_file.exists():
            shutil.copy2(filepath, backup_file)
            print(f"Backed up to: backup/{filename}")

        # 拆分文件
        created_files = split_workflow(filepath)
        total_created += len(created_files)

        # 删除原文件
        if created_files:
            os.remove(filepath)
            print(f"Removed original file: {filename}")

    # 统计信息
    print(f"\n{'='*50}")
    print("SPLIT SUMMARY")
    print(f"{'='*50}")
    print(f"Files processed: {len(files_to_split)}")
    print(f"Total FC-NH test files created: {total_created}")

    # 列出所有文件
    all_yaml_files = list(workflows_dir.glob("naohai_FC_NH_*.yaml"))
    at_nh_files = [f for f in all_yaml_files if not 'FC_NH_' in f.name]
    fc_nh_files = [f for f in all_yaml_files if 'FC_NH_' in f.name]

    print(f"\nExisting AT-NH files: {len(at_nh_files)}")
    print(f"FC-NH files: {len(fc_nh_files)}")
    print(f"\nTotal test files: {len(at_nh_files) + len(fc_nh_files)}")

    # 显示新创建的文件列表
    if total_created > 0:
        print("\nNewly created FC-NH files:")
        for f in sorted(fc_nh_files, key=lambda x: int(re.search(r'(\d+)', x.name).group(1))):
            print(f"  - {f.name}")

if __name__ == "__main__":
    main()