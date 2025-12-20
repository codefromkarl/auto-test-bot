#!/usr/bin/env python3
"""
Base Task Processor for Naohai Testing Framework
为所有任务处理器提供统一的基础抽象类
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TaskResult:
    """任务结果数据类"""
    task_id: str
    task_type: str
    status: str
    timestamp: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseTaskProcessor(ABC):
    """任务处理器基础抽象类"""

    def __init__(self, config: Dict[str, Any], processor_name: str):
        self.config = config
        self.processor_name = processor_name
        self.output_dir = Path(f"workspace/{processor_name}_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 性能优化：缓存配置结果
        self._execution_config = None
        self._timeout = None

    @property
    def execution_config(self) -> Dict[str, Any]:
        """获取执行配置（带缓存）"""
        if self._execution_config is None:
            self._execution_config = self.config.get("execution_modes", {}).get(
                self.processor_name, {}
            )
        return self._execution_config

    @property
    def timeout(self) -> int:
        """获取超时配置（带缓存）"""
        if self._timeout is None:
            self._timeout = self.execution_config.get("timeout", 600)
        return self._timeout

    @abstractmethod
    async def execute_task(self, task_config: Dict[str, Any]) -> TaskResult:
        """执行任务的具体实现 - 子类必须实现"""
        pass

    def create_task_result(self, task_type: str, task_config: Dict[str, Any]) -> TaskResult:
        """创建标准化的任务结果对象"""
        return TaskResult(
            task_id=f"{self.processor_name}_{task_type}_{int(time.time())}",
            task_type=task_type,
            status="initialized",
            timestamp=time.time(),
            metadata={"config": task_config, "processor": self.processor_name}
        )

    async def execute_with_timeout(self, task_func, *args, **kwargs):
        """带超时的任务执行"""
        import asyncio
        try:
            return await asyncio.wait_for(task_func(*args, **kwargs), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Task execution timed out after {self.timeout} seconds")

    def save_task_result(self, result: TaskResult):
        """保存任务结果"""
        output_file = self.output_dir / f"{result.task_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # 转换TaskResult为字典
            result_dict = {
                "task_id": result.task_id,
                "task_type": result.task_type,
                "status": result.status,
                "timestamp": result.timestamp,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "metadata": result.metadata
            }
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

    def log_task_start(self, task_result: TaskResult):
        """记录任务开始"""
        print(f"[{self.processor_name}] Starting task: {task_result.task_id}")
        task_result.status = "running"
        task_result.metadata = task_result.metadata or {}
        task_result.metadata["start_time"] = time.time()

    def log_task_complete(self, task_result: TaskResult):
        """记录任务完成"""
        if task_result.metadata and "start_time" in task_result.metadata:
            task_result.execution_time = time.time() - task_result.metadata["start_time"]

        status_emoji = "✅" if task_result.status == "completed" else "❌"
        print(f"[{self.processor_name}] {status_emoji} Task completed: {task_result.task_id} "
              f"(took {task_result.execution_time:.2f}s)")

    def validate_config(self) -> List[str]:
        """验证配置的有效性"""
        errors = []

        if not isinstance(self.config, dict):
            errors.append("Configuration must be a dictionary")
            return errors

        if "execution_modes" not in self.config:
            errors.append("Missing 'execution_modes' in configuration")
            return errors

        processor_config = self.config.get("execution_modes", {}).get(self.processor_name)
        if not processor_config:
            errors.append(f"Missing configuration for processor '{self.processor_name}'")

        return errors

    async def cleanup(self):
        """清理资源 - 子类可以重写"""
        pass

class MCPIntegrationMixin:
    """MCP集成混入类 - 提供统一的MCP调用方法"""

    async def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一的MCP工具调用方法
        优先使用直接API调用，fallback到subprocess
        """
        try:
            # 优先尝试直接API调用
            return await self._direct_mcp_call(tool_name, parameters)
        except Exception as e:
            print(f"Direct MCP call failed, falling back to subprocess: {e}")
            return await self._subprocess_mcp_call(tool_name, parameters)

    async def _direct_mcp_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """直接MCP API调用"""
        # 这里应该实现直接的MCP API调用
        # 目前先返回模拟结果
        return {
            "success": True,
            "method": "direct_api",
            "tool": tool_name,
            "parameters": parameters
        }

    async def _subprocess_mcp_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """subprocess fallback调用"""
        import subprocess
        import os

        cmd = self._build_mcp_command(tool_name, parameters)

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return {
                "success": result.returncode == 0,
                "method": "subprocess",
                "tool": tool_name,
                "output": result.stdout,
                "error": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"MCP call timeout after {self.timeout} seconds"
            }

    def _build_mcp_command(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """构建MCP命令"""
        # 根据工具类型构建不同的命令
        if tool_name == "gemini":
            return f"cd {os.getcwd()} && gemini -p \"{parameters.get('prompt', '')}\" --approval-mode yolo"
        elif tool_name == "codex":
            return f"codex -C {os.getcwd()} --full-auto exec \"{parameters.get('prompt', '')}\" --skip-git-repo-check -s danger-full-access"
        else:
            raise ValueError(f"Unsupported MCP tool: {tool_name}")