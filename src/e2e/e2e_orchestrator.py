"""
E2E编排器 - 负责协调和管理端到端测试的完整执行流程

基于NAOHAI_TESTING_TODO.md Phase 1.1要求，实现闹海系统7阶段黄金路径的编排管理。

核心功能：
- 工作流执行编排和状态管理
- 性能监控集成和数据收集
- 错误恢复和容错处理
- 截图证据收集和管理
- RF语义化action调度
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from ..models.context import Context
from ..models.action import Action
from ..monitoring.performance_monitor import PerformanceMonitor
from ..utils.recovery_checker import RecoveryChecker
from ..browser_manager import BrowserManager
from ..executor.workflow_executor import WorkflowExecutor


class E2EOrchestrator:
    """
    E2E测试编排器

    负责端到端测试的整体编排，包括：
    - 工作流阶段管理和执行
    - 性能监控和检查点记录
    - 错误恢复和重试机制
    - 截图和证据收集
    - RF语义化action调度
    """

    def __init__(
        self,
        config: Dict[str, Any],
        performance_monitor: PerformanceMonitor,
        recovery_checker: RecoveryChecker
    ):
        """
        初始化E2E编排器

        Args:
            config: 配置信息
            performance_monitor: 性能监控器
            recovery_checker: 恢复检查器
        """
        self.config = config
        self.performance_monitor = performance_monitor
        self.recovery_checker = recovery_checker
        self.logger = logging.getLogger(__name__)

        # 浏览器和工作流执行器
        self.browser_manager: Optional[BrowserManager] = None
        self.workflow_executor: Optional[WorkflowExecutor] = None

        # 执行状态
        self.session_id: Optional[str] = None
        self.current_phase: Optional[str] = None
        self.phase_results: List[Dict[str, Any]] = []
        self.screenshots_taken: int = 0

    async def execute_workflow(
        self,
        workflow: Dict[str, Any],
        context: Context,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行完整的E2E工作流

        Args:
            workflow: 工作流定义
            context: 执行上下文
            session_id: 会话ID

        Returns:
            执行结果报告
        """
        self.session_id = session_id or f"e2e_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"开始执行E2E工作流 - Session: {self.session_id}")

        try:
            # 初始化浏览器和执行器
            await self._initialize_executor()

            # 执行套件初始化步骤
            await self._execute_suite_setup(workflow.get("suite_setup", []), context)

            # 执行核心阶段
            phases = workflow.get("phases", [])
            for i, phase in enumerate(phases):
                phase_name = phase.get("name", f"phase_{i+1}")
                self.current_phase = phase_name

                phase_result = await self._execute_phase(phase, context, i + 1, len(phases))
                self.phase_results.append(phase_result)

                # 检查阶段执行结果
                if not phase_result.get("success", False):
                    # 尝试错误恢复
                    recovery_success = await self._attempt_phase_recovery(phase, context)
                    if not recovery_success:
                        break  # 恢复失败，终止执行

            # 生成最终报告
            final_result = self._generate_final_report(workflow)
            return final_result

        except Exception as e:
            self.logger.error(f"E2E工作流执行异常: {str(e)}", exc_info=True)
            return self._generate_error_report(e)

        finally:
            # 清理资源
            await self._cleanup()

    async def _initialize_executor(self):
        """初始化浏览器和工作流执行器"""
        self.logger.info("初始化浏览器和执行器...")

        # 初始化浏览器管理器
        self.browser_manager = BrowserManager(self.config)
        browser_ok = await self.browser_manager.initialize()
        if not browser_ok:
            raise RuntimeError("浏览器初始化失败")

        # 初始化工作流执行器
        self.workflow_executor = WorkflowExecutor(
            self.config,
            self.browser_manager,
            mcp_observer=None
        )

        self.logger.info("浏览器和执行器初始化完成")

    async def _execute_suite_setup(self, setup_steps: List[Dict[str, Any]], context: Context):
        """执行套件初始化步骤"""
        self.logger.info("执行套件初始化步骤...")

        for step in setup_steps:
            action = Action.create(step["action"], step.get("params", {}))
            timeout = step.get("timeout", self.config.get("test", {}).get("timeout", {}).get("element_load", 10000))

            try:
                # 执行action
                await self._execute_action_with_timeout(action, context, timeout)
                self.logger.debug(f"套件初始化步骤完成: {step['action']}")

            except Exception as e:
                self.logger.error(f"套件初始化步骤失败: {step['action']}, 错误: {str(e)}")
                raise

    async def _execute_phase(
        self,
        phase: Dict[str, Any],
        context: Context,
        phase_index: int,
        total_phases: int
    ) -> Dict[str, Any]:
        """
        执行单个阶段

        Args:
            phase: 阶段定义
            context: 执行上下文
            phase_index: 阶段序号
            total_phases: 总阶段数

        Returns:
            阶段执行结果
        """
        phase_name = phase.get("name", f"phase_{phase_index}")
        phase_description = phase.get("description", "")
        steps = phase.get("steps", [])

        self.logger.info(f"执行阶段 {phase_index}/{total_phases}: {phase_name}")

        # 开始性能监控
        checkpoint_name = f"phase_{phase_index}_{phase_name}"
        await self.performance_monitor.start_checkpoint(self.session_id, checkpoint_name)

        start_time = datetime.now()
        step_results = []

        try:
            # 执行阶段中的所有步骤
            for step in steps:
                step_result = await self._execute_step(step, context)
                step_results.append(step_result)

                # 如果步骤失败且不可跳过，终止阶段执行
                if not step_result.get("success", False) and not step.get("optional", False):
                    break

            duration = (datetime.now() - start_time).total_seconds()
            phase_success = all(step.get("success", False) for step in step_results if not step.get("optional", False))

            # 记录性能检查点
            await self.performance_monitor.end_checkpoint(
                self.session_id,
                checkpoint_name,
                duration,
                phase_success
            )

            phase_result = {
                "phase_index": phase_index,
                "phase_name": phase_name,
                "phase_description": phase_description,
                "success": phase_success,
                "duration": duration,
                "steps_executed": len(step_results),
                "step_results": step_results,
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(f"阶段 {phase_name} 执行完成, 成功: {phase_success}, 耗时: {duration:.2f}秒")
            return phase_result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"阶段 {phase_name} 执行异常: {str(e)}")

            # 记录失败的性能检查点
            await self.performance_monitor.end_checkpoint(
                self.session_id,
                checkpoint_name,
                duration,
                False
            )

            return {
                "phase_index": phase_index,
                "phase_name": phase_name,
                "phase_description": phase_description,
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _execute_step(self, step: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """
        执行单个步骤

        Args:
            step: 步骤定义
            context: 执行上下文

        Returns:
            步骤执行结果
        """
        action_name = step["action"]
        params = step.get("params", {})
        timeout = step.get("timeout", self.config.get("test", {}).get("timeout", {}).get("element_load", 10000))

        start_time = datetime.now()

        try:
            self.logger.debug(f"执行步骤: {action_name}")

            # 创建action并执行
            action = Action.create(action_name, params)

            # 如果是截图action，特殊处理
            if action_name == "screenshot":
                screenshot_result = await self._handle_screenshot_action(action, context)
                self.screenshots_taken += 1
                return screenshot_result

            # 执行普通action
            updated_context = await self._execute_action_with_timeout(action, context, timeout)
            duration = (datetime.now() - start_time).total_seconds()

            return {
                "action": action_name,
                "success": True,
                "duration": duration,
                "context_updated": True
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"步骤执行失败: {action_name}, 错误: {str(e)}")

            return {
                "action": action_name,
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    async def _execute_action_with_timeout(
        self,
        action: Action,
        context: Context,
        timeout: int
    ) -> Context:
        """执行action并处理超时"""
        try:
            return await asyncio.wait_for(
                action.execute(context),
                timeout=timeout / 1000.0  # 转换为秒
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Action执行超时: {action.action}, 超时时间: {timeout}ms")

    async def _handle_screenshot_action(self, action: Action, context: Context) -> Dict[str, Any]:
        """处理截图action的特殊逻辑"""
        try:
            # 执行截图
            updated_context = await action.execute(context)

            # 获取截图路径
            screenshot_path = action.params.get("save_path", f"screenshots/e2e/screenshot_{self.screenshots_taken}.png")

            # 确保目录存在
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)

            return {
                "action": "screenshot",
                "success": True,
                "screenshot_path": screenshot_path,
                "context_updated": True
            }

        except Exception as e:
            return {
                "action": "screenshot",
                "success": False,
                "error": str(e)
            }

    async def _attempt_phase_recovery(self, phase: Dict[str, Any], context: Context) -> bool:
        """尝试阶段错误恢复"""
        self.logger.warning(f"尝试恢复阶段: {phase.get('name', 'unknown')}")

        recovery_steps = self.config.get("error_recovery", [])

        for recovery_step in recovery_steps:
            try:
                action = Action.create(recovery_step["action"], recovery_step.get("params", {}))
                await action.execute(context)
                self.logger.info(f"恢复步骤执行成功: {recovery_step['action']}")

                # 重新执行阶段
                phase_result = await self._execute_phase(phase, context,
                                                   self.phase_results[-1]["phase_index"],
                                                   len(self.phase_results) + 1)

                if phase_result.get("success", False):
                    self.logger.info("阶段恢复成功")
                    return True

            except Exception as e:
                self.logger.error(f"恢复步骤失败: {recovery_step['action']}, 错误: {str(e)}")

        self.logger.error("阶段恢复失败")
        return False

    def _generate_final_report(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终执行报告"""
        total_duration = sum(phase.get("duration", 0) for phase in self.phase_results)
        successful_phases = sum(1 for phase in self.phase_results if phase.get("success", False))
        total_phases = len(self.phase_results)

        return {
            "session_id": self.session_id,
            "workflow_name": workflow.get("name", "unknown"),
            "success": successful_phases == total_phases and total_phases > 0,
            "total_duration": total_duration,
            "phase_results": self.phase_results,
            "summary": {
                "total_phases": total_phases,
                "successful_phases": successful_phases,
                "success_rate": successful_phases / total_phases if total_phases > 0 else 0,
                "screenshots_taken": self.screenshots_taken
            },
            "timestamp": datetime.now().isoformat()
        }

    def _generate_error_report(self, error: Exception) -> Dict[str, Any]:
        """生成错误报告"""
        return {
            "session_id": self.session_id,
            "success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": str(error.__traceback__) if error.__traceback__ else None
            },
            "phase_results": self.phase_results,
            "summary": {
                "total_phases": len(self.phase_results),
                "successful_phases": sum(1 for phase in self.phase_results if phase.get("success", False)),
                "screenshots_taken": self.screenshots_taken
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _cleanup(self):
        """清理资源"""
        self.logger.info("清理E2E编排器资源...")

        if self.browser_manager:
            try:
                await self.browser_manager.close()
            except Exception as e:
                self.logger.warning(f"浏览器清理异常: {str(e)}")

        self.browser_manager = None
        self.workflow_executor = None