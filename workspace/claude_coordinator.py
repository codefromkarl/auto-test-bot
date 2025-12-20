#!/usr/bin/env python3
"""
Claude Workflow Coordinator for Naohai Parallel Testing
负责协调Gemini和Codex任务执行，聚合结果，生成报告
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from gemini_tasks import GeminiUITasks
from codex_tasks import CodexFunctionalTasks

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task_type: str
    executor: str
    phase: str
    dependencies: List[str]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class ClaudeWorkflowCoordinator:
    """Claude工作流协调器"""

    def __init__(self, config_path: str = "workspace/parallel_executor_config.yaml"):
        self.config = self._load_config(config_path)
        self.gemini_tasks = GeminiUITasks(self.config)
        self.codex_tasks = CodexFunctionalTasks(self.config)

        self.workspace_dir = Path("workspace")
        self.output_dir = Path("workspace/claude_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tasks: Dict[str, TaskInfo] = {}
        self.phase_results: Dict[str, List[Dict[str, Any]]] = {}
        self.global_status = {
            "started_at": time.time(),
            "current_phase": None,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "current_status": "initialized"
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    async def orchestrate_workflow(self) -> Dict[str, Any]:
        """
        编排并执行完整工作流
        """
        self.global_status["current_status"] = "running"
        self.global_status["started_at"] = time.time()

        try:
            # 初始化任务
            self._initialize_tasks()

            # 按阶段执行任务
            for phase_name, phase_config in self.config.get("workflow_phases", {}).items():
                await self._execute_phase(phase_name, phase_config)

                # 检查同步点
                if not await self._check_sync_point(phase_name):
                    break

            # 生成聚合报告
            final_report = await self._generate_final_report()

            self.global_status["current_status"] = "completed"
            return final_report

        except Exception as e:
            self.global_status["current_status"] = "failed"
            self.global_status["error"] = str(e)
            return await self._generate_error_report(e)

    def _initialize_tasks(self):
        """初始化所有任务"""
        workflow_phases = self.config.get("workflow_phases", {})
        task_counter = 0

        for phase_name, phase_config in workflow_phases.items():
            tasks = phase_config.get("tasks", [])

            for task in tasks:
                task_id = f"{task['executor']}_{task['task_type']}_{int(time.time())}_{task_counter}"

                task_info = TaskInfo(
                    task_id=task_id,
                    task_type=task["task_type"],
                    executor=task["executor"],
                    phase=phase_name,
                    dependencies=task.get("dependencies", [])
                )

                self.tasks[task_id] = task_info
                task_counter += 1

        self.global_status["total_tasks"] = len(self.tasks)
        self._save_status()

    async def _execute_phase(self, phase_name: str, phase_config: Dict[str, Any]):
        """执行单个阶段"""
        self.global_status["current_phase"] = phase_name
        phase_start_time = time.time()

        # 获取阶段任务
        phase_tasks = [task for task in self.tasks.values() if task.phase == phase_name]

        # 按依赖关系排序
        sorted_tasks = self._sort_tasks_by_dependencies(phase_tasks)

        # 并行执行无依赖任务
        task_groups = self._group_tasks_by_dependencies(sorted_tasks)

        for group in task_groups:
            if group:
                await self._execute_task_group(group, phase_name)

        # 阶段完成处理
        phase_end_time = time.time()
        phase_duration = phase_end_time - phase_start_time

        self.phase_results[phase_name] = [
            {
                "task_id": task.task_id,
                "status": task.status.value,
                "result": task.result,
                "error": task.error
            }
            for task in phase_tasks
        ]

        await self._handle_phase_completion(phase_name, phase_duration)

    def _sort_tasks_by_dependencies(self, tasks: List[TaskInfo]) -> List[TaskInfo]:
        """根据依赖关系排序任务"""
        sorted_tasks = []
        remaining_tasks = tasks.copy()

        while remaining_tasks:
            # 找出无依赖或依赖已满足的任务
            ready_tasks = []
            for task in remaining_tasks:
                if all(dep in [t.task_id for t in sorted_tasks] for dep in task.dependencies):
                    ready_tasks.append(task)

            if not ready_tasks:
                # 循环依赖检测
                raise Exception(f"循环依赖检测: {remaining_tasks}")

            sorted_tasks.extend(ready_tasks)
            for task in ready_tasks:
                remaining_tasks.remove(task)

        return sorted_tasks

    def _group_tasks_by_dependencies(self, sorted_tasks: List[TaskInfo]) -> List[List[TaskInfo]]:
        """将任务分组，同组内任务可并行执行"""
        groups = []
        processed_tasks = set()

        for task in sorted_tasks:
            if task.task_id in processed_tasks:
                continue

            # 检查依赖
            if all(dep in processed_tasks for dep in task.dependencies):
                # 找到可以并行执行的任务
                current_group = [task]
                processed_tasks.add(task.task_id)

                # 查找其他无依赖的任务
                for other_task in sorted_tasks:
                    if (other_task.task_id not in processed_tasks and
                        all(dep in processed_tasks for dep in other_task.dependencies)):
                        current_group.append(other_task)
                        processed_tasks.add(other_task.task_id)

                groups.append(current_group)

        return groups

    async def _execute_task_group(self, task_group: List[TaskInfo], phase_name: str):
        """执行任务组"""
        # 启动所有任务
        tasks_futures = []
        for task in task_group:
            task.status = TaskStatus.RUNNING
            task.start_time = time.time()
            self._save_status()

            if task.executor == "gemini":
                future = self._execute_gemini_task(task)
            elif task.executor == "codex":
                future = self._execute_codex_task(task)
            else:
                future = self._execute_claude_task(task)

            tasks_futures.append(future)

        # 等待所有任务完成
        try:
            max_concurrent = self.config.get("parallel_control", {}).get("max_concurrent_tasks", 5)
            timeout = self.config.get("execution_modes", {}).get("gemini", {}).get("timeout", 600)

            results = await asyncio.wait_for(
                asyncio.gather(*tasks_futures, return_exceptions=True),
                timeout=timeout
            )

            # 处理结果
            for i, result in enumerate(results):
                task = task_group[i]
                task.end_time = time.time()

                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.error = str(result)
                    self.global_status["failed_tasks"] += 1
                else:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    self.global_status["completed_tasks"] += 1

        except asyncio.TimeoutError:
            # 处理超时
            for task in task_group:
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.FAILED
                    task.error = "Task execution timeout"
                    task.end_time = time.time()
                    self.global_status["failed_tasks"] += 1

        self._save_status()

    async def _execute_gemini_task(self, task: TaskInfo) -> Dict[str, Any]:
        """执行Gemini UI分析任务"""
        if task.task_type == "ui_analysis":
            return await self.gemini_tasks.analyze_page_layout(
                url=self.config.get("test", {}).get("url", "")
            )
        elif task.task_type == "element_visibility_check":
            return await self.gemini_tasks.validate_element_visibility(
                selectors=self.config.get("test", {}).get("selectors", {})
            )
        elif task.task_type == "screenshot_analysis":
            return await self.gemini_tasks.analyze_screenshot_quality(
                screenshot_path="screenshots/latest.png",
                expected_content=self.config.get("test", {}).get("test_prompt", "")
            )
        elif task.task_type == "responsiveness_test":
            return await self.gemini_tasks.check_responsiveness(
                viewports=[
                    {"width": 1920, "height": 1080},
                    {"width": 768, "height": 1024},
                    {"width": 375, "height": 667}
                ]
            )
        elif task.task_type == "accessibility_check":
            return await self.gemini_tasks.check_accessibility()
        elif task.task_type == "dom_structure_validation":
            return await self.gemini_tasks.validate_dom_structure()
        else:
            raise Exception(f"未知的Gemini任务类型: {task.task_type}")

    async def _execute_codex_task(self, task: TaskInfo) -> Dict[str, Any]:
        """执行Codex功能测试任务"""
        if task.task_type == "workflow_execution":
            return await self.codex_tasks.execute_workflow_test({
                "url": self.config.get("test", {}).get("url", ""),
                "test_prompt": self.config.get("test", {}).get("test_prompt", ""),
                "steps": self.config.get("steps", {})
            })
        elif task.task_type == "functional_test":
            return await self.codex_tasks.test_functional_requirements(
                feature="ai_creation"
            )
        elif task.task_type == "api_validation":
            return await self.codex_tasks.validate_api_integration([
                {"endpoint": "/api/generate", "method": "POST"},
                {"endpoint": "/api/status", "method": "GET"}
            ])
        elif task.task_type == "data_flow_test":
            return await self.codex_tasks.test_data_flow({
                "input": self.config.get("test", {}).get("test_prompt", ""),
                "output_format": "image"
            })
        elif task.task_type == "business_logic_test":
            return await self.codex_tasks.test_business_logic([
                {"rule": "content_generation", "expected": "valid_output"}
            ])
        elif task.task_type == "error_handling_test":
            return await self.codex_tasks.test_error_handling([
                {"scenario": "network_failure"},
                {"scenario": "invalid_input"}
            ])
        elif task.task_type == "integration_test":
            return await self.codex_tasks.test_integration([
                {"component": "ui", "interface": "api"}
            ])
        elif task.task_type == "performance_test":
            return await self.codex_tasks.test_performance({
                "response_time_threshold": 5.0,
                "throughput_threshold": 100
            })
        else:
            raise Exception(f"未知的Codex任务类型: {task.task_type}")

    async def _execute_claude_task(self, task: TaskInfo) -> Dict[str, Any]:
        """执行Claude协调任务"""
        if task.task_type == "workflow_orchestration":
            return {"status": "completed", "message": "Workflow orchestrated successfully"}
        elif task.task_type == "result_aggregation":
            return await self._aggregate_results()
        elif task.task_type == "decision_making":
            return await self._make_decisions()
        elif task.task_type == "error_recovery":
            return await self._recover_from_errors()
        elif task.task_type == "report_generation":
            return await self._generate_interim_report()
        elif task.task_type == "task_prioritization":
            return await self._prioritize_tasks()
        else:
            raise Exception(f"未知的Claude任务类型: {task.task_type}")

    async def _check_sync_point(self, phase_name: str) -> bool:
        """检查同步点"""
        sync_points = self.config.get("parallel_control", {}).get("sync_points", [])
        for sync_point in sync_points:
            if sync_point.get("after") == phase_name:
                # 检查阶段是否成功
                phase_success = all(
                    task.status == TaskStatus.COMPLETED
                    for task in self.tasks.values()
                    if task.phase == phase_name
                )

                if not phase_success:
                    error_handling_mode = self.config.get("error_handling", {}).get("failure_mode", "continue_on_failure")
                    if error_handling_mode == "stop_on_failure":
                        return False

        return True

    async def _handle_phase_completion(self, phase_name: str, duration: float):
        """处理阶段完成"""
        # 保存阶段结果
        phase_summary = {
            "phase": phase_name,
            "duration": duration,
            "status": "completed" if all(
                task.status == TaskStatus.COMPLETED
                for task in self.tasks.values()
                if task.phase == phase_name
            ) else "failed",
            "tasks": self.phase_results[phase_name],
            "timestamp": time.time()
        }

        phase_file = self.output_dir / f"phase_{phase_name}_summary.json"
        with open(phase_file, 'w', encoding='utf-8') as f:
            json.dump(phase_summary, f, ensure_ascii=False, indent=2)

    async def _aggregate_results(self) -> Dict[str, Any]:
        """聚合所有结果"""
        aggregated = {
            "gemini_results": {},
            "codex_results": {},
            "claude_results": {},
            "summary": {
                "total_tasks": self.global_status["total_tasks"],
                "completed_tasks": self.global_status["completed_tasks"],
                "failed_tasks": self.global_status["failed_tasks"],
                "success_rate": self.global_status["completed_tasks"] / max(self.global_status["total_tasks"], 1)
            }
        }

        for task_id, task in self.tasks.items():
            if task.result:
                if task.executor == "gemini":
                    aggregated["gemini_results"][task_id] = task.result
                elif task.executor == "codex":
                    aggregated["codex_results"][task_id] = task.result
                elif task.executor == "claude":
                    aggregated["claude_results"][task_id] = task.result

        return aggregated

    async def _make_decisions(self) -> Dict[str, Any]:
        """基于结果做出决策"""
        decisions = {
            "continue_workflow": True,
            "next_actions": [],
            "quality_gates": {},
            "recommendations": []
        }

        # 检查质量门禁
        for phase_name, phase_results in self.phase_results.items():
            success_rate = sum(1 for result in phase_results if result["status"] == "completed") / len(phase_results)

            if success_rate < 0.8:  # 80%成功率阈值
                decisions["quality_gates"][phase_name] = "failed"
                decisions["continue_workflow"] = False
                decisions["recommendations"].append(f"阶段 {phase_name} 成功率过低: {success_rate:.2%}")

        return decisions

    async def _recover_from_errors(self) -> Dict[str, Any]:
        """从错误中恢复"""
        recovery_actions = []

        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.FAILED:
                # 分析错误并尝试恢复
                if "timeout" in task.error.lower():
                    recovery_actions.append({
                        "task": task_id,
                        "action": "retry_with_timeout",
                        "new_timeout": self.config.get("retry", {}).get("timeout_multiplier", 2) * 60
                    })
                elif "network" in task.error.lower():
                    recovery_actions.append({
                        "task": task_id,
                        "action": "retry_with_retry",
                        "max_attempts": self.config.get("retry", {}).get("max_attempts", 3)
                    })

        return {"recovery_actions": recovery_actions, "recovery_possible": len(recovery_actions) > 0}

    async def _generate_interim_report(self) -> Dict[str, Any]:
        """生成临时报告"""
        return {
            "report_type": "interim",
            "timestamp": time.time(),
            "global_status": self.global_status,
            "current_phase": self.global_status.get("current_phase"),
            "progress": {
                "completed_percentage": self.global_status["completed_tasks"] / max(self.global_status["total_tasks"], 1),
                "current_phase_progress": "calculating..."
            }
        }

    async def _prioritize_tasks(self) -> Dict[str, Any]:
        """任务优先级排序"""
        prioritized_tasks = []

        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                priority = self._calculate_task_priority(task)
                prioritized_tasks.append({
                    "task_id": task_id,
                    "priority": priority,
                    "executor": task.executor,
                    "type": task.task_type
                })

        prioritized_tasks.sort(key=lambda x: x["priority"], reverse=True)
        return {"prioritized_tasks": prioritized_tasks}

    def _calculate_task_priority(self, task: TaskInfo) -> int:
        """计算任务优先级"""
        base_priority = 100

        # 基于任务类型的优先级
        type_priority = {
            "workflow_execution": 10,
            "functional_test": 9,
            "ui_analysis": 8,
            "api_validation": 7,
            "integration_test": 6
        }

        base_priority += type_priority.get(task.task_type, 0)

        # 基于依赖的优先级调整
        dependency_penalty = len(task.dependencies) * 5

        return base_priority - dependency_penalty

    async def _generate_final_report(self) -> Dict[str, Any]:
        """生成最终报告"""
        # 聚合所有结果
        aggregated_results = await self._aggregate_results()

        # 生成决策
        decisions = await self._make_decisions()

        # 计算总体指标
        total_duration = time.time() - self.global_status["started_at"]

        final_report = {
            "report_type": "final",
            "timestamp": time.time(),
            "execution_summary": {
                "total_duration": total_duration,
                "total_tasks": self.global_status["total_tasks"],
                "completed_tasks": self.global_status["completed_tasks"],
                "failed_tasks": self.global_status["failed_tasks"],
                "success_rate": self.global_status["completed_tasks"] / max(self.global_status["total_tasks"], 1)
            },
            "phase_results": self.phase_results,
            "aggregated_results": aggregated_results,
            "decisions": decisions,
            "quality_assessment": {
                "ui_quality_score": self._calculate_ui_quality_score(),
                "functional_quality_score": self._calculate_functional_quality_score(),
                "overall_quality_score": 0.0
            },
            "recommendations": await self._generate_recommendations(),
            "artifacts": {
                "screenshots": "screenshots/",
                "logs": "logs/",
                "gemini_outputs": "workspace/gemini_outputs/",
                "codex_outputs": "workspace/codex_outputs/"
            }
        }

        # 保存最终报告
        report_file = self.output_dir / "naohai_final_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)

        # 生成HTML报告
        await self._generate_html_report(final_report)

        return final_report

    def _calculate_ui_quality_score(self) -> float:
        """计算UI质量分数"""
        ui_tasks = [task for task in self.tasks.values() if task.executor == "gemini"]
        if not ui_tasks:
            return 0.0

        completed_ui_tasks = [task for task in ui_tasks if task.status == TaskStatus.COMPLETED]
        return len(completed_ui_tasks) / len(ui_tasks)

    def _calculate_functional_quality_score(self) -> float:
        """计算功能质量分数"""
        functional_tasks = [task for task in self.tasks.values() if task.executor == "codex"]
        if not functional_tasks:
            return 0.0

        completed_functional_tasks = [task for task in functional_tasks if task.status == TaskStatus.COMPLETED]
        return len(completed_functional_tasks) / len(functional_tasks)

    async def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于失败任务的建议
        failed_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.FAILED]
        if failed_tasks:
            recommendations.append(f"修复 {len(failed_tasks)} 个失败任务")

            # 按错误类型分组
            error_types = {}
            for task in failed_tasks:
                if task.error:
                    error_type = "timeout" if "timeout" in task.error.lower() else "other"
                    error_types[error_type] = error_types.get(error_type, 0) + 1

            for error_type, count in error_types.items():
                if error_type == "timeout":
                    recommendations.append(f"增加任务超时时间 ({count} 个任务超时)")

        # 基于成功率的建议
        success_rate = self.global_status["completed_tasks"] / max(self.global_status["total_tasks"], 1)
        if success_rate < 0.9:
            recommendations.append("提升测试稳定性，当前成功率为 {:.1%}".format(success_rate))

        return recommendations

    async def _generate_html_report(self, report_data: Dict[str, Any]):
        """生成HTML报告"""
        html_template = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>闹海并行测试报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background: #f5f5f5; padding: 20px; border-radius: 8px; }
                .section { margin: 20px 0; }
                .success { color: green; }
                .failure { color: red; }
                .pending { color: orange; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>闹海并行测试报告</h1>
                <p>生成时间: {timestamp}</p>
            </div>

            <div class="section">
                <h2>执行摘要</h2>
                <table>
                    <tr><th>指标</th><th>数值</th></tr>
                    <tr><td>总任务数</td><td>{total_tasks}</td></tr>
                    <tr><td>完成任务数</td><td class="success">{completed_tasks}</td></tr>
                    <tr><td>失败任务数</td><td class="failure">{failed_tasks}</td></tr>
                    <tr><td>成功率</td><td>{success_rate:.1%}</td></tr>
                    <tr><td>总耗时</td><td>{total_duration:.2f}秒</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>阶段结果</h2>
                {phase_details}
            </div>

            <div class="section">
                <h2>质量评估</h2>
                <table>
                    <tr><th>质量维度</th><th>分数</th></tr>
                    <tr><td>UI质量分数</td><td>{ui_quality_score:.1%}</td></tr>
                    <tr><td>功能质量分数</td><td>{functional_quality_score:.1%}</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>改进建议</h2>
                <ul>
                    {recommendations}
                </ul>
            </div>
        </body>
        </html>
        """

        # 填充模板数据
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(report_data["timestamp"]))
        total_tasks = report_data["execution_summary"]["total_tasks"]
        completed_tasks = report_data["execution_summary"]["completed_tasks"]
        failed_tasks = report_data["execution_summary"]["failed_tasks"]
        success_rate = report_data["execution_summary"]["success_rate"]
        total_duration = report_data["execution_summary"]["total_duration"]
        ui_quality_score = report_data["quality_assessment"]["ui_quality_score"]
        functional_quality_score = report_data["quality_assessment"]["functional_quality_score"]

        # 生成阶段详情
        phase_details = ""
        for phase_name, phase_results in report_data["phase_results"].items():
            phase_details += f"<h3>{phase_name}</h3><table><tr><th>任务ID</th><th>状态</th></tr>"
            for result in phase_results:
                status_class = result["status"]
                phase_details += f'<tr><td>{result["task_id"]}</td><td class="{status_class}">{result["status"]}</td></tr>'
            phase_details += "</table>"

        # 生成建议列表
        recommendations = "".join([f"<li>{rec}</li>" for rec in report_data["recommendations"]])

        html_content = html_template.format(
            timestamp=timestamp,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            success_rate=success_rate,
            total_duration=total_duration,
            ui_quality_score=ui_quality_score,
            functional_quality_score=functional_quality_score,
            phase_details=phase_details,
            recommendations=recommendations
        )

        # 保存HTML报告
        html_file = Path("reports/naohai_parallel_test_report.html")
        html_file.parent.mkdir(exist_ok=True)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    async def _generate_error_report(self, error: Exception) -> Dict[str, Any]:
        """生成错误报告"""
        error_report = {
            "report_type": "error",
            "timestamp": time.time(),
            "error": str(error),
            "execution_summary": self.global_status,
            "partial_results": self.phase_results
        }

        error_file = self.output_dir / "error_report.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, ensure_ascii=False, indent=2)

        return error_report

    def _save_status(self):
        """保存状态"""
        status_file = self.workspace_dir / "workflow_status.json"
        status_data = {
            "global_status": self.global_status,
            "tasks": {
                task_id: {
                    "task_type": task.task_type,
                    "executor": task.executor,
                    "phase": task.phase,
                    "status": task.status.value,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                    "error": task.error
                }
                for task_id, task in self.tasks.items()
            }
        }

        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

async def main():
    """主函数"""
    coordinator = ClaudeWorkflowCoordinator()

    print("🚀 启动闹海并行测试工作流...")
    print("=" * 60)

    try:
        final_report = await coordinator.orchestrate_workflow()

        print("\n✅ 工作流执行完成!")
        print(f"📊 成功率: {final_report['execution_summary']['success_rate']:.1%}")
        print(f"⏱️ 总耗时: {final_report['execution_summary']['total_duration']:.2f}秒")
        print(f"📄 报告位置: reports/naohai_parallel_test_report.html")

        if final_report.get("recommendations"):
            print("\n💡 改进建议:")
            for rec in final_report["recommendations"]:
                print(f"  • {rec}")

    except Exception as e:
        print(f"\n❌ 工作流执行失败: {str(e)}")
        print("📄 错误报告: workspace/claude_outputs/error_report.json")

if __name__ == "__main__":
    asyncio.run(main())