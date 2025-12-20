#!/usr/bin/env python3
"""
统一FC目录文件命名
将naohai_04_*.yaml格式的文件重命名为naohai_FC_NH_###.yaml
"""

import re
from pathlib import Path
from typing import Dict, Optional

import yaml

# 定义映射关系：旧名 -> 新名
# 编号从051开始，避免与现有的002-050冲突
RENAME_MAPPING = {
    'naohai_04_nav_items_present.yaml': 'naohai_FC_NH_051.yaml',
    'naohai_05_ai_create_story_list_readonly.yaml': 'naohai_FC_NH_052.yaml',
    'naohai_06_ai_create_step_tabs_present.yaml': 'naohai_FC_NH_053.yaml',
    'naohai_07_story_list_add_entry_present.yaml': 'naohai_FC_NH_054.yaml',
    'naohai_08_open_create_modal_readonly.yaml': 'naohai_FC_NH_055.yaml',
    'naohai_09_create_modal_inputs_present.yaml': 'naohai_FC_NH_056.yaml',
    'naohai_10_create_modal_upload_present.yaml': 'naohai_FC_NH_057.yaml',
    'naohai_11_create_modal_ratios_present.yaml': 'naohai_FC_NH_058.yaml',
    'naohai_12_create_modal_next_button_present.yaml': 'naohai_FC_NH_059.yaml',
    'naohai_13_create_modal_default_step_readonly.yaml': 'naohai_FC_NH_060.yaml',
}

# 功能描述映射（用于生成目录）
FUNCTION_DESCRIPTION = {
    'naohai_FC_NH_051.yaml': '导航项展示验证',
    'naohai_FC_NH_052.yaml': 'AI创作只读验证',
    'naohai_FC_NH_053.yaml': 'Tab项存在验证',
    'naohai_FC_NH_054.yaml': '新增按钮存在验证',
    'naohai_FC_NH_055.yaml': '创建弹窗只读验证',
    'naohai_FC_NH_056.yaml': '输入框存在验证',
    'naohai_FC_NH_057.yaml': '上传组件存在验证',
    'naohai_FC_NH_058.yaml': '比例选项存在验证',
    'naohai_FC_NH_059.yaml': '下一步按钮存在验证',
    'naohai_FC_NH_060.yaml': '默认步骤只读验证',
}

_FC_FILE_RE = re.compile(r"^naohai_FC_NH_(\d{3})\.yaml$")


def _extract_fc_number(filename: str) -> Optional[int]:
    m = _FC_FILE_RE.match(filename)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _read_workflow_description(path: Path) -> str:
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        wf = (data or {}).get('workflow') or {}
        desc = wf.get('description')
        return str(desc) if desc else '未定义'
    except Exception:
        return '未定义'


def backup_directory(fc_dir: Path) -> Path:
    """备份FC目录"""
    backup_path = fc_dir.parent / 'fc_backup_before_rename'

    if backup_path.exists():
        print(f"备份目录已存在: {backup_path}")
        return backup_path

    import shutil
    shutil.copytree(fc_dir, backup_path)
    print(f"已备份到: {backup_path}")
    return backup_path

def rename_files(fc_dir: Path) -> None:
    """执行重命名操作"""
    success_count = 0
    error_count = 0

    print("\n开始重命名...")
    print("-" * 60)

    for old_name, new_name in RENAME_MAPPING.items():
        old_path = fc_dir / old_name
        new_path = fc_dir / new_name

        if old_path.exists():
            try:
                old_path.rename(new_path)
                print(f"✓ {old_name:40} -> {new_name}")
                success_count += 1
            except Exception as e:
                print(f"✗ {old_name:40} -> 失败: {e}")
                error_count += 1
        else:
            print(f"- {old_name:40} -> 文件不存在")
            error_count += 1

    print("-" * 60)
    print(f"重命名完成: 成功 {success_count}, 失败 {error_count}")

def generate_index(fc_dir: Path) -> None:
    """生成FC用例索引"""
    index_path = fc_dir / 'FC_INDEX.md'

    # 收集所有FC用例
    fc_files = sorted(fc_dir.glob('naohai_FC_NH_*.yaml'))

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('# FC用例索引\n\n')
        f.write('| 编号 | 文件名 | 描述 |\n')
        f.write('|------|--------|------|\n')

        for file_path in fc_files:
            filename = file_path.name
            fc_num = _extract_fc_number(filename)
            fc_id = f'FC-NH-{fc_num:03d}' if fc_num is not None else 'UNKNOWN'
            description = _read_workflow_description(file_path)
            f.write(f'| {fc_id} | {filename} | {description} |\n')

    print(f"\n索引已生成: {index_path}")

def verify_result(fc_dir: Path) -> None:
    """验证重命名结果"""
    print("\n验证结果...")

    # 统计各类文件
    fc_files = list(fc_dir.glob('naohai_FC_NH_*.yaml'))
    old_files = list(fc_dir.glob('naohai_0?_*.yaml'))

    print(f"FC-NH格式文件: {len(fc_files)}")
    print(f"旧格式文件: {len(old_files)}")

    if old_files:
        print("\n仍有未转换的旧格式文件:")
        for f in old_files:
            print(f"  - {f.name}")

    # 检查编号连续性
    fc_numbers = []
    for f in fc_files:
        num_str = f.stem.split('_')[3]  # naohai_FC_NH_XXX
        try:
            fc_numbers.append(int(num_str))
        except:
            pass

    if fc_numbers:
        min_num = min(fc_numbers)
        max_num = max(fc_numbers)
        expected = set(range(min_num, max_num + 1))
        actual = set(fc_numbers)
        missing = sorted(expected - actual)

        if missing:
            print(f"\n缺失的编号: {missing}")
        else:
            print(f"\n编号连续: {min_num:03d} - {max_num:03d}")

def main():
    """主函数"""
    fc_dir = Path('workflows/fc')

    if not fc_dir.exists():
        print(f"错误: 目录不存在 {fc_dir}")
        return

    print("=" * 60)
    print("FC目录命名统一工具")
    print("=" * 60)

    # 1. 备份
    backup_directory(fc_dir)

    # 2. 重命名
    rename_files(fc_dir)

    # 3. 生成索引
    generate_index(fc_dir)

    # 4. 验证
    verify_result(fc_dir)

    print("\n" + "=" * 60)
    print("操作完成！")
    print("\n建议下一步:")
    print("1. 运行批量更新脚本标准化内容")
    print("   python scripts/batch_update_workflows.py --type FC")
    print("2. 验证用例是否能正常执行")
    print("=" * 60)

if __name__ == '__main__':
    main()
