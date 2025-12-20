"""
E2E 专用模块
"""

from .golden_path_validator import validate_golden_path_workflow, evaluate_golden_path_coverage

__all__ = [
    "validate_golden_path_workflow",
    "evaluate_golden_path_coverage",
]

