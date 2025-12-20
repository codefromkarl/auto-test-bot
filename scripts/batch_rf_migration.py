#!/usr/bin/env python3
"""
RF全量批量迁移脚本
自动化迁移全部59个FC到RF版本
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class BatchRFMigrator:
    """RF全量批量迁移器"""

    def __init__(self):
        self.fc_dir = Path(__file__).parent.parent / "workflows/fc"
        self.migration_results = []
        self.start_time = time.time()

    def migrate_all_fcs(self) -> Dict:
        """批量迁移全部FC到RF版本"""
        print("🚀 开始RF全量批量迁移\n")

        # 获取所有FC文件
        all_yaml_files = sorted(self.fc_dir.glob("naohai_FC_NH_*.yaml"))
        original_fc_files = [f for f in all_yaml_files if not f.stem.endswith('_rf')]
        rf_files = sorted(self.fc_dir.glob("naohai_FC_NH_*_rf.yaml"))

        existing_rf_basenames = {p.stem.replace('_rf', '') for p in rf_files}
        fc_to_migrate = [f for f in original_fc_files if f.stem not in existing_rf_basenames]

        print(f"📊 发现 {len(all_yaml_files)} 个工作流文件（原版 {len(original_fc_files)} / RF {len(rf_files)}）")
        print(f"🎯 需要迁移 {len(fc_to_migrate)} 个FC\n")

        # 按业务领域分组
        fc_groups = self._group_fcs_by_business_area(fc_to_migrate)

        # 并行迁移每组
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_group = {}

            for group_name, fc_paths in fc_groups.items():
                print(f"🔄 开始迁移组: {group_name} ({len(fc_paths)} 个)")

                # 为每个FC组创建迁移future
                group_futures = []
                for fc_path in fc_paths:
                    future = executor.submit(self._migrate_single_fc, fc_path)
                    group_futures.append(future)

                future_to_group[group_name] = group_futures

            # 等待所有组完成
            all_futures = []
            for group_futures in future_to_group.values():
                all_futures.extend(group_futures)

            # 收集结果
            for future in as_completed(all_futures):
                try:
                    result = future.result()
                    self.migration_results.append(result)
                except Exception as e:
                    print(f"❌ FC迁移失败: {e}")

        # 生成全量报告（基于当前目录下全部RF版本，而不是“本次迁移了多少个”）
        migrated_in_this_run = {p.stem for p in fc_to_migrate}
        full_results = self._build_full_results(migrated_in_this_run)
        migration_report = self._generate_migration_report(full_results, migrated_in_this_run, len(all_yaml_files), len(original_fc_files), len(rf_files))

        end_time = time.time()
        migration_report['execution_time'] = {
            'start_time': self.start_time,
            'end_time': end_time,
            'duration_minutes': (end_time - self.start_time) / 60
        }

        return migration_report

    def _build_full_results(self, migrated_in_this_run: set[str]) -> List[Dict]:
        """基于当前目录下全部RF版本，构建全量验证结果"""
        rf_files = sorted(self.fc_dir.glob("naohai_FC_NH_*_rf.yaml"))
        results: List[Dict] = []

        for rf_path in rf_files:
            original_path = rf_path.with_name(rf_path.name.replace('_rf.yaml', '.yaml'))
            fc_name = original_path.name

            if not original_path.exists():
                results.append({
                    'original_fc': str(original_path),
                    'rf_fc': str(rf_path),
                    'fc_name': fc_name,
                    'success': False,
                    'error': '对应的原版FC不存在，无法生成对比指标',
                    'migrated_in_this_run': False,
                    'selector_reduction': 0,
                    'semantic_actions_added': 0,
                })
                continue

            validation = self._validate_migration(original_path, rf_path)
            validation_error = validation.get('validation_error')
            results.append({
                'original_fc': str(original_path),
                'rf_fc': str(rf_path),
                'fc_name': fc_name,
                'success': validation_error is None,
                'validation': validation,
                'migrated_in_this_run': original_path.stem in migrated_in_this_run,
                'selector_reduction': validation.get('selector_reduction', 0),
                'semantic_actions_added': validation.get('semantic_actions_added', 0),
                **({'error': validation_error} if validation_error else {})
            })

        return results

    def _group_fcs_by_business_area(self, fc_files: List[Path]) -> Dict[str, List[Path]]:
        """按业务领域分组FC"""
        groups = {
            'core_navigation': [],      # 进入AI创作、剧本列表
            'story_management': [],      # 剧本操作、菜单
            'character_scene': [],         # 角色、场景管理
            'storyboard_video': [],       # 分镜、视频创作
            'export_upload': []           # 导出、上传功能
        }

        for fc_file in fc_files:
            with open(fc_file, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
                description = workflow.get('workflow', {}).get('description', '').lower()

            # 根据描述分组
            if 'ai创作' in description or '剧本列表' in description:
                groups['core_navigation'].append(fc_file)
            elif '角色' in description or '绑定' in description:
                groups['character_scene'].append(fc_file)
            elif '分镜' in description or '故事板' in description:
                groups['storyboard_video'].append(fc_file)
            elif '导出' in description or '上传' in description:
                groups['export_upload'].append(fc_file)
            else:
                groups['story_management'].append(fc_file)

        return groups

    def _migrate_single_fc(self, fc_path: Path) -> Dict:
        """迁移单个FC到RF版本"""
        try:
            fc_name = fc_path.name
            print(f"  🔄 迁移 {fc_name}")

            # 解析原版FC
            with open(fc_path, 'r', encoding='utf-8') as f:
                original_workflow = yaml.safe_load(f)

            # 生成RF版本
            rf_workflow = self._convert_to_rf_version(original_workflow)

            # 保存RF版本
            rf_path = fc_path.parent / f"{fc_path.stem}_rf.yaml"
            with open(rf_path, 'w', encoding='utf-8') as f:
                yaml.dump(rf_workflow, f, allow_unicode=True, default_flow_style=False)

            # 验证迁移结果
            validation = self._validate_migration(fc_path, rf_path)

            result = {
                'original_fc': str(fc_path),
                'rf_fc': str(rf_path),
                'fc_name': fc_name,
                'success': True,
                'validation': validation,
                'selector_reduction': validation.get('selector_reduction', 0),
                'semantic_actions_added': validation.get('semantic_actions_added', 0)
            }

            print(f"    ✅ {fc_name} 迁移完成")
            return result

        except Exception as e:
            print(f"    ❌ {fc_name} 迁移失败: {e}")
            return {
                'original_fc': str(fc_path),
                'rf_fc': str(fc_path),
                'fc_name': fc_path.name if 'fc_path' in locals() else 'unknown',
                'success': False,
                'error': str(e),
                'selector_reduction': 0,
                'semantic_actions_added': 0
            }

    def _convert_to_rf_version(self, original_workflow: Dict) -> Dict:
        """将原版workflow转换为RF版本"""
        rf_workflow = {
            'workflow': {
                'name': original_workflow['workflow']['name'] + '_rf',
                'description': original_workflow['workflow']['description'] + ' (RF版本)',
                'version': 'rf-v1.0'
            }
        }

        # 分析原版workflow，提取公共路径
        common_actions = self._extract_common_actions(original_workflow)

        if common_actions:
            rf_workflow['workflow']['suite_setup'] = common_actions
            print(f"    📦 提取 {len(common_actions)} 个公共步骤到 suite_setup")

        # 转换phases
        rf_phases = []
        for phase in original_workflow['workflow'].get('phases', []):
            rf_phase = self._convert_phase_to_rf(phase)
            if rf_phase:
                rf_phases.append(rf_phase)

        if rf_phases:
            rf_workflow['workflow']['phases'] = rf_phases

        # 添加RF特性
        rf_workflow['workflow']['success_criteria'] = self._generate_success_criteria(original_workflow)
        rf_workflow['workflow']['error_recovery'] = self._generate_error_recovery(original_workflow)

        return rf_workflow

    def _extract_common_actions(self, workflow: Dict) -> List[Dict]:
        """提取公共action到suite_setup"""
        common_patterns = {
            'open_page': {'url': '${test.url}'},
            'wait_for': {'condition': {'selector': 'body', 'visible': True}},
            'assert_logged_in': {}
        }

        # 统计高频actions
        action_counts = {}
        for phase in workflow.get('workflow', {}).get('phases', []):
            for step in phase.get('steps', []):
                action = step.get('action', '')
                if action in action_counts:
                    action_counts[action] += 1
                else:
                    action_counts[action] = 1

        # 提取出现2次以上的actions作为公共步骤 - 修复break逻辑
        common_actions = []
        for action_pattern, params_template in common_patterns.items():
            if action_counts.get(action_pattern, 0) >= 2:
                # 适配参数
                actual_params = {}
                found_first = False
                for phase in workflow.get('workflow', {}).get('phases', []):
                    for step in phase.get('steps', []):
                        if step.get('action', '') == action_pattern:
                            actual_params = {k: v for k, v in step.items() if k != 'action'}
                            found_first = True
                            break
                    if found_first:
                        break

                # 合并模板和实际参数
                merged_params = {**params_template, **actual_params}
                common_actions.append({
                    'action': action_pattern,
                    **merged_params
                })

        return common_actions

    def _convert_phase_to_rf(self, phase: Dict) -> Dict:
        """转换单个phase到RF版本"""
        rf_steps = []
        selector_count = 0
        semantic_action_count = 0

        for step in phase.get('steps', []):
            if 'selector' in step:
                selector_count += 1

            # 尝试语义化
            semantic_action = self._try_semantic_conversion(step)
            if semantic_action:
                rf_steps.append(semantic_action)
                semantic_action_count += 1
            else:
                rf_steps.append(step)

        return {
            'name': phase.get('name'),
            'description': phase.get('description') + ' (RF语义化）',
            'steps': rf_steps,
            'metadata': {
                'selector_count': selector_count,
                'semantic_action_count': semantic_action_count,
                'conversion_rate': semantic_action_count / len(rf_steps) if rf_steps else 0
            }
        }

    def _try_semantic_conversion(self, step: Dict) -> Dict:
        """尝试将step转换为语义action"""
        selector = step.get('selector', '')
        action_type = step.get('action', '')

        # 语义化规则映射
        semantic_rules = {
            '.nav-routerTo-item:has-text("AI创作")': {
                'action': 'rf_enter_ai_creation',
                'remove_selector': True
            },
            'div.list-item:not(.add-item)': {
                'action': 'rf_ensure_story_exists',
                'remove_selector': True
            },
            'text=分镜管理': {
                'action': 'rf_enter_storyboard_management',
                'remove_selector': True
            },
            'text=视频创作': {
                'action': 'rf_select_fusion_generation',
                'remove_selector': True
            },
            'text=模型生成': {
                'action': 'rf_create_scene_mode',
                'params': {'mode': 'generate'},
                'remove_selector': True
            },
            'text=自己上传': {
                'action': 'rf_create_scene_mode',
                'params': {'mode': 'upload'},
                'remove_selector': True
            },
            'text=建议分镜': {
                'action': 'rf_suggest_shot_count',
                'remove_selector': True
            },
            '.suggest-count': {
                'action': 'rf_suggest_shot_count',
                'remove_selector': True
            },
            '.video-fragment:first-child': {
                'action': 'rf_select_video_segments',
                'remove_selector': True
            },
            'text=保存选择': {
                'action': 'rf_select_video_segments',
                'remove_selector': True
            },
            'div.episode-item:has-text(': {
                'action': 'rf_open_episode_menu',
                'remove_selector': True
            },
        }

        # 检查selector匹配
        for pattern, semantic_info in semantic_rules.items():
            if pattern in selector:
                rf_step = {
                    'action': semantic_info['action'],
                    'timeout': step.get('timeout', '${test.timeout.element_load}'),
                    **(semantic_info.get('params', {}) or {}),
                }

                # 保留非selector参数
                for key, value in step.items():
                    if key != 'action' and key != 'selector':
                        rf_step[key] = value

                return rf_step

        return None  # 无法语义化，保持原样

    def _generate_success_criteria(self, workflow: Dict) -> List[str]:
        """生成成功标准"""
        return [
            "成功进入AI创作模块",
            "业务逻辑验证通过",
            "RF语义化改进生效",
            "向后兼容性保持"
        ]

    def _generate_error_recovery(self, workflow: Dict) -> List[Dict]:
        """生成错误恢复策略"""
        return [
            {
                'action': 'rf_enter_ai_creation',
                'timeout': '${test.timeout.element_load}'
            },
            {
                'action': 'rf_ensure_story_exists',
                'timeout': '${test.timeout.element_load}'
            }
        ]

    def _validate_migration(self, original_path: Path, rf_path: Path) -> Dict:
        """验证迁移结果"""
        try:
            # 尝试创建RF版本的actions
            with open(rf_path, 'r', encoding='utf-8') as f:
                rf_workflow = yaml.safe_load(f)

            # 统计selector减少
            original_selectors = self._count_selectors(original_path)
            rf_selectors = self._count_selectors(rf_path)

            # 统计semantic actions
            semantic_actions = self._count_semantic_actions(rf_path)

            return {
                'selector_reduction': original_selectors - rf_selectors,
                'semantic_actions_added': semantic_actions,
                'selector_reduction_rate': (original_selectors - rf_selectors) / original_selectors if original_selectors > 0 else 0
            }

        except Exception as e:
            return {
                'validation_error': str(e),
                'selector_reduction': 0,
                'semantic_actions_added': 0
            }

    def _count_selectors(self, yaml_path: Path) -> int:
        """统计文件中的selector数量"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content.count('selector:')
        except:
            return 0

    def _count_semantic_actions(self, yaml_path: Path) -> int:
        """统计文件中的semantic action数量"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f) or {}

            count = 0
            wf = workflow.get('workflow', {})

            for step in wf.get('suite_setup', []) or []:
                if isinstance(step, dict) and str(step.get('action', '')).startswith('rf_'):
                    count += 1

            for phase in wf.get('phases', []) or []:
                for step in phase.get('steps', []) or []:
                    if isinstance(step, dict) and str(step.get('action', '')).startswith('rf_'):
                        count += 1

            for step in wf.get('error_recovery', []) or []:
                if isinstance(step, dict) and str(step.get('action', '')).startswith('rf_'):
                    count += 1

            return count
        except Exception:
            return 0

    def _generate_migration_report(
        self,
        full_results: List[Dict],
        migrated_in_this_run: set[str],
        all_workflow_files: int,
        original_fc_files: int,
        rf_files: int,
    ) -> Dict:
        """生成迁移报告（全量：以当前RF文件为准）"""
        successful_migrations = [r for r in full_results if r.get('success')]
        failed_migrations = [r for r in full_results if not r.get('success')]

        # 统计指标
        total_selector_reduction = sum(r.get('selector_reduction', 0) for r in successful_migrations)
        total_semantic_actions = sum(r.get('semantic_actions_added', 0) for r in successful_migrations)

        return {
            'run_context': {
                'discovered_workflow_files': all_workflow_files,
                'discovered_original_fcs': original_fc_files,
                'discovered_rf_versions': rf_files,
                'migrated_in_this_run': len(migrated_in_this_run),
            },
            'migration_summary': {
                'total_fcs': len(full_results),
                'successful': len(successful_migrations),
                'failed': len(failed_migrations),
                'success_rate': len(successful_migrations) / len(full_results) * 100 if full_results else 0
            },
            'improvement_metrics': {
                'total_selector_reduction': total_selector_reduction,
                'total_semantic_actions': total_semantic_actions,
                'avg_selector_reduction_per_fc': total_selector_reduction / len(successful_migrations) if successful_migrations else 0,
                'avg_semantic_actions_per_fc': total_semantic_actions / len(successful_migrations) if successful_migrations else 0
            },
            'detailed_results': full_results,
            'failed_migrations': failed_migrations
        }


def main():
    """主函数"""
    print("🚀 RF全量批量迁移开始\n")

    migrator = BatchRFMigrator()

    # 执行全量迁移
    migration_report = migrator.migrate_all_fcs()

    # 保存迁移报告
    report_path = Path(__file__).parent.parent / "docs/rf_full_migration_report.yaml"
    with open(report_path, 'w', encoding='utf-8') as f:
        yaml.dump(migration_report, f, allow_unicode=True, default_flow_style=False)

    # 输出摘要
    summary = migration_report['migration_summary']
    metrics = migration_report['improvement_metrics']

    print(f"\n🎉 RF全量迁移完成！")
    print(f"📊 迁移摘要:")
    print(f"  总FC数: {summary['total_fcs']}")
    print(f"  成功: {summary['successful']}")
    print(f"  失败: {summary['failed']}")
    print(f"  成功率: {summary['success_rate']:.1f}%")

    print(f"\n📈 改进指标:")
    print(f"  Selector总减少: {metrics['total_selector_reduction']}")
    print(f"  平均每FC减少: {metrics['avg_selector_reduction_per_fc']:.1f}")
    print(f"  语义Action总数: {metrics['total_semantic_actions']}")
    print(f"  平均每FC增加: {metrics['avg_semantic_actions_per_fc']:.1f}")

    if summary['success_rate'] >= 90:
        print("🎯 迁移质量：优秀")
        return 0
    elif summary['success_rate'] >= 75:
        print("🎯 迁移质量：良好")
        return 0
    else:
        print("⚠️  迁移需要优化")
        return 1


if __name__ == "__main__":
    sys.exit(main())
