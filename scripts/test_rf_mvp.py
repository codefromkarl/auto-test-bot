#!/usr/bin/env python3
"""
测试RF MVP版本的可行性
验证语义Action的创建和执行
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.action import Action
from models.context import Context
from models.semantic_action import SemanticAction


def test_semantic_action_creation():
    """测试语义Action的创建"""
    print("🔧 测试语义Action创建...")

    try:
        # 测试rf_enter_ai_creation
        action1 = Action.create('rf_enter_ai_creation', {})
        print(f"✅ rf_enter_ai_creation: {type(action1).__name__}")

        # 测试rf_ensure_story_exists
        action2 = Action.create('rf_ensure_story_exists', {})
        print(f"✅ rf_ensure_story_exists: {type(action2).__name__}")

        # 测试rf_open_first_story_card
        action3 = Action.create('rf_open_first_story_card', {})
        print(f"✅ rf_open_first_story_card: {type(action3).__name__}")

        return True

    except Exception as e:
        print(f"❌ 语义Action创建失败: {e}")
        return False


def test_atomic_action_composition():
    """测试语义Action的原子Action组合"""
    print("\n🧩 测试原子Action组合...")

    try:
        # 创建语义Action
        semantic_action = Action.create('rf_enter_ai_creation', {})

        # 获取组合的原子Action
        atomic_actions = semantic_action.get_atomic_actions()

        print(f"✅ 原子Action数量: {len(atomic_actions)}")
        for i, action in enumerate(atomic_actions):
            print(f"  {i+1}. {action.get_step_name()}: {action.params}")

        return True

    except Exception as e:
        print(f"❌ 原子Action组合失败: {e}")
        return False


def test_workflow_yaml_parsing():
    """测试RF版本YAML工作流的解析"""
    print("\n📄 测试RF工作流YAML解析...")

    try:
        import yaml
        rf_workflow_path = Path(__file__).parent.parent / "workflows/fc/naohai_FC_NH_002_rf.yaml"

        if not rf_workflow_path.exists():
            print(f"❌ RF工作流文件不存在: {rf_workflow_path}")
            return False

        with open(rf_workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        print("✅ YAML解析成功")
        print(f"  名称: {workflow['workflow']['name']}")
        print(f"  版本: {workflow['workflow'].get('version', 'N/A')}")
        print(f"  suite_setup步骤: {len(workflow['workflow']['suite_setup'])}")

        # 检查RF语义Action
        rf_actions = []
        for step in workflow['workflow']['suite_setup']:
            if step['action'].startswith('rf_'):
                rf_actions.append(step['action'])

        for phase in workflow['workflow']['phases']:
            for step in phase['steps']:
                if step['action'].startswith('rf_'):
                    rf_actions.append(step['action'])

        print(f"  RF语义Action: {rf_actions}")

        return True

    except Exception as e:
        print(f"❌ YAML解析失败: {e}")
        return False


def test_context_integration():
    """测试Context状态管理"""
    print("\n🧠 测试Context状态管理...")

    try:
        # 创建Context
        context = Context()

        # 执行语义Action
        semantic_action = Action.create('rf_enter_ai_creation', {})
        result_context = semantic_action.execute(context)

        # 检查状态设置
        print(f"✅ Context创建成功")
        print(f"  进入AI创作标志: {result_context.get_data('entering_ai_creation')}")
        print(f"  AI创作页面标志: {result_context.get_data('ai_creation_page')}")
        print(f"  当前模块: {result_context.get_data('current_module')}")

        return True

    except Exception as e:
        print(f"❌ Context集成失败: {e}")
        return False


def compare_old_vs_rf():
    """对比原版和RF版本的区别"""
    print("\n📊 原版 vs RF版本对比:")

    try:
        import yaml

        # 原版
        old_path = Path(__file__).parent.parent / "workflows/fc/naohai_FC_NH_002.yaml"
        with open(old_path, 'r', encoding='utf-8') as f:
            old_workflow = yaml.safe_load(f)

        # RF版
        rf_path = Path(__file__).parent.parent / "workflows/fc/naohai_FC_NH_002_rf.yaml"
        with open(rf_path, 'r', encoding='utf-8') as f:
            rf_workflow = yaml.safe_load(f)

        # 统计selector数量
        old_selectors = []
        rf_selectors = []

        for phase in old_workflow['workflow']['phases']:
            for step in phase['steps']:
                if 'selector' in step:
                    old_selectors.append(step['selector'])

        for phase in rf_workflow['workflow']['phases']:
            for step in phase['steps']:
                if 'selector' in step:
                    rf_selectors.append(step['selector'])

        print(f"  原版selector数量: {len(old_selectors)}")
        print(f"  RF版selector数量: {len(rf_selectors)}")
        print(f"  减少了 {len(old_selectors) - len(rf_selectors)} 个硬编码selector")

        if old_selectors:
            print("  原版selectors:")
            for i, selector in enumerate(old_selectors[:3], 1):
                print(f"    {i}. {selector}")

        print("  RF版语义Actions:")
        for step in rf_workflow['workflow']['suite_setup']:
            print(f"    - {step['action']}")
        for phase in rf_workflow['workflow']['phases']:
            for step in phase['steps']:
                if step['action'].startswith('rf_'):
                    print(f"    - {step['action']}")

        return True

    except Exception as e:
        print(f"❌ 对比分析失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 RF MVP可行性测试开始\n")

    tests = [
        test_semantic_action_creation,
        test_atomic_action_composition,
        test_workflow_yaml_parsing,
        test_context_integration,
        compare_old_vs_rf
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📈 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 RF MVP验证成功！可以开始正式迁移。")
        return 0
    else:
        print("⚠️  RF MVP需要进一步优化。")
        return 1


if __name__ == "__main__":
    sys.exit(main())