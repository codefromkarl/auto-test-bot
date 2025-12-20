#!/usr/bin/env python3
"""
批量更新workflow文件，添加标准字段并优化结构
"""

import os
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any

def load_template(template_name: str) -> Dict:
    """加载公共模板"""
    template_path = Path(f"scripts/templates/{template_name}.yaml")
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None

def update_at_workflow(file_path: Path) -> None:
    """更新AT系列用例"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 提取原始名称中的信息
    name = data.get('workflow', {}).get('name', '')
    description = data.get('workflow', {}).get('description', '')

    # 生成标准ID
    if 'story_list' in name:
        at_id = "AT-NH-001"
        entrypoint = "story_list"
        title = "剧本列表冒烟"
    elif 'create_story' in name:
        at_id = "AT-NH-002"
        entrypoint = "create_story"
        title = "创建剧本冒烟"
    elif 'storyboard' in name:
        at_id = "AT-NH-003"
        entrypoint = "storyboard"
        title = "分镜管理冒烟"
    else:
        at_id = "AT-NH-XXX"
        entrypoint = "unknown"
        title = name.replace('_', ' ').title()

    # 更新workflow结构
    if 'workflow' not in data:
        data['workflow'] = {}

    data['workflow']['id'] = at_id
    data['workflow']['kind'] = 'AT'
    data['workflow']['entrypoint'] = entrypoint
    data['workflow']['title'] = title
    data['workflow']['coverage_level'] = 'L0'  # AT通常L0
    data['workflow']['data_strategy'] = 'Readonly'

    # 保留原有的phases
    # phases结构保持不变

    return data

def update_fc_workflow(file_path: Path) -> Dict:
    """更新FC系列用例"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 从文件名提取ID
    filename = file_path.stem
    if 'FC_NH_' in filename:
        fc_id = filename.replace('naohai_', '').upper()
        feature_id = fc_id
    else:
        # 对于未命名的FC用例，需要根据内容判断
        phases = data.get('workflow', {}).get('phases', [])
        fc_id = "FC-NH-XXX"
        feature_id = fc_id

    # 确定entrypoint和coverage_level
    entrypoint = determine_entrypoint(data)
    coverage_level = determine_coverage_level(data)
    title = extract_title(data)

    # 更新workflow结构
    if 'workflow' not in data:
        data['workflow'] = {}

    data['workflow']['id'] = fc_id
    data['workflow']['kind'] = 'FC'
    data['workflow']['feature_id'] = feature_id
    data['workflow']['entrypoint'] = entrypoint
    data['workflow']['title'] = title
    data['workflow']['coverage_level'] = coverage_level
    data['workflow']['data_strategy'] = 'Readonly'  # 默认只读

    # 检查并优化前置步骤
    optimize_setup_phase(data)

    return data

def determine_entrypoint(data: Dict) -> str:
    """根据用例内容确定入口点"""
    phases = data.get('workflow', {}).get('phases', [])
    for phase in phases:
        steps = phase.get('steps', [])
        for step in steps:
            selector = step.get('selector', '')
            if 'text=剧本列表' in selector:
                return 'story_list'
            elif 'text=分镜管理' in selector:
                return 'storyboard'
            elif '角色' in selector:
                return 'character'
    return 'unknown'

def determine_coverage_level(data: Dict) -> str:
    """根据断言深度确定覆盖等级"""
    phases = data.get('workflow', {}).get('phases', [])
    has_input = False
    has_click = False
    has_wait = False

    for phase in phases:
        steps = phase.get('steps', [])
        for step in steps:
            action = step.get('action', '')
            if action == 'input':
                has_input = True
            elif action == 'click' and 'wait_for' not in str(step):
                has_click = True
            elif action == 'wait_for':
                has_wait = True

    # 判断覆盖等级
    if has_wait and not has_click and not has_input:
        return 'L0'  # 只等待元素出现
    elif has_click and not has_input:
        return 'L1'  # 点击交互
    elif has_input:
        return 'L2'  # 输入交互
    else:
        return 'L1'  # 默认

def extract_title(data: Dict) -> str:
    """提取用例标题"""
    description = data.get('workflow', {}).get('description', '')
    if description:
        # 从描述中提取标题
        if 'FC-NH-' in description:
            return description.split('：')[1] if '：' in description else description
        elif '冒烟' in description:
            return description
        else:
            return description[:50]  # 截取前50字符
    return "未命名用例"

def optimize_setup_phase(data: Dict) -> None:
    """优化setup阶段，减少重复"""
    phases = data.get('workflow', {}).get('phases', [])

    # 检查是否有setup阶段
    setup_found = False
    for phase in phases:
        if phase.get('name') == 'setup':
            setup_found = True
            # 检查setup步骤是否重复
            steps = phase.get('steps', [])
            if len(steps) > 5:  # 步骤过多，可能有重复
                # 标记需要优化
                phase['description'] = phase.get('description', '') + " [需要优化：考虑使用模板]"
            break

    # 如果没有setup，但第一个phase包含重复的前置，标记它
    if not setup_found and phases:
        first_phase = phases[0]
        if 'open_page' in str(first_phase):
            first_phase['name'] = 'setup'
            first_phase['description'] = '前置步骤 [需要优化：建议使用模板]'

def process_directory(dir_path: str, workflow_type: str) -> None:
    """处理指定目录下的所有workflow文件"""
    path = Path(dir_path)

    if not path.exists():
        print(f"目录不存在: {dir_path}")
        return

    # 查找所有yaml文件
    yaml_files = list(path.glob("*.yaml"))

    for file_path in yaml_files:
        print(f"\n处理文件: {file_path}")

        try:
            # 根据类型选择更新函数
            if workflow_type == 'AT':
                updated_data = update_at_workflow(file_path)
            elif workflow_type == 'FC':
                updated_data = update_fc_workflow(file_path)
            else:
                print(f"未知类型: {workflow_type}")
                continue

            # 备份原文件
            backup_path = file_path.with_suffix('.yaml.bak')
            file_path.rename(backup_path)
            print(f"  备份到: {backup_path}")

            # 写入更新后的文件
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(updated_data, f, allow_unicode=True, default_flow_style=False, indent=2)

            print(f"  ✓ 更新完成")

        except Exception as e:
            print(f"  ✗ 处理失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='批量更新workflow文件')
    parser.add_argument('--type', choices=['AT', 'FC', 'ALL'], default='ALL',
                      help='要更新的workflow类型')
    parser.add_argument('--dir', default='workflows',
                      help='workflow文件根目录')

    args = parser.parse_args()

    print("=" * 60)
    print("批量更新workflow文件")
    print("=" * 60)

    if args.type in ['AT', 'ALL']:
        print("\n处理AT系列用例...")
        process_directory(f"{args.dir}/at", 'AT')

    if args.type in ['FC', 'ALL']:
        print("\n处理FC系列用例...")
        process_directory(f"{args.dir}/fc", 'FC')

    print("\n" + "=" * 60)
    print("批量更新完成！")
    print("建议：")
    print("1. 检查.bak备份文件，确认无误后可删除")
    print("2. 运行测试验证更新后的用例")
    print("3. 使用公共模板进一步优化前置步骤")
    print("=" * 60)

if __name__ == '__main__':
    main()