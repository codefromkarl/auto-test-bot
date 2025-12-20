#!/usr/bin/env python3
"""闹海E2E黄金路径工作流静态验证脚本"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from e2e.golden_path_validator import (
    evaluate_golden_path_coverage,
    validate_golden_path_workflow,
    REQUIRED_PHASES,
)
from models import Workflow


def load_workflow(yaml_path: str) -> Workflow:
    """加载并解析YAML工作流"""
    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_content = f.read()
    return Workflow.from_yaml(yaml_content)


def validate_workflow_structure(workflow: Workflow) -> Dict[str, Any]:
    """验证工作流结构完整性"""
    errors = validate_golden_path_workflow(workflow)

    # 额外的结构验证
    structure_issues = []

    # 检查阶段数量
    phases_count = len(workflow.phases)
    if phases_count != 7:
        structure_issues.append({
            "type": "phase_count_mismatch",
            "expected": 7,
            "actual": phases_count,
            "message": f"阶段数量应为7个，实际为{phases_count}个"
        })

    # 检查每个阶段的步骤
    phase_details = []
    for phase in workflow.phases:
        steps_count = len(phase.steps)
        rf_actions = []
        screenshot_count = 0
        optional_count = 0

        for step in phase.steps:
            action_name = getattr(step, 'action', step.__class__.__name__ if hasattr(step, '__class__') else 'unknown')
            if action_name.startswith('rf_'):
                rf_actions.append(action_name)
            if hasattr(step, 'action') and step.action == 'screenshot':
                screenshot_count += 1
            if hasattr(step, 'optional') and step.optional:
                optional_count += 1

        phase_details.append({
            "name": phase.name,
            "steps_count": steps_count,
            "rf_actions": rf_actions,
            "screenshot_count": screenshot_count,
            "optional_steps": optional_count,
            "has_screenshot": screenshot_count > 0
        })

    # 检查成功标准
    success_criteria_count = len(workflow.success_criteria)
    success_criteria_issues = []
    if success_criteria_count < 7:
        success_criteria_issues.append(f"成功标准建议至少7条，当前为{success_criteria_count}条")

    return {
        "validation_errors": errors,
        "structure_issues": structure_issues,
        "phase_details": phase_details,
        "success_criteria": {
            "count": success_criteria_count,
            "items": list(workflow.success_criteria),
            "issues": success_criteria_issues
        }
    }


def validate_performance_monitoring(workflow: Workflow) -> Dict[str, Any]:
    """验证性能监控配置"""
    perf_monitoring = workflow.metadata.get('performance_monitoring', {})

    issues = []

    # 检查是否启用性能监控
    if not perf_monitoring.get('enabled'):
        issues.append("性能监控未启用")

    # 检查检查点配置
    checkpoints = perf_monitoring.get('checkpoints', [])
    if len(checkpoints) != 7:
        issues.append(f"性能检查点应为7个，实际为{len(checkpoints)}个")

    # 验证每个检查点
    checkpoint_details = []
    for cp in checkpoints:
        phase_name = cp.get('phase')
        expected_duration = cp.get('expected_duration')

        if not phase_name or phase_name not in REQUIRED_PHASES:
            issues.append(f"无效的性能检查点阶段: {phase_name}")

        checkpoint_details.append({
            "phase": phase_name,
            "expected_duration": expected_duration,
            "valid": phase_name in REQUIRED_PHASES if phase_name else False
        })

    return {
        "enabled": perf_monitoring.get('enabled', False),
        "checkpoint_count": len(checkpoints),
        "checkpoint_details": checkpoint_details,
        "issues": issues
    }


def validate_error_recovery(workflow: Workflow) -> Dict[str, Any]:
    """验证错误恢复机制"""
    error_recovery = workflow.error_recovery

    recovery_actions = []
    has_rf_actions = False

    for action in error_recovery:
        action_name = getattr(action, 'action', action.__class__.__name__)
        recovery_actions.append({
            "action": action_name,
            "is_rf_action": action_name.startswith('rf_'),
            "optional": getattr(action, 'optional', False)
        })
        if action_name.startswith('rf_'):
            has_rf_actions = True

    issues = []
    if not recovery_actions:
        issues.append("未配置错误恢复步骤")

    return {
        "action_count": len(recovery_actions),
        "has_rf_actions": has_rf_actions,
        "actions": recovery_actions,
        "issues": issues
    }


def calculate_business_path_coverage(workflow: Workflow) -> Dict[str, Any]:
    """计算关键业务路径覆盖度"""
    phases_by_name = {p.name: p for p in workflow.phases}

    # 关键业务路径检查点
    critical_paths = {
        "script_creation": {
            "phase": "create_script_and_outline",
            "requirements": ["填写剧本名称", "填写剧本描述", "选择画风"],
            "found": False
        },
        "asset_creation": {
            "phase": "setup_episode_assets",
            "requirements": ["创建分集", "创建角色", "创建场景"],
            "found": False
        },
        "storyboard_generation": {
            "phase": "analyze_and_create_storyboard",
            "requirements": ["分析剧本", "生成分镜", "生成提示词"],
            "found": False
        },
        "asset_binding": {
            "phase": "bind_storyboard_assets",
            "requirements": ["绑定角色", "绑定场景"],
            "found": False
        },
        "image_generation": {
            "phase": "generate_image_assets",
            "requirements": ["融合生图"],
            "found": False
        },
        "video_generation": {
            "phase": "generate_video_segments",
            "requirements": ["图生视频"],
            "found": False
        },
        "export": {
            "phase": "export_final_video",
            "requirements": ["导出资源"],
            "found": False
        }
    }

    # 检查每个关键路径
    for path_name, path_info in critical_paths.items():
        phase = phases_by_name.get(path_info["phase"])
        if phase:
            # 检查步骤中是否包含关键操作
            step_texts = []
            for step in phase.steps:
                if hasattr(step, 'selector') and step.selector:
                    step_texts.append(step.selector)
                if hasattr(step, 'text') and step.text:
                    step_texts.append(step.text)

            # 简单的关键词匹配
            all_steps_text = " ".join(step_texts).lower()
            for req in path_info["requirements"]:
                if req.lower() in all_steps_text:
                    path_info["found"] = True
                    break

    covered_paths = [p for p in critical_paths.values() if p["found"]]
    coverage_ratio = len(covered_paths) / len(critical_paths)

    return {
        "total_paths": len(critical_paths),
        "covered_paths": len(covered_paths),
        "coverage_ratio": coverage_ratio,
        "critical_paths": critical_paths
    }


def generate_validation_report() -> Dict[str, Any]:
    """生成完整的验证报告"""
    yaml_path = Path(__file__).parent.parent / "workflows" / "e2e" / "naohai_E2E_GoldenPath.yaml"

    # 加载工作流
    workflow = load_workflow(yaml_path)

    # 执行各项验证
    structure_validation = validate_workflow_structure(workflow)
    performance_validation = validate_performance_monitoring(workflow)
    error_recovery_validation = validate_error_recovery(workflow)
    coverage_evaluation = evaluate_golden_path_coverage(workflow)
    business_path_coverage = calculate_business_path_coverage(workflow)

    # 汇总报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "workflow_name": workflow.name,
        "workflow_version": workflow.metadata.get('version', 'unknown'),
        "validation_summary": {
            "total_errors": len(structure_validation["validation_errors"]),
            "total_issues": len(structure_validation["structure_issues"]) +
                          len(performance_validation["issues"]) +
                          len(error_recovery_validation["issues"]),
            "phase_coverage": coverage_evaluation["coverage_ratio"],
            "evidence_coverage": coverage_evaluation["evidence_ratio"],
            "business_path_coverage": business_path_coverage["coverage_ratio"]
        },
        "structure_validation": structure_validation,
        "performance_monitoring": performance_validation,
        "error_recovery": error_recovery_validation,
        "coverage_evaluation": coverage_evaluation,
        "business_path_coverage": business_path_coverage,
        "overall_status": {
            "passed": len(structure_validation["validation_errors"]) == 0 and
                    len(structure_validation["structure_issues"]) == 0,
            "ready_for_execution": False,  # 需要综合判断
            "recommendations": []
        }
    }

    # 生成建议
    recommendations = []
    if report["validation_summary"]["phase_coverage"] < 1.0:
        recommendations.append("补充缺失的核心阶段以达到100%阶段覆盖")
    if report["validation_summary"]["evidence_coverage"] < 0.8:
        recommendations.append("为每个阶段添加截图步骤以提供执行证据")
    if len(performance_validation["issues"]) > 0:
        recommendations.append("修复性能监控配置问题")
    if len(error_recovery_validation["issues"]) > 0:
        recommendations.append("完善错误恢复机制")

    report["overall_status"]["recommendations"] = recommendations
    report["overall_status"]["ready_for_execution"] = (
        report["validation_summary"]["total_errors"] == 0 and
        report["validation_summary"]["phase_coverage"] == 1.0 and
        len(performance_validation["issues"]) == 0
    )

    return report


def main():
    """主函数"""
    print("开始验证闹海E2E黄金路径工作流...")

    try:
        report = generate_validation_report()

        # 保存报告
        report_path = Path(__file__).parent.parent / "reports" / "e2e" / "validation_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        print(f"\n验证完成！报告已保存到: {report_path}")
        print(f"\n=== 验证摘要 ===")
        print(f"工作流名称: {report['workflow_name']}")
        print(f"总错误数: {report['validation_summary']['total_errors']}")
        print(f"总问题数: {report['validation_summary']['total_issues']}")
        print(f"阶段覆盖率: {report['validation_summary']['phase_coverage']:.1%}")
        print(f"证据覆盖率: {report['validation_summary']['evidence_coverage']:.1%}")
        print(f"业务路径覆盖率: {report['validation_summary']['business_path_coverage']:.1%}")
        print(f"整体状态: {'✅ 通过' if report['overall_status']['passed'] else '❌ 未通过'}")
        print(f"可执行: {'✅ 是' if report['overall_status']['ready_for_execution'] else '❌ 否'}")

        if report['overall_status']['recommendations']:
            print(f"\n=== 建议 ===")
            for rec in report['overall_status']['recommendations']:
                print(f"- {rec}")

        return 0 if report['overall_status']['passed'] else 1

    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())