#!/usr/bin/env python3
"""拆分FC-NH系列测试用例文件，每个FC-NH编号对应一个独立文件"""

import os
import re
import yaml
from pathlib import Path
from datetime import datetime

def extract_phase(workflow, fc_nh_number):
    """从workflow中提取特定FC-NH编号对应的phase"""
    for phase in workflow.get('phases', []):
        # 检查phase description是否包含目标FC-NH编号
        desc = phase.get('description', '')
        if f'FC-NH-{fc_nh_number}' in desc or f'FC-NH-0{fc_nh_number}' in desc:
            return phase
    return None

def create_single_test_file(original_file, fc_nh_number, phase_data, phase_index):
    """创建单个FC-NH测试文件"""
    # 构建新文件名
    new_filename = f"naohai_FC_NH_{fc_nh_number:03d}_{phase['name'].replace(' ', '_')}.yaml"
    new_filepath = original_file.parent / new_filename

    # 创建新的workflow
    new_workflow = {
        'name': f"naohai_FC_NH_{fc_nh_number:03d}_{phase['name'].replace(' ', '_')}",
        'description': phase.get('description', ''),
        'phases': [phase]
    }

    # 写入新文件
    with open(new_filepath, 'w', encoding='utf-8') as f:
        yaml.dump(new_workflow, f, default_flow_style=False, allow_unicode=True, indent=2)

    print(f"Created: {new_filename}")
    return new_filepath

def split_file(filepath):
    """拆分一个包含多个FC-NH的文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        workflow = yaml.safe_load(f)

    created_files = []
    filename = filepath.stem

    # 提取文件中的所有FC-NH编号
    fc_nh_numbers = []

    # 从description和phases中查找FC-NH编号
    content = str(workflow)
    matches = re.findall(r'FC-NH-(\d+)', content)
    fc_nh_numbers = sorted(set(int(m) for m in matches))

    if not fc_nh_numbers:
        print(f"No FC-NH numbers found in {filename}")
        return created_files

    print(f"Splitting {filename} with FC-NH numbers: {fc_nh_numbers}")

    # 为每个FC-NH编号创建独立文件
    for fc_nh_number in fc_nh_numbers:
        # 查找对应的phase
        phase = extract_phase(workflow, fc_nh_number)
        if phase:
            new_file = create_single_test_file(filepath, fc_nh_number, phase, 0)
            created_files.append(new_file)
        else:
            print(f"Warning: Could not find phase for FC-NH-{fc_nh_number:03d}")

    return created_files

def main():
    """主函数"""
    workflows_dir = Path("workflows")

    # 查找需要拆分的FC-NH文件
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

        print(f"\nProcessing: {filename}")

        # 备份原文件
        backup_file = backup_dir / filename
        if not backup_file.exists():
            import shutil
            shutil.copy2(filepath, backup_file)
            print(f"Backed up to: {backup_file}")

        # 拆分文件
        created_files = split_file(filepath)
        total_created += len(created_files)

    # 统计信息
    print(f"\n=== Split Summary ===")
    print(f"Files processed: {len(files_to_split)}")
    print(f"Total FC-NH test files created: {total_created}")

    # 列出所有AT-NH文件
    at_nh_files = list(workflows_dir.glob("naohai_[0-9][0-9]*.yaml"))
    at_nh_files = [f for f in at_nh_files if 'FC_NH_' not in f.name]
    print(f"Existing AT-NH files: {len(at_nh_files)}")

    print(f"\nTotal test files after split: {len(at_nh_files) + total_created}")

if __name__ == "__main__":
    main()