"""
用户旅程看板模块
实现时间轴式测试报告展示，包含截图预览、体验评分和问题标记
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    BLOCKED = "blocked"


class IssueSeverity(Enum):
    """问题严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class JourneyStep:
    """旅程步骤数据结构"""
    id: str
    name: str
    status: StepStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    description: str = ""
    screenshots: List[str] = None
    artifacts: List[Dict[str, str]] = None
    issues: List[Dict[str, Any]] = None
    metrics: Dict[str, Any] = None
    user_experience_score: Optional[float] = None

    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
        if self.artifacts is None:
            self.artifacts = []
        if self.issues is None:
            self.issues = []
        if self.metrics is None:
            self.metrics = {}


@dataclass
class ExperienceScore:
    """体验评分数据结构"""
    overall_score: float
    usability_score: float
    performance_score: float
    reliability_score: float
    satisfaction_score: float
    factors: Dict[str, float]


class JourneyDashboard:
    """用户旅程看板核心类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化旅程看板

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 配置参数
        self.screenshot_dir = config.get('screenshot_dir', 'screenshots')
        self.artifact_dir = config.get('artifact_dir', 'artifacts')
        self.output_dir = config.get('output_dir', 'reports/dashboard')

        # 旅程数据
        self.journey_id: str = ""
        self.test_name: str = ""
        self.start_time: float = 0
        self.end_time: Optional[float] = None
        self.steps: List[JourneyStep] = []
        self.experience_score: Optional[ExperienceScore] = None

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.artifact_dir, exist_ok=True)

    def start_journey(self, test_name: str) -> str:
        """
        开始新的测试旅程

        Args:
            test_name: 测试名称

        Returns:
            str: 旅程ID
        """
        self.journey_id = f"journey_{int(datetime.now().timestamp() * 1000)}"
        self.test_name = test_name
        self.start_time = datetime.now().timestamp()
        self.steps = []
        self.experience_score = None

        self.logger.info(f"🚀 开始测试旅程: {test_name} (ID: {self.journey_id})")
        return self.journey_id

    def add_step(self, step_name: str, description: str = "",
                 screenshots: List[str] = None,
                 artifacts: List[Dict[str, str]] = None,
                 metrics: Dict[str, Any] = None) -> str:
        """
        添加测试步骤

        Args:
            step_name: 步骤名称
            description: 步骤描述
            screenshots: 截图路径列表
            artifacts: 产物信息列表
            metrics: 性能指标

        Returns:
            str: 步骤ID
        """
        step_id = f"step_{len(self.steps) + 1}"

        step = JourneyStep(
            id=step_id,
            name=step_name,
            status=StepStatus.RUNNING,
            start_time=datetime.now().timestamp(),
            description=description,
            screenshots=screenshots or [],
            artifacts=artifacts or [],
            metrics=metrics or {}
        )

        self.steps.append(step)
        self.logger.info(f"📍 添加步骤: {step_name} (ID: {step_id})")
        return step_id

    def complete_step(self, step_id: str, success: bool = True,
                      error_message: str = "",
                      issues: List[Dict[str, Any]] = None) -> bool:
        """
        完成测试步骤

        Args:
            step_id: 步骤ID
            success: 是否成功
            error_message: 错误信息
            issues: 问题列表

        Returns:
            bool: 是否成功完成
        """
        step = self._find_step(step_id)
        if not step:
            self.logger.error(f"❌ 未找到步骤: {step_id}")
            return False

        step.end_time = datetime.now().timestamp()
        step.duration = step.end_time - step.start_time

        if success:
            step.status = StepStatus.SUCCESS
        else:
            # 根据错误类型确定状态
            if "blocked" in error_message.lower() or "阻止" in error_message:
                step.status = StepStatus.BLOCKED
            elif "timeout" in error_message.lower() or "超时" in error_message:
                step.status = StepStatus.FAILED
            else:
                step.status = StepStatus.WARNING

            # 添加错误信息
            if error_message:
                step.issues.append({
                    "type": "error",
                    "message": error_message,
                    "severity": self._determine_issue_severity(error_message),
                    "timestamp": datetime.now().isoformat()
                })

        # 添加额外的问题
        if issues:
            step.issues.extend(issues)

        self.logger.info(f"✅ 完成步骤: {step.name} (状态: {step.status.value})")
        return True

    def calculate_experience_score(self) -> ExperienceScore:
        """
        计算用户体验评分

        Returns:
            ExperienceScore: 体验评分对象
        """
        if not self.steps:
            return ExperienceScore(0, 0, 0, 0, 0, {})

        # 1. 可用性评分（基于失败步骤和问题）
        usability_score = self._calculate_usability_score()

        # 2. 性能评分（基于执行时间）
        performance_score = self._calculate_performance_score()

        # 3. 可靠性评分（基于错误和阻断）
        reliability_score = self._calculate_reliability_score()

        # 4. 满意度评分（综合评估）
        satisfaction_score = self._calculate_satisfaction_score()

        # 综合评分
        overall_score = (usability_score + performance_score +
                        reliability_score + satisfaction_score) / 4

        # 影响因素
        factors = {
            "可用性": usability_score,
            "性能": performance_score,
            "可靠性": reliability_score,
            "满意度": satisfaction_score
        }

        self.experience_score = ExperienceScore(
            overall_score=overall_score,
            usability_score=usability_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            satisfaction_score=satisfaction_score,
            factors=factors
        )

        return self.experience_score

    def end_journey(self) -> Dict[str, Any]:
        """
        结束测试旅程并生成看板数据

        Returns:
            Dict[str, Any]: 完整的看板数据
        """
        self.end_time = datetime.now().timestamp()
        total_duration = self.end_time - self.start_time

        # 计算体验评分
        self.calculate_experience_score()

        # 生成时间轴数据
        timeline_data = self._generate_timeline_data()

        # 统计信息
        stats = self._generate_statistics()

        # 问题汇总
        issues_summary = self._summarize_issues()

        dashboard_data = {
            "journey_info": {
                "id": self.journey_id,
                "test_name": self.test_name,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "total_duration": total_duration,
                "total_duration_formatted": self._format_duration(total_duration)
            },
            "timeline": timeline_data,
            "steps": [asdict(step) for step in self.steps],
            "experience_score": asdict(self.experience_score) if self.experience_score else None,
            "statistics": stats,
            "issues_summary": issues_summary,
            "screenshots": self._collect_all_screenshots(),
            "artifacts": self._collect_all_artifacts()
        }

        self.logger.info(f"📊 旅程看板生成完成: {self.journey_id}")
        return dashboard_data

    def _find_step(self, step_id: str) -> Optional[JourneyStep]:
        """查找指定步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def _determine_issue_severity(self, error_message: str) -> str:
        """确定问题严重程度"""
        error_lower = error_message.lower()

        if any(keyword in error_lower for keyword in ["critical", "致命", "崩溃", "中断"]):
            return IssueSeverity.CRITICAL.value
        elif any(keyword in error_lower for keyword in ["blocked", "阻止", "failed", "失败"]):
            return IssueSeverity.HIGH.value
        elif any(keyword in error_lower for keyword in ["warning", "警告", "timeout", "超时"]):
            return IssueSeverity.MEDIUM.value
        else:
            return IssueSeverity.LOW.value

    def _calculate_usability_score(self) -> float:
        """计算可用性评分"""
        if not self.steps:
            return 0

        total_steps = len(self.steps)
        successful_steps = sum(1 for step in self.steps if step.status == StepStatus.SUCCESS)

        # 基础分数
        base_score = (successful_steps / total_steps) * 100

        # 问题扣分
        total_issues = sum(len(step.issues) for step in self.steps)
        penalty = min(total_issues * 5, 50)  # 最多扣50分

        return max(0, base_score - penalty)

    def _calculate_performance_score(self) -> float:
        """计算性能评分"""
        if not self.steps:
            return 0

        # 定义预期时间阈值（秒）
        expected_durations = {
            "open_site": 10,
            "generate_image": 120,
            "generate_video": 300,
            "validate": 30
        }

        total_score = 0
        evaluated_steps = 0

        for step in self.steps:
            if step.duration:
                expected = expected_durations.get(step.name, 60)
                actual = step.duration

                if actual <= expected:
                    score = 100
                elif actual <= expected * 2:
                    score = 80 - ((actual - expected) / expected) * 20
                else:
                    score = max(0, 60 - ((actual - expected * 2) / (expected * 3)) * 60)

                total_score += score
                evaluated_steps += 1

        return total_score / evaluated_steps if evaluated_steps > 0 else 100

    def _calculate_reliability_score(self) -> float:
        """计算可靠性评分"""
        if not self.steps:
            return 0

        total_steps = len(self.steps)
        failed_steps = sum(1 for step in self.steps
                          if step.status in [StepStatus.FAILED, StepStatus.BLOCKED])

        # 基础可靠性分数
        reliability = ((total_steps - failed_steps) / total_steps) * 100

        # 严重问题扣分
        critical_issues = sum(
            1 for step in self.steps
            for issue in step.issues
            if issue.get("severity") == IssueSeverity.CRITICAL.value
        )

        penalty = min(critical_issues * 20, 80)
        return max(0, reliability - penalty)

    def _calculate_satisfaction_score(self) -> float:
        """计算满意度评分"""
        if not self.steps:
            return 0

        # 基于多个因素计算满意度
        usability = self._calculate_usability_score()
        performance = self._calculate_performance_score()
        reliability = self._calculate_reliability_score()

        # 满意度受其他因素影响，但有独立的计算逻辑
        base_satisfaction = (usability + performance + reliability) / 3

        # 如果有截图和产物，提升满意度
        has_screenshots = any(step.screenshots for step in self.steps)
        has_artifacts = any(step.artifacts for step in self.steps)

        bonus = 0
        if has_screenshots:
            bonus += 5
        if has_artifacts:
            bonus += 5

        # 如果所有步骤都成功，额外加分
        all_success = all(step.status == StepStatus.SUCCESS for step in self.steps)
        if all_success:
            bonus += 10

        return min(100, base_satisfaction + bonus)

    def _generate_timeline_data(self) -> List[Dict[str, Any]]:
        """生成时间轴数据"""
        timeline = []
        current_time = self.start_time

        for i, step in enumerate(self.steps):
            step_start = current_time
            step_end = step.end_time or step_start
            step_duration = step_end - step_start
            current_time = step_end

            timeline.append({
                "step_id": step.id,
                "step_name": step.name,
                "start_time": datetime.fromtimestamp(step_start).isoformat(),
                "end_time": datetime.fromtimestamp(step_end).isoformat(),
                "duration": step_duration,
                "duration_formatted": self._format_duration(step_duration),
                "status": step.status.value,
                "description": step.description,
                "has_screenshots": len(step.screenshots) > 0,
                "has_artifacts": len(step.artifacts) > 0,
                "issues_count": len(step.issues),
                "position": i + 1
            })

        return timeline

    def _generate_statistics(self) -> Dict[str, Any]:
        """生成统计信息"""
        if not self.steps:
            return {}

        total_steps = len(self.steps)
        successful_steps = sum(1 for step in self.steps if step.status == StepStatus.SUCCESS)
        failed_steps = sum(1 for step in self.steps
                          if step.status in [StepStatus.FAILED, StepStatus.BLOCKED])
        warning_steps = sum(1 for step in self.steps if step.status == StepStatus.WARNING)

        total_issues = sum(len(step.issues) for step in self.steps)
        total_screenshots = sum(len(step.screenshots) for step in self.steps)
        total_artifacts = sum(len(step.artifacts) for step in self.steps)

        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "warning_steps": warning_steps,
            "success_rate": (successful_steps / total_steps) * 100 if total_steps > 0 else 0,
            "total_issues": total_issues,
            "total_screenshots": total_screenshots,
            "total_artifacts": total_artifacts,
            "average_step_duration": sum(s.duration or 0 for s in self.steps) / total_steps,
            "fastest_step": min(self.steps, key=lambda s: s.duration or float('inf')).name if self.steps else None,
            "slowest_step": max(self.steps, key=lambda s: s.duration or 0).name if self.steps else None
        }

    def _summarize_issues(self) -> Dict[str, Any]:
        """汇总问题信息"""
        all_issues = []
        for step in self.steps:
            for issue in step.issues:
                issue["step_name"] = step.name
                issue["step_id"] = step.id
                all_issues.append(issue)

        # 按严重程度分组
        severity_counts = {}
        severity_types = [sev.value for sev in IssueSeverity]
        for sev in severity_types:
            severity_counts[sev] = sum(1 for issue in all_issues if issue.get("severity") == sev)

        # 获取关键问题
        critical_issues = [issue for issue in all_issues
                          if issue.get("severity") in [IssueSeverity.CRITICAL.value, IssueSeverity.HIGH.value]]

        return {
            "total_issues": len(all_issues),
            "severity_breakdown": severity_counts,
            "critical_issues": critical_issues[:5],  # 只显示前5个关键问题
            "issues_by_step": self._group_issues_by_step(all_issues)
        }

    def _group_issues_by_step(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按步骤分组问题"""
        step_issues = {}
        for issue in issues:
            step_name = issue.get("step_name", "Unknown")
            if step_name not in step_issues:
                step_issues[step_name] = []
            step_issues[step_name].append(issue)

        return [
            {
                "step_name": step_name,
                "issues_count": len(step_issues[step_name]),
                "issues": step_issues[step_name]
            }
            for step_name in step_issues
        ]

    def _collect_all_screenshots(self) -> List[Dict[str, Any]]:
        """收集所有截图信息"""
        screenshots = []
        for step in self.steps:
            for i, screenshot_path in enumerate(step.screenshots):
                screenshots.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "path": screenshot_path,
                    "filename": os.path.basename(screenshot_path),
                    "thumbnail": self._generate_thumbnail_path(screenshot_path),
                    "index": i
                })
        return screenshots

    def _collect_all_artifacts(self) -> List[Dict[str, Any]]:
        """收集所有产物信息"""
        artifacts = []
        for step in self.steps:
            for i, artifact in enumerate(step.artifacts):
                artifact_info = {
                    "step_id": step.id,
                    "step_name": step.name,
                    "index": i,
                    **artifact
                }
                artifacts.append(artifact_info)
        return artifacts

    def _generate_thumbnail_path(self, image_path: str) -> str:
        """生成缩略图路径"""
        if not image_path:
            return ""

        # 简单的缩略图路径生成逻辑
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        return f"thumbnails/{name}_thumb{ext}"

    def _format_duration(self, duration_seconds: float) -> str:
        """格式化时间显示"""
        if duration_seconds < 60:
            return f"{duration_seconds:.1f}秒"
        elif duration_seconds < 3600:
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            return f"{minutes}分{seconds}秒"
        else:
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            return f"{hours}小时{minutes}分钟"

    def save_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, str]:
        """
        保存看板数据

        Args:
            dashboard_data: 看板数据

        Returns:
            Dict[str, str]: 保存的文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = os.path.join(self.output_dir, f"{self.journey_id}_{timestamp}.json")

        # 保存JSON数据
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"📄 看板数据已保存: {json_filename}")

        return {"json": json_filename}