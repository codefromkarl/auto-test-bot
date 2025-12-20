#!/usr/bin/env python3
"""
RF迁移验证器
验证RF版本FC与原版的兼容性和改进效果
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class RFMigrationValidator:
    """RF迁移验证器"""

    def __init__(self):
        self.fc_dir = Path(__file__).parent.parent / "workflows/fc"
        self.validation_results = []

    def validate_migration(self, original_fc: str, rf_fc: str) -> Dict:
        """验证单个FC的迁移效果"""
        result = {
            'original_fc': original_fc,
            'rf_fc': rf_fc,
            'selector_reduction': 0,
            'semantic_actions_added': 0,
            'business_logic_improved': False,
            'error_recovery_added': False,
            'success_criteria_defined': False,
            'backward_compatibility': True,
            'improvement_score': 0
        }

        try:
            # 解析原版和RF版
            original = self._parse_yaml(original_fc)
            rf_version = self._parse_yaml(rf_fc)

            # 分析selector减少
            result['selector_reduction'] = self._analyze_selector_reduction(original, rf_version)

            # 分析语义Action增加
            result['semantic_actions_added'] = self._count_semantic_actions(rf_version)

            # 分析业务逻辑改进
            result['business_logic_improved'] = self._analyze_business_logic_improvement(original, rf_version)

            # 分析错误恢复机制
            result['error_recovery_added'] = self._analyze_error_recovery(rf_version)

            # 分析成功标准定义
            result['success_criteria_defined'] = self._analyze_success_criteria(rf_version)

            # 分析向后兼容性
            result['backward_compatibility'] = self._analyze_backward_compatibility(original, rf_version)

            # 计算综合改进分数
            result['improvement_score'] = self._calculate_improvement_score(result)

        except Exception as e:
            print(f"验证失败 {original_fc}: {e}")
            result['error'] = str(e)

        return result

    def _parse_yaml(self, yaml_path: str) -> Dict:
        """解析YAML文件"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _analyze_selector_reduction(self, original: Dict, rf_version: Dict) -> int:
        """分析selector减少数量"""
        original_selectors = self._count_selectors(original)
        rf_selectors = self._count_selectors(rf_version)
        return original_selectors - rf_selectors

    def _count_selectors(self, workflow: Dict) -> int:
        """统计selector数量"""
        count = 0
        if 'workflow' in workflow:
            # suite_setup中的selectors
            for step in workflow['workflow'].get('suite_setup', []):
                if 'selector' in step:
                    count += 1

            # phases中的selectors
            for phase in workflow['workflow'].get('phases', []):
                for step in phase.get('steps', []):
                    if 'selector' in step:
                        count += 1

            # error_recovery中的selectors
            for step in workflow['workflow'].get('error_recovery', []):
                if 'selector' in step:
                    count += 1

        return count

    def _count_semantic_actions(self, rf_version: Dict) -> int:
        """统计语义Action数量"""
        count = 0
        if 'workflow' in rf_version:
            # 检查suite_setup
            for step in rf_version['workflow'].get('suite_setup', []):
                if step.get('action', '').startswith('rf_'):
                    count += 1

            # 检查phases
            for phase in rf_version['workflow'].get('phases', []):
                for step in phase.get('steps', []):
                    if step.get('action', '').startswith('rf_'):
                        count += 1

            # 检查error_recovery
            for step in rf_version['workflow'].get('error_recovery', []):
                if step.get('action', '').startswith('rf_'):
                    count += 1

        return count

    def _analyze_business_logic_improvement(self, original: Dict, rf_version: Dict) -> bool:
        """分析业务逻辑改进"""
        rf_improvements = 0

        # 检查是否有suite_setup（公共路径收束）
        if rf_version['workflow'].get('suite_setup'):
            rf_improvements += 1

        # 检查phase description是否更明确
        rf_descriptions = []
        for phase in rf_version['workflow'].get('phases', []):
            rf_descriptions.append(phase.get('description', '').lower())

        if any('rf语义化' in desc or '语义' in desc for desc in rf_descriptions):
            rf_improvements += 1

        return rf_improvements >= 1

    def _analyze_error_recovery(self, rf_version: Dict) -> bool:
        """分析错误恢复机制"""
        return 'error_recovery' in rf_version['workflow'] and len(rf_version['workflow']['error_recovery']) > 0

    def _analyze_success_criteria(self, rf_version: Dict) -> bool:
        """分析成功标准定义"""
        return 'success_criteria' in rf_version['workflow'] and len(rf_version['workflow']['success_criteria']) > 0

    def _analyze_backward_compatibility(self, original: Dict, rf_version: Dict) -> bool:
        """分析向后兼容性"""
        # 检查RF版是否保留原版的核心功能
        original_actions = set()
        rf_actions = set()

        # 收集原版action类型
        for phase in original['workflow'].get('phases', []):
            for step in phase.get('steps', []):
                original_actions.add(step.get('action', ''))

        # 收集RF版action类型（包含rf_前缀的语义action和其他）
        for phase in rf_version['workflow'].get('phases', []):
            for step in phase.get('steps', []):
                action = step.get('action', '')
                if action.startswith('rf_'):
                    # 语义action映射到原版action
                    if 'enter_ai_creation' in action or 'ensure_story_exists' in action:
                        rf_actions.update(['open_page', 'click', 'wait_for'])
                else:
                    rf_actions.add(action)

        # 检查是否包含核心功能
        core_actions = {'screenshot', 'assert_element_exists'}
        return core_actions.issubset(rf_actions)

    def _calculate_improvement_score(self, result: Dict) -> int:
        """计算综合改进分数"""
        score = 0

        # selector减少（权重：40%）
        score += min(result['selector_reduction'] * 4, 40)

        # 语义Action增加（权重：20%）
        score += min(result['semantic_actions_added'] * 5, 20)

        # 业务逻辑改进（权重：15%）
        score += 15 if result['business_logic_improved'] else 0

        # 错误恢复机制（权重：15%）
        score += 15 if result['error_recovery_added'] else 0

        # 成功标准定义（权重：10%）
        score += 10 if result['success_criteria_defined'] else 0

        return min(score, 100)

    def validate_batch(self, migration_pairs: List[Tuple[str, str]]) -> Dict:
        """批量验证迁移"""
        results = {
            'total_pairs': len(migration_pairs),
            'validations': [],
            'summary': {
                'total_selector_reduction': 0,
                'total_semantic_actions': 0,
                'average_improvement_score': 0,
                'high_quality_migrations': 0,
                'backward_compatible_rate': 0
            }
        }

        for original, rf_version in migration_pairs:
            validation = self.validate_migration(original, rf_version)
            results['validations'].append(validation)

            # 更新汇总
            results['summary']['total_selector_reduction'] += validation['selector_reduction']
            results['summary']['total_semantic_actions'] += validation['semantic_actions_added']
            results['summary']['high_quality_migrations'] += 1 if validation['improvement_score'] >= 80 else 0
            results['summary']['backward_compatible_rate'] += 1 if validation['backward_compatibility'] else 0

        # 计算平均值
        if results['validations']:
            total_score = sum(v['improvement_score'] for v in results['validations'])
            results['summary']['average_improvement_score'] = total_score / len(results['validations'])
            results['summary']['backward_compatible_rate'] = (
                results['summary']['backward_compatible_rate'] / len(results['validations']) * 100
            )

        return results


def main():
    """主验证函数"""
    print("🔍 RF迁移验证开始\n")

    validator = RFMigrationValidator()

    # 获取已迁移的FC对
    migration_pairs = [
        ("naohai_FC_NH_002.yaml", "naohai_FC_NH_002_rf.yaml"),
        ("naohai_FC_NH_003.yaml", "naohai_FC_NH_003_rf.yaml"),
        ("naohai_FC_NH_037.yaml", "naohai_FC_NH_037_rf.yaml"),
        ("naohai_FC_NH_050.yaml", "naohai_FC_NH_050_rf.yaml"),
    ]

    # 添加完整路径
    fc_dir = Path(__file__).parent.parent / "workflows/fc"
    migration_pairs = [
        (str(fc_dir / original), str(fc_dir / rf_version))
        for original, rf_version in migration_pairs
    ]

    # 执行验证
    results = validator.validate_batch(migration_pairs)

    # 输出详细结果
    print(f"📊 验证了 {results['total_pairs']} 个迁移对\n")

    for validation in results['validations']:
        fc_name = Path(validation['original_fc']).name
        print(f"📋 {fc_name}:")
        print(f"  ✅ Selector减少: {validation['selector_reduction']} 个")
        print(f"  ✅ 语义Action: {validation['semantic_actions_added']} 个")
        print(f"  ✅ 业务逻辑改进: {'是' if validation['business_logic_improved'] else '否'}")
        print(f"  ✅ 错误恢复机制: {'有' if validation['error_recovery_added'] else '无'}")
        print(f"  ✅ 成功标准定义: {'有' if validation['success_criteria_defined'] else '无'}")
        print(f"  ✅ 向后兼容性: {'通过' if validation['backward_compatibility'] else '失败'}")
        print(f"  📈 改进分数: {validation['improvement_score']}/100")
        print()

    # 输出汇总结果
    summary = results['summary']
    print("📈 汇总结果:")
    print(f"  总Selector减少: {summary['total_selector_reduction']} 个")
    print(f"  总语义Action增加: {summary['total_semantic_actions']} 个")
    print(f"  平均改进分数: {summary['average_improvement_score']:.1f}/100")
    print(f"  高质量迁移数量: {summary['high_quality_migrations']}/{results['total_pairs']}")
    print(f"  向后兼容率: {summary['backward_compatible_rate']:.1f}%")

    # 生成验证报告
    report = {
        'validation_timestamp': str(Path(__file__).stat().st_mtime),
        'migration_pairs': migration_pairs,
        'detailed_results': results['validations'],
        'summary': summary,
        'recommendations': generate_recommendations(summary)
    }

    report_path = Path(__file__).parent.parent / "docs/rf_migration_validation_report.yaml"
    with open(report_path, 'w', encoding='utf-8') as f:
        yaml.dump(report, f, allow_unicode=True, default_flow_style=False)

    print(f"📁 详细报告已保存到: {report_path}")

    # 判断验证结果
    if summary['average_improvement_score'] >= 70 and summary['backward_compatible_rate'] >= 80:
        print("🎉 RF迁移验证通过！可以继续扩大迁移范围。")
        return 0
    else:
        print("⚠️  RF迁移需要进一步优化。")
        return 1


def generate_recommendations(summary: Dict) -> List[str]:
    """生成改进建议"""
    recommendations = []

    if summary['average_improvement_score'] < 70:
        recommendations.append("增加更多语义Action以提升业务抽象程度")

    if summary['total_selector_reduction'] < summary['high_quality_migrations'] * 3:
        recommendations.append("进一步减少硬编码selector使用")

    if summary['backward_compatible_rate'] < 100:
        recommendations.append("确保所有RF版本保持核心功能兼容性")

    recommendations.append("继续扩展语义Action库覆盖更多业务场景")
    recommendations.append("建立自动化验证流程确保迁移质量")

    return recommendations


if __name__ == "__main__":
    sys.exit(main())