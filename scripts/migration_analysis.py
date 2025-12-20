#!/usr/bin/env python3
"""
分析FC脆弱性，选择优先迁移目标
"""

import sys
import os
from pathlib import Path
from collections import Counter
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def analyze_selector_patterns():
    """分析selector模式和使用频率"""
    fc_dir = Path(__file__).parent.parent / "workflows/fc"

    # 统计高频selector
    selector_counter = Counter()
    fc_selector_count = {}
    high_vulnerability_fcs = []

    for yaml_file in fc_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)

            selectors = []
            # 遍历所有步骤提取selector
            if 'workflow' in workflow:
                for phase in workflow['workflow'].get('phases', []):
                    for step in phase.get('steps', []):
                        if 'selector' in step:
                            selectors.append(step['selector'])
                            selector_counter[step['selector']] += 1

            fc_selector_count[yaml_file.name] = len(selectors)

            # 高脆弱性标准：selector数量多，且包含高频脆弱selector
            vulnerability_score = len(selectors)
            vulnerable_selectors = [s for s in selectors if any(pattern in s for pattern in [
                '.nav-routerTo-item:has-text("AI创作")',
                'div.list-item:not(.add-item)',
                'text=',  # 纯文本定位
                ':first-child',  # 位置依赖
                ':nth-child'   # 位置依赖
            ])]

            vulnerability_score += len(vulnerable_selectors) * 2

            high_vulnerability_fcs.append({
                'file': yaml_file.name,
                'selectors': selectors,
                'vulnerable_selectors': vulnerable_selectors,
                'score': vulnerability_score,
                'description': workflow.get('workflow', {}).get('description', '')
            })

        except Exception as e:
            print(f"解析文件失败 {yaml_file}: {e}")

    return selector_counter, high_vulnerability_fcs


def select_migration_targets(high_vulnerability_fcs, count=8):
    """选择迁移目标"""
    # 按脆弱性评分排序
    sorted_fcs = sorted(high_vulnerability_fcs, key=lambda x: x['score'], reverse=True)

    # 选择覆盖不同业务场景的FC
    selected_fcs = []
    business_areas = set()

    for fc in sorted_fcs:
        # 分析业务领域
        area = analyze_business_area(fc['description'])

        # 确保覆盖不同业务领域
        if area not in business_areas or len(selected_fcs) < count // 2:
            selected_fcs.append(fc)
            business_areas.add(area)

            if len(selected_fcs) >= count:
                break

    return selected_fcs


def analyze_business_area(description):
    """分析FC的业务领域"""
    if '卡片' in description or '菜单' in description:
        return 'ui_interaction'
    elif '角色' in description or '绑定' in description:
        return 'character_management'
    elif '分镜' in description:
        return 'storyboard'
    elif '创建' in description or '新建' in description:
        return 'creation_flow'
    elif '视频' in description:
        return 'video_generation'
    else:
        return 'other'


def main():
    print("🔍 分析FC脆弱性和选择迁移目标\n")

    # 分析selector模式
    selector_counter, high_vulnerability_fcs = analyze_selector_patterns()

    print("📊 高频脆弱Selector (Top 10):")
    for selector, count in selector_counter.most_common(10):
        vulnerability_level = "🔴 高" if any(pattern in selector for pattern in [
            ':has-text', 'div.list-item:not', 'text='
        ]) else "🟡 中"
        print(f"  {vulnerability_level} {count}次: {selector}")

    print(f"\n📋 分析了 {len(high_vulnerability_fcs)} 个FC")

    # 选择迁移目标
    selected_fcs = select_migration_targets(high_vulnerability_fcs, count=8)

    print(f"\n🎯 选择迁移目标 (8个高优先级FC):")
    total_selectors = 0
    total_vulnerable = 0

    for i, fc in enumerate(selected_fcs, 1):
        total_selectors += len(fc['selectors'])
        total_vulnerable += len(fc['vulnerable_selectors'])
        area = analyze_business_area(fc['description'])

        print(f"  {i}. {fc['file']} (评分: {fc['score']})")
        print(f"     描述: {fc['description']}")
        print(f"     领域: {area}")
        print(f"     Selectors: {len(fc['selectors'])} (脆弱: {len(fc['vulnerable_selectors'])})")
        print(f"     脆弱示例: {fc['vulnerable_selectors'][:2]}")
        print()

    print(f"📈 迁移效果预估:")
    print(f"  总Selector数: {total_selectors}")
    print(f"  脆弱Selector数: {total_vulnerable}")
    print(f"  预期减少: {total_vulnerable} 个硬编码selector")
    print(f"  预期收敛为: {8} 个语义Action")

    # 保存迁移目标
    migration_targets = {
        'selected_fcs': selected_fcs,
        'migration_plan': generate_migration_plan(selected_fcs),
        'success_metrics': {
            'selectors_to_reduce': total_selectors,
            'vulnerable_selectors_to_eliminate': total_vulnerable,
            'semantic_actions_needed': 8,
            'business_areas_covered': list(set(analyze_business_area(fc['description']) for fc in selected_fcs))
        }
    }

    output_file = Path(__file__).parent.parent / "docs" / "rf_migration_targets.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(migration_targets, f, allow_unicode=True, default_flow_style=False)

    print(f"📁 迁移计划已保存到: {output_file}")
    return 0


def generate_migration_plan(selected_fcs):
    """生成迁移计划"""
    plan = {
        'phase_1': ['naohai_FC_NH_002', 'naohai_FC_NH_003', 'naohai_FC_NH_037'],  # 最高优先级
        'phase_2': ['naohai_FC_NH_015', 'naohai_FC_NH_035', 'naohai_FC_NH_051'],  # 中等优先级
        'phase_3': ['naohai_FC_NH_012', 'naohai_FC_NH_052']  # 验证和补充
    }
    return plan


if __name__ == "__main__":
    sys.exit(main())