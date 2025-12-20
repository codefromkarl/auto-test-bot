#!/usr/bin/env python3
"""
Enhanced Configuration Manager for Naohai Testing Framework
提供配置验证、动态加载和缓存功能
"""

import json
import yaml
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class ConfigValidationLevel(Enum):
    """配置验证级别"""
    STRICT = "strict"  # 严格模式，所有错误都阻止执行
    WARN = "warn"      # 警告模式，记录警告但继续执行
    LOOSE = "loose"    # 宽松模式，只检查关键配置

@dataclass
class ValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validation_level: ConfigValidationLevel

class EnhancedConfigManager:
    """增强配置管理器"""

    def __init__(self, config_path: str, validation_level: ConfigValidationLevel = ConfigValidationLevel.WARN):
        self.config_path = Path(config_path)
        self.validation_level = validation_level
        self._config_cache = None
        self._last_modified = None

        # 配置架构定义
        self.config_schema = self._define_schema()

    def _define_schema(self) -> Dict[str, Any]:
        """定义配置架构"""
        return {
            "required_fields": {
                "executor_type": str,
                "execution_modes": dict,
                "workflow_phases": dict
            },
            "optional_fields": {
                "task_allocation": dict,
                "parallel_control": dict,
                "error_handling": dict,
                "coordination": dict,
                "output": dict
            },
            "execution_mode_schema": {
                "mode": str,
                "timeout": int,
                "retry_count": int,
                "parallel_limit": int
            }
        }

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置（带缓存）

        Args:
            force_reload: 强制重新加载

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误
        """
        # 检查文件是否被修改
        if not force_reload and self._config_cache is not None:
            current_modified = self.config_path.stat().st_mtime
            if current_modified == self._last_modified:
                return self._config_cache

        # 加载配置文件
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    config = json.load(f)
                elif self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config format: {self.config_path.suffix}")

        except Exception as e:
            raise ValueError(f"Failed to parse configuration: {e}")

        # 验证配置
        validation_result = self.validate_config(config)

        if not validation_result.is_valid:
            if self.validation_level == ConfigValidationLevel.STRICT:
                error_msg = "Configuration validation failed:\n" + "\n".join(validation_result.errors)
                raise ValueError(error_msg)
            elif self.validation_level == ConfigValidationLevel.WARN:
                print("⚠️ Configuration validation warnings:")
                for error in validation_result.errors:
                    print(f"  - {error}")

        # 显示警告
        if validation_result.warnings:
            print("⚠️ Configuration warnings:")
            for warning in validation_result.warnings:
                print(f"  - {warning}")

        # 更新缓存
        self._config_cache = config
        self._last_modified = self.config_path.stat().st_mtime

        return config

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置的有效性"""
        errors = []
        warnings = []

        # 检查必需字段
        for field, field_type in self.config_schema["required_fields"].items():
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(config[field], field_type):
                errors.append(f"Field '{field}' should be of type {field_type.__name__}")

        # 验证execution_modes结构
        if "execution_modes" in config:
            execution_modes = config["execution_modes"]
            for mode_name, mode_config in execution_modes.items():
                mode_errors = self._validate_execution_mode(mode_name, mode_config)
                errors.extend(mode_errors)

        # 验证workflow_phases
        if "workflow_phases" in config:
            phase_errors = self._validate_workflow_phases(config["workflow_phases"])
            errors.extend(phase_errors)

        # 验证可选字段
        for field, field_type in self.config_schema["optional_fields"].items():
            if field in config and not isinstance(config[field], field_type):
                errors.append(f"Optional field '{field}' should be of type {field_type.__name__}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, self.validation_level)

    def _validate_execution_mode(self, mode_name: str, mode_config: Any) -> List[str]:
        """验证单个execution_mode配置"""
        errors = []

        if not isinstance(mode_config, dict):
            errors.append(f"Execution mode '{mode_name}' should be a dictionary")
            return errors

        schema = self.config_schema["execution_mode_schema"]
        for field, field_type in schema.items():
            if field not in mode_config:
                errors.append(f"Execution mode '{mode_name}' missing required field: {field}")
            elif not isinstance(mode_config[field], field_type):
                errors.append(f"Execution mode '{mode_name}' field '{field}' should be {field_type.__name__}")

        # 验证超时值
        if "timeout" in mode_config and mode_config["timeout"] <= 0:
            errors.append(f"Execution mode '{mode_name}' timeout must be positive")

        # 验证重试次数
        if "retry_count" in mode_config and mode_config["retry_count"] < 0:
            errors.append(f"Execution mode '{mode_name}' retry_count must be non-negative")

        return errors

    def _validate_workflow_phases(self, phases: Any) -> List[str]:
        """验证workflow_phases配置"""
        errors = []

        if not isinstance(phases, dict):
            errors.append("workflow_phases should be a dictionary")
            return errors

        for phase_name, phase_config in phases.items():
            if not isinstance(phase_config, dict):
                errors.append(f"Phase '{phase_name}' should be a dictionary")
                continue

            if "tasks" not in phase_config:
                errors.append(f"Phase '{phase_name}' missing 'tasks' field")
                continue

            if not isinstance(phase_config["tasks"], list):
                errors.append(f"Phase '{phase_name}' tasks should be a list")
                continue

            for i, task in enumerate(phase_config["tasks"]):
                task_errors = self._validate_task(phase_name, i, task)
                errors.extend(task_errors)

        return errors

    def _validate_task(self, phase_name: str, task_index: int, task: Any) -> List[str]:
        """验证单个任务配置"""
        errors = []

        if not isinstance(task, dict):
            errors.append(f"Phase '{phase_name}' task {task_index} should be a dictionary")
            return errors

        required_task_fields = ["name", "executor", "task_type"]
        for field in required_task_fields:
            if field not in task:
                errors.append(f"Phase '{phase_name}' task {task_index} missing required field: {field}")

        # 验证executor值
        if "executor" in task and task["executor"] not in ["gemini", "codex", "claude"]:
            errors.append(f"Phase '{phase_name}' task {task_index} has invalid executor: {task['executor']}")

        return errors

    def get_execution_config(self, processor_name: str) -> Dict[str, Any]:
        """获取特定处理器的执行配置"""
        config = self.load_config()
        return config.get("execution_modes", {}).get(processor_name, {})

    def get_task_allocation(self, processor_name: str) -> List[str]:
        """获取处理器的任务分配"""
        config = self.load_config()
        task_allocation = config.get("task_allocation", {})
        return task_allocation.get(f"{processor_name}_tasks", [])

    def get_workflow_phases(self) -> Dict[str, Any]:
        """获取工作流阶段配置"""
        config = self.load_config()
        return config.get("workflow_phases", {})

    def update_config(self, updates: Dict[str, Any], save_to_file: bool = False) -> Dict[str, Any]:
        """更新配置"""
        config = self.load_config()

        # 深度合并更新
        def deep_merge(base: Dict, updates: Dict) -> Dict:
            result = base.copy()
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        updated_config = deep_merge(config, updates)

        # 验证更新后的配置
        validation_result = self.validate_config(updated_config)
        if not validation_result.is_valid:
            error_msg = "Updated configuration validation failed:\n" + "\n".join(validation_result.errors)
            raise ValueError(error_msg)

        # 保存到文件
        if save_to_file:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(updated_config, f, default_flow_style=False, allow_unicode=True)

            # 清除缓存以强制重新加载
            self._config_cache = None
            self._last_modified = None
        else:
            # 更新缓存
            self._config_cache = updated_config

        return updated_config

    def get_output_config(self) -> Dict[str, str]:
        """获取输出配置"""
        config = self.load_config()
        output_config = config.get("output", {})

        # 设置默认值
        defaults = {
            "gemini_output": "workspace/gemini_outputs",
            "codex_output": "workspace/codex_outputs",
            "claude_output": "workspace/claude_outputs"
        }

        for key, default_value in defaults.items():
            if key not in output_config:
                output_config[key] = default_value

        return output_config

    def create_directories(self):
        """创建配置中定义的目录"""
        config = self.load_config()

        # 创建输出目录
        output_config = config.get("output", {})
        for key, path in output_config.items():
            if key.endswith("_output"):
                Path(path).mkdir(parents=True, exist_ok=True)

        # 创建workspace目录
        Path("workspace").mkdir(exist_ok=True)

# 配置工厂函数
def create_config_manager(config_path: str, validation_level: ConfigValidationLevel = ConfigValidationLevel.WARN) -> EnhancedConfigManager:
    """创建配置管理器实例"""
    return EnhancedConfigManager(config_path, validation_level)