#!/usr/bin/env python3
"""
E2E黄金路径工作流静态验证脚本
使用golden_path_validator进行全面的静态分析和验证
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.workflow import Workflow
from e2e.golden_path_validator import (
    validate_golden_path_workflow,
    evaluate_golden_path_coverage,
    REQUIRED_PHASES
)


def validate_phase_structure(workflow: Workflow) -> Dict[str, Any]:
    """验证每个阶段的详细结构"""
    phase_validation = {
        "total_phases": len(workflow.phases),
        "phases_detail": []
    }

    for phase in workflow.phases:
        phase_name = getattr(phase, "name", "unknown")
        steps = getattr(phase, "steps", [])

        # 统计action类型
        action_types = {}
        rf_actions = []
        screenshot_count = 0

        for step in steps:
            action_name = getattr(step, "action", "unknown")
            action_types[action_name] = action_types.get(action_name, 0) + 1

            # 检查RF语义化action
            if action_name.startswith("rf_"):
                rf_actions.append(action_name)

            # 统计截图步骤
            if action_name == "screenshot":
                screenshot_count += 1

        phase_detail = {
            "name": phase_name,
            "description": getattr(phase, "description", ""),
            "step_count": len(steps),
            "action_types": action_types,
            "rf_actions": rf_actions,
            "screenshot_count": screenshot_count,
            "has_screenshot_evidence": screenshot_count > 0,
            "validation_status": "valid" if screenshot_count > 0 else "missing_screenshot"
        }

        phase_validation["phases_detail"].append(phase_detail)

    return phase_validation


def validate_rf_semantics(workflow: Workflow) -> Dict[str, Any]:
    """验证RF语义化action的使用"""
    rf_validation = {
        "total_rf_actions": 0,
        "rf_actions_by_phase": {},
        "rf_action_list": [],
        "semantic_coverage": {}
    }

    # 预期的RF语义化action列表
    expected_rf_actions = [
        "rf_enter_ai_creation",
        "rf_bind_characters"
    ]

    for phase in workflow.phases:
        phase_name = getattr(phase, "name", "unknown")
        steps = getattr(phase, "steps", [])

        phase_rf_actions = []
        for step in steps:
            action_name = getattr(step, "action", "unknown")
            if action_name.startswith("rf_"):
                phase_rf_actions.append(action_name)
                rf_validation["rf_action_list"].append({
                    "phase": phase_name,
                    "action": action_name
                })

        rf_validation["rf_actions_by_phase"][phase_name] = phase_rf_actions
        rf_validation["total_rf_actions"] += len(phase_rf_actions)

    # 计算语义化覆盖率
    rf_validation["semantic_coverage"] = {
        "expected_rf_actions": expected_rf_actions,
        "found_rf_actions": list(set([item["action"] for item in rf_validation["rf_action_list"]])),
        "coverage_rate": len(set([item["action"] for item in rf_validation["rf_action_list"]])) / len(expected_rf_actions) if expected_rf_actions else 0
    }

    return rf_validation


def validate_performance_monitoring(workflow: Workflow) -> Dict[str, Any]:
    """验证性能监控配置"""
    perf_monitoring = getattr(workflow, "metadata", {}).get("performance_monitoring", {})

    if not perf_monitoring:
        return {
            "enabled": False,
            "error": "No performance_monitoring configuration found"
        }

    validation = {
        "enabled": perf_monitoring.get("enabled", False),
        "checkpoints_configured": len(perf_monitoring.get("checkpoints", [])),
        "checkpoints_detail": [],
        "total_expected_duration": 0,
        "validation_errors": []
    }

    # 验证每个检查点
    for checkpoint in perf_monitoring.get("checkpoints", []):
        phase_name = checkpoint.get("phase")
        expected_duration = checkpoint.get("expected_duration", 0)

        validation["total_expected_duration"] += expected_duration
        validation["checkpoints_detail"].append({
            "phase": phase_name,
            "expected_duration": expected_duration,
            "phase_exists": phase_name in [getattr(p, "name", "") for p in workflow.phases]
        })

        # 检查阶段是否存在
        if phase_name not in [getattr(p, "name", "") for p in workflow.phases]:
            validation["validation_errors"].append(f"Checkpoint references non-existent phase: {phase_name}")

    return validation


def assess_business_path_integrity(workflow: Workflow) -> Dict[str, Any]:
    """评估关键业务路径完整性"""
    business_paths = {
        "creation_path": {
            "description": "从创建剧本到完成的路径",
            "phases": ["create_script_and_outline"],
            "status": "not_verified"
        },
        "asset_management_path": {
            "description": "资产管理路径（分集、角色、场景）",
            "phases": ["setup_episode_assets"],
            "status": "not_verified"
        },
        "storyboard_path": {
            "description": "分镜创作路径",
            "phases": ["analyze_and_create_storyboard"],
            "status": "not_verified"
        },
        "generation_path": {
            "description": "内容生成路径（图片、视频）",
            "phases": ["generate_image_assets", "generate_video_segments"],
            "status": "not_verified"
        },
        "export_path": {
            "description": "导出交付路径",
            "phases": ["export_final_video"],
            "status": "not_verified"
        }
    }

    existing_phases = [getattr(p, "name", "") for p in workflow.phases]

    for path_name, path_info in business_paths.items():
        required_phases = path_info["phases"]
        missing_phases = [p for p in required_phases if p not in existing_phases]

        if not missing_phases:
            path_info["status"] = "complete"
            path_info["missing_phases"] = []
        else:
            path_info["status"] = "incomplete"
            path_info["missing_phases"] = missing_phases

    # 计算整体完整性
    complete_paths = [p for p in business_paths.values() if p["status"] == "complete"]
    integrity_score = len(complete_paths) / len(business_paths)

    return {
        "business_paths": business_paths,
        "integrity_score": integrity_score,
        "complete_paths_count": len(complete_paths),
        "total_paths_count": len(business_paths)
    }


def validate_error_recovery(workflow: Workflow) -> Dict[str, Any]:
    """验证错误恢复机制"""
    error_recovery_actions = getattr(workflow, "error_recovery", [])

    validation = {
        "has_error_recovery": len(error_recovery_actions) > 0,
        "recovery_actions_count": len(error_recovery_actions),
        "recovery_actions_detail": [],
        "recovery_mechanisms": {
            "page_refresh": False,
            "navigation_reset": False,
            "session_recovery": False
        }
    }

    for action in error_recovery_actions:
        action_name = getattr(action, "action", "unknown")
        validation["recovery_actions_detail"].append({
            "action": action_name,
            "parameters": getattr(action, "parameters", {})
        })

        # 检查恢复机制类型
        if action_name == "open_page":
            validation["recovery_mechanisms"]["page_refresh"] = True
        elif action_name.startswith("rf_") and "enter" in action_name:
            validation["recovery_mechanisms"]["navigation_reset"] = True

    return validation


def generate_validation_report() -> Dict[str, Any]:
    """生成完整的验证报告"""

    # 1. 加载工作流
    workflow_path = Path(__file__).parent.parent / "workflows" / "e2e" / "naohai_E2E_GoldenPath.yaml"

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        workflow = Workflow.from_yaml(yaml_content)
    except Exception as e:
        return {
            "validation_error": f"Failed to load workflow: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "status": "failed"
        }

    # 2. 执行各项验证
    report = {
        "workflow_info": {
            "name": workflow.name,
            "description": getattr(workflow, "metadata", {}).get("description", ""),
            "version": getattr(workflow, "metadata", {}).get("version", ""),
            "validation_timestamp": datetime.now().isoformat()
        },

        # 结构完整性验证
        "structure_validation": {
            "errors": validate_golden_path_workflow(workflow),
            "phase_structure": validate_phase_structure(workflow)
        },

        # RF语义化验证
        "rf_semantics_validation": validate_rf_semantics(workflow),

        # 性能监控验证
        "performance_monitoring_validation": validate_performance_monitoring(workflow),

        # 覆盖度评估
        "coverage_evaluation": evaluate_golden_path_coverage(workflow),

        # 业务路径完整性
        "business_path_integrity": assess_business_path_integrity(workflow),

        # 错误恢复验证
        "error_recovery_validation": validate_error_recovery(workflow),

        # 成功标准验证
        "success_criteria_validation": {
            "criteria_count": len(workflow.success_criteria),
            "criteria_list": list(workflow.success_criteria),
            "meets_minimum": len(workflow.success_criteria) >= 7
        },

        # 总体评估
        "overall_assessment": {
            "status": "pending",
            "score": 0,
            "critical_issues": [],
            "recommendations": []
        }
    }

    # 3. 计算总体评估分数和状态
    structure_errors = len(report["structure_validation"]["errors"])
    coverage_ratio = report["coverage_evaluation"]["coverage_ratio"]
    evidence_ratio = report["coverage_evaluation"]["evidence_ratio"]
    integrity_score = report["business_path_integrity"]["integrity_score"]
    has_error_recovery = report["error_recovery_validation"]["has_error_recovery"]
    meets_success_criteria = report["success_criteria_validation"]["meets_minimum"]

    # 计算综合分数（0-100）
    score = 0
    weights = {
        "structure": 30,
        "coverage": 25,
        "evidence": 15,
        "integrity": 15,
        "error_recovery": 10,
        "success_criteria": 5
    }

    if structure_errors == 0:
        score += weights["structure"]

    score += coverage_ratio * weights["coverage"]
    score += evidence_ratio * weights["evidence"]
    score += integrity_score * weights["integrity"]

    if has_error_recovery:
        score += weights["error_recovery"]

    if meets_success_criteria:
        score += weights["success_criteria"]

    report["overall_assessment"]["score"] = round(score, 2)

    # 确定状态
    if structure_errors > 0:
        report["overall_assessment"]["status"] = "failed"
    elif score >= 90:
        report["overall_assessment"]["status"] = "excellent"
    elif score >= 80:
        report["overall_assessment"]["status"] = "good"
    elif score >= 70:
        report["overall_assessment"]["status"] = "acceptable"
    else:
        report["overall_assessment"]["status"] = "needs_improvement"

    # 收集关键问题
    if structure_errors > 0:
        report["overall_assessment"]["critical_issues"].append(
            f"Structure validation failed with {structure_errors} errors"
        )

    if coverage_ratio < 1.0:
        missing_phases = 7 - report["coverage_evaluation"]["present_count"]
        report["overall_assessment"]["critical_issues"].append(
            f"Missing {missing_phases} required phases"
        )

    if evidence_ratio < 0.8:
        report["overall_assessment"]["critical_issues"].append(
            "Insufficient screenshot evidence in phases"
        )

    if not has_error_recovery:
        report["overall_assessment"]["critical_issues"].append(
            "No error recovery mechanisms configured"
        )

    # 生成建议
    if evidence_ratio < 1.0:
        report["overall_assessment"]["recommendations"].append(
            "Add screenshot evidence steps to all phases for better validation"
        )

    if report["rf_semantics_validation"]["semantic_coverage"]["coverage_rate"] < 1.0:
        report["overall_assessment"]["recommendations"].append(
            "Consider using more RF semantic actions for better maintainability"
        )

    if not report["performance_monitoring_validation"]["enabled"]:
        report["overall_assessment"]["recommendations"].append(
            "Enable performance monitoring to track execution times"
        )

    return report


def main():
    """主函数：执行验证并保存报告"""
    print("开始执行E2E黄金路径工作流静态验证...")

    # 生成验证报告
    report = generate_validation_report()

    # 确保reports目录存在
    reports_dir = Path(__file__).parent.parent / "reports" / "e2e"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 保存报告到JSON文件
    report_path = reports_dir / "validation_report.json"

    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n验证报告已保存到: {report_path}")
        print(f"验证状态: {report.get('overall_assessment', {}).get('status', 'unknown')}")
        print(f"综合评分: {report.get('overall_assessment', {}).get('score', 0)}/100")

        # 打印关键摘要
        if report.get("validation_error"):
            print(f"\n错误: {report['validation_error']}")
        else:
            structure_errors = len(report.get("structure_validation", {}).get("errors", []))
            coverage_ratio = report.get("coverage_evaluation", {}).get("coverage_ratio", 0)
            evidence_ratio = report.get("coverage_evaluation", {}).get("evidence_ratio", 0)

            print(f"\n验证摘要:")
            print(f"- 结构错误: {structure_errors}")
            print(f"- 阶段覆盖率: {coverage_ratio:.1%}")
            print(f"- 证据覆盖率: {evidence_ratio:.1%}")

            if report.get("overall_assessment", {}).get("critical_issues"):
                print(f"\n关键问题:")
                for issue in report["overall_assessment"]["critical_issues"]:
                    print(f"  - {issue}")

            if report.get("overall_assessment", {}).get("recommendations"):
                print(f"\n改进建议:")
                for rec in report["overall_assessment"]["recommendations"]:
                    print(f"  - {rec}")

    except Exception as e:
        print(f"保存报告失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()