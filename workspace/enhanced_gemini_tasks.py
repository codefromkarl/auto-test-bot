#!/usr/bin/env python3
"""
Enhanced Gemini UI Analysis Tasks for Naohai Testing
基于新架构重构的UI分析任务处理器
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import re
import time

from base_task_processor import BaseTaskProcessor, MCPIntegrationMixin, TaskResult
from config_manager import EnhancedConfigManager

class EnhancedGeminiUITasks(BaseTaskProcessor, MCPIntegrationMixin):
    """增强版Gemini UI分析任务处理器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "gemini")
        self.config_manager = EnhancedConfigManager("workspace/parallel_executor_config.yaml")

    async def execute_task(self, task_config: Dict[str, Any]) -> TaskResult:
        """执行任务的主要入口点"""
        task_type = task_config.get("task_type")
        task_result = self.create_task_result(task_type, task_config)

        self.log_task_start(task_result)
        start_time = time.time()

        try:
            if task_type == "ui_analysis":
                result = await self.analyze_page_layout(
                    task_config.get("url"),
                    task_config.get("screenshot_path")
                )
            elif task_type == "element_visibility_check":
                result = await self.validate_element_visibility(
                    task_config.get("selectors", {})
                )
            elif task_type == "screenshot_analysis":
                result = await self.analyze_screenshot_quality(
                    task_config.get("screenshot_path"),
                    task_config.get("expected_content")
                )
            elif task_type == "responsiveness_test":
                result = await self.check_responsiveness(
                    task_config.get("viewports", [])
                )
            elif task_type == "accessibility_check":
                result = await self.check_accessibility()
            elif task_type == "dom_structure_validation":
                result = await self.validate_dom_structure()
            else:
                raise ValueError(f"Unsupported task type: {task_type}")

            task_result.result = result
            task_result.status = "completed"

        except Exception as e:
            task_result.status = "failed"
            task_result.error = str(e)
            print(f"❌ Task {task_result.task_id} failed: {e}")

        finally:
            task_result.execution_time = time.time() - start_time
            self.log_task_complete(task_result)
            self.save_task_result(task_result)

        return task_result

    async def analyze_page_layout(self, url: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """分析页面布局 - 完整实现"""
        analysis_prompt = self._build_ui_analysis_prompt(url, screenshot_path)

        # 使用MCP工具调用
        mcp_result = await self.call_mcp_tool("gemini", {"prompt": analysis_prompt})

        if not mcp_result.get("success", False):
            raise RuntimeError(f"Gemini analysis failed: {mcp_result.get('error', 'Unknown error')}")

        # 处理分析结果
        analysis_output = mcp_result.get("output", "")
        return {
            "url": url,
            "screenshot_path": screenshot_path,
            "analysis": analysis_output,
            "components_found": self._extract_ui_components(analysis_output),
            "layout_score": self._calculate_layout_score(analysis_output),
            "issues_identified": self._identify_ui_issues(analysis_output)
        }

    async def validate_element_visibility(self, selectors: Dict[str, List[str]]) -> Dict[str, Any]:
        """验证元素可见性 - 完整实现"""
        validation_prompt = self._build_visibility_validation_prompt(selectors)

        mcp_result = await self.call_mcp_tool("gemini", {"prompt": validation_prompt})

        if not mcp_result.get("success", False):
            raise RuntimeError(f"Visibility validation failed: {mcp_result.get('error', 'Unknown error')}")

        validation_output = mcp_result.get("output", "")
        return {
            "selectors": selectors,
            "visibility_report": validation_output,
            "accessible_elements": self._count_accessible_elements(validation_output),
            "blocked_elements": self._identify_blocked_elements(validation_output)
        }

    async def analyze_screenshot_quality(self, screenshot_path: str, expected_content: str) -> Dict[str, Any]:
        """分析截图质量 - 完整实现"""
        analysis_prompt = self._build_screenshot_analysis_prompt(screenshot_path, expected_content)

        mcp_result = await self.call_mcp_tool("gemini", {"prompt": analysis_prompt})

        if not mcp_result.get("success", False):
            raise RuntimeError(f"Screenshot analysis failed: {mcp_result.get('error', 'Unknown error')}")

        analysis_output = mcp_result.get("output", "")
        return {
            "screenshot_path": screenshot_path,
            "expected_content": expected_content,
            "quality_analysis": analysis_output,
            "quality_score": self._calculate_quality_score(analysis_output),
            "content_match": self._validate_content_match(analysis_output, expected_content),
            "visual_issues": self._identify_visual_issues(analysis_output)
        }

    async def check_responsiveness(self, viewports: List[Dict[str, int]]) -> Dict[str, Any]:
        """检查响应式设计 - 完整实现"""
        responsiveness_prompt = self._build_responsiveness_check_prompt(viewports)

        mcp_result = await self.call_mcp_tool("gemini", {"prompt": responsiveness_prompt})

        if not mcp_result.get("success", False):
            raise RuntimeError(f"Responsiveness check failed: {mcp_result.get('error', 'Unknown error')}")

        analysis_output = mcp_result.get("output", "")
        return {
            "viewports": viewports,
            "responsiveness_report": analysis_output,
            "mobile_friendly": self._check_mobile_friendly(analysis_output),
            "layout_breakpoints": self._identify_layout_breakpoints(analysis_output)
        }

    async def check_accessibility(self) -> Dict[str, Any]:
        """检查无障碍性 - 完整实现"""
        accessibility_prompt = self._build_accessibility_check_prompt()

        mcp_result = await self.call_mcp_tool("gemini", {"prompt": accessibility_prompt})

        if not mcp_result.get("success", False):
            raise RuntimeError(f"Accessibility check failed: {mcp_result.get('error', 'Unknown error')}")

        analysis_output = mcp_result.get("output", "")
        return {
            "accessibility_report": analysis_output,
            "wcag_compliance": self._calculate_wcag_compliance(analysis_output),
            "accessibility_score": self._calculate_accessibility_score(analysis_output),
            "critical_issues": self._identify_critical_accessibility_issues(analysis_output)
        }

    async def validate_dom_structure(self) -> Dict[str, Any]:
        """验证DOM结构 - 完整实现"""
        dom_prompt = self._build_dom_validation_prompt()

        mcp_result = await self.call_mcp_tool("gemini", {"prompt": dom_prompt})

        if not mcp_result.get("success", False):
            raise RuntimeError(f"DOM validation failed: {mcp_result.get('error', 'Unknown error')}")

        analysis_output = mcp_result.get("output", "")
        return {
            "dom_analysis": analysis_output,
            "structure_valid": self._validate_structure(analysis_output),
            "semantic_score": self._calculate_semantic_score(analysis_output),
            "seo_friendly": self._check_seo_friendliness(analysis_output)
        }

    # Prompt构建方法
    def _build_ui_analysis_prompt(self, url: str, screenshot_path: Optional[str]) -> str:
        """构建UI分析prompt"""
        context = f"页面URL: {url}"
        if screenshot_path:
            context += f", 截图路径: {screenshot_path}"

        return f"""
PURPOSE: 分析页面布局和UI组件
TASK:
• 检查页面整体布局是否合理
• 识别主要UI组件和交互元素
• 评估视觉层次和用户体验
• 检查响应式设计适配
• 识别潜在的UI问题

MODE: analysis
CONTEXT: {context}
EXPECTED: 详细的UI分析报告，包括布局评估、组件识别和改进建议
RULES: Focus on UI/UX best practices | analysis=READ-ONLY
"""

    def _build_visibility_validation_prompt(self, selectors: Dict[str, List[str]]) -> str:
        """构建可见性验证prompt"""
        return f"""
PURPOSE: 验证页面元素可见性和可访问性
TASK:
• 检查每个选择器对应的元素是否可见
• 验证元素的可访问性属性
• 评估元素的交互可行性
• 识别遮挡或重叠问题

MODE: analysis
CONTEXT: 需要验证的选择器: {json.dumps(selectors, ensure_ascii=False)}
EXPECTED: 元素可见性报告，包含每个元素的状态和问题
RULES: Focus on accessibility and visibility validation | analysis=READ-ONLY
"""

    def _build_screenshot_analysis_prompt(self, screenshot_path: str, expected_content: str) -> str:
        """构建截图分析prompt"""
        return f"""
PURPOSE: 分析生成内容的视觉质量
TASK:
• 评估图片/视频内容的视觉质量
• 验证内容是否符合预期描述
• 检查内容的完整性和准确性
• 识别视觉缺陷或异常

MODE: analysis
CONTEXT: 截图路径: {screenshot_path}, 预期内容: {expected_content}
EXPECTED: 视觉质量评估报告，包含质量分数和问题识别
RULES: Focus on visual quality assessment | analysis=READ-ONLY
"""

    def _build_responsiveness_check_prompt(self, viewports: List[Dict[str, int]]) -> str:
        """构建响应式检查prompt"""
        return f"""
PURPOSE: 验证响应式设计适配
TASK:
• 分析不同视口尺寸下的页面布局
• 检查元素是否正确适配
• 验证交互功能在移动端的可用性
• 识别响应式设计问题

MODE: analysis
CONTEXT: 测试视口: {json.dumps(viewports, ensure_ascii=False)}
EXPECTED: 响应式设计报告，包含各视口的适配状态
RULES: Focus on mobile-first responsive design validation | analysis=READ-ONLY
"""

    def _build_accessibility_check_prompt(self) -> str:
        """构建无障碍检查prompt"""
        return """
PURPOSE: 执行无障碍性检查
TASK:
• 检查页面的ARIA标签和语义化HTML
• 验证键盘导航可用性
• 检查颜色对比度和可读性
• 评估屏幕阅读器兼容性

MODE: analysis
CONTEXT: 执行WCAG 2.1 AA级别无障碍性检查
EXPECTED: 无障碍性评估报告，包含合规性分数和改进建议
RULES: Focus on WCAG compliance | analysis=READ-ONLY
"""

    def _build_dom_validation_prompt(self) -> str:
        """构建DOM验证prompt"""
        return """
PURPOSE: 验证DOM结构的完整性和语义
TASK:
• 检查HTML文档结构的正确性
• 验证语义化标签的使用
• 识别潜在的DOM结构问题
• 评估SEO友好的结构元素

MODE: analysis
CONTEXT: 验证页面DOM结构和语义化HTML
EXPECTED: DOM结构验证报告，包含结构评估和优化建议
RULES: Focus on HTML5 semantic structure | analysis=READ-ONLY
"""

    # 完整实现的辅助方法
    def _extract_ui_components(self, analysis: str) -> List[str]:
        """从分析结果中提取UI组件"""
        components = []

        # 使用正则表达式提取组件信息
        patterns = [
            r"组件[：:]?\s*([^\n,，。.]+)",
            r"element[：:]?\s*([^\n,，。.]+)",
            r"按钮[：:]?\s*([^\n,，。.]+)",
            r"导航[：:]?\s*([^\n,，。.]+)"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, analysis, re.IGNORECASE)
            components.extend([match.strip() for match in matches])

        return list(set(components))

    def _calculate_layout_score(self, analysis: str) -> float:
        """计算布局分数"""
        score = 70.0  # 基础分数

        # 正面关键词加分
        positive_keywords = ["良好", "合理", "清晰", "规范", "响应式", "用户友好", "层次分明"]
        for keyword in positive_keywords:
            if keyword in analysis:
                score += 3.0

        # 负面关键词减分
        negative_keywords = ["问题", "错误", "不合理", "缺失", "重叠", "遮挡", "混乱"]
        for keyword in negative_keywords:
            if keyword in analysis:
                score -= 5.0

        return max(0.0, min(100.0, score))

    def _identify_ui_issues(self, analysis: str) -> List[str]:
        """识别UI问题"""
        issues = []

        # 使用模式匹配识别问题
        issue_patterns = [
            r"问题[：:]?\s*([^\n,，。.]+)",
            r"错误[：:]?\s*([^\n,，。.]+)",
            r"建议[：:]?\s*[^\n,，。.]*?改善[^\n,，。.]*?([^\n,，。.]+)",
            r"需要[：:]?\s*([^\n,，。.]+)"
        ]

        for pattern in issue_patterns:
            matches = re.findall(pattern, analysis, re.IGNORECASE)
            issues.extend([match.strip() for match in matches])

        return list(set(issues))

    def _count_accessible_elements(self, result: str) -> int:
        """统计可访问元素数量"""
        accessible_indicators = ["可访问", "有标签", "有焦点", "键盘可操作", "aria-"]
        count = 0

        for indicator in accessible_indicators:
            count += len(re.findall(indicator, result, re.IGNORECASE))

        return count

    def _identify_blocked_elements(self, result: str) -> List[str]:
        """识别被遮挡元素"""
        blocked_patterns = [
            r"遮挡[：:]?\s*([^\n,，。.]+)",
            r"重叠[：:]?\s*([^\n,，。.]+)",
            r"不可见[：:]?\s*([^\n,，。.]+)",
            r"隐藏[：:]?\s*([^\n,，。.]+)"
        ]

        blocked = []
        for pattern in blocked_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            blocked.extend([match.strip() for match in matches])

        return list(set(blocked))

    def _calculate_quality_score(self, result: str) -> float:
        """计算质量分数"""
        score = 70.0

        positive_keywords = ["清晰", "完整", "准确", "高质量", "符合预期", "无缺陷"]
        for keyword in positive_keywords:
            if keyword in result:
                score += 4.0

        negative_keywords = ["模糊", "不完整", "错误", "缺陷", "问题", "偏差"]
        for keyword in negative_keywords:
            if keyword in result:
                score -= 6.0

        return max(0.0, min(100.0, score))

    def _validate_content_match(self, result: str, expected: str) -> bool:
        """验证内容匹配"""
        # 检查结果中是否包含预期内容的关键词
        expected_keywords = expected.split()[:5]  # 取前5个关键词
        match_count = sum(1 for keyword in expected_keywords if keyword in result)
        return match_count >= len(expected_keywords) * 0.6  # 60%匹配率

    def _identify_visual_issues(self, result: str) -> List[str]:
        """识别视觉问题"""
        issue_patterns = [
            r"(模糊|不清晰|失真|变形|错位|缺失|错误|缺陷)[：:]?\s*([^\n,，。.]+)",
            r"视觉问题[：:]?\s*([^\n,，。.]+)",
            r"建议[：:]?\s*[^\n,，。.]*?修复[^\n,，。.]*?([^\n,，。.]+)"
        ]

        issues = []
        for pattern in issue_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    issues.extend([match[0] + match[1] for match in matches])
                else:
                    issues.extend(matches)

        return list(set(issues))

    def _check_mobile_friendly(self, result: str) -> bool:
        """检查移动端友好性"""
        mobile_indicators = ["移动端", "响应式", "适配", "手机", "触屏"]
        return any(indicator in result for indicator in mobile_indicators)

    def _identify_layout_breakpoints(self, result: str) -> List[Dict[str, Any]]:
        """识别布局断点"""
        breakpoint_patterns = [
            r"([0-9]+)px",
            r"(手机|平板|桌面|移动|tablet|mobile|desktop)",
            r"(断点|breakpoint)[：:]?\s*([^\n,，。.]+)"
        ]

        breakpoints = []
        for pattern in breakpoint_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        breakpoints.append({"size": match[0], "type": match[1]})
                    else:
                        breakpoints.append({"size": match, "type": "unknown"})

        return breakpoints

    def _calculate_wcag_compliance(self, result: str) -> Dict[str, float]:
        """计算WCAG合规性"""
        levels = {
            "A": 0.0,
            "AA": 0.0,
            "AAA": 0.0
        }

        # 检查合规性关键词
        for level in levels:
            pattern = f"{level}级?合规"
            matches = re.findall(pattern, result, re.IGNORECASE)
            if matches:
                levels[level] = 100.0
            elif "基本合规" in result and level == "A":
                levels[level] = 80.0
            elif "部分合规" in result:
                levels[level] = 60.0

        return levels

    def _calculate_accessibility_score(self, result: str) -> float:
        """计算无障碍性分数"""
        score = 60.0

        positive_factors = [
            "可访问", "无障碍", "aria", "语义化", "键盘导航",
            "屏幕阅读器", "对比度", "标签", "焦点管理"
        ]

        for factor in positive_factors:
            if factor in result:
                score += 4.0

        negative_factors = [
            "不可访问", "障碍", "缺失", "错误", "问题", "违反"
        ]

        for factor in negative_factors:
            if factor in result:
                score -= 5.0

        return max(0.0, min(100.0, score))

    def _identify_critical_accessibility_issues(self, result: str) -> List[str]:
        """识别关键无障碍问题"""
        critical_patterns = [
            r"关键问题[：:]?\s*([^\n,，。.]+)",
            r"严重问题[：:]?\s*([^\n,，。.]+)",
            r"违反[：:]?\s*([^\n,，。.]+)",
            r"缺失[：:]?\s*([^\n,，。.]+)"
        ]

        issues = []
        for pattern in critical_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            issues.extend([match.strip() for match in matches])

        return list(set(issues))

    def _validate_structure(self, result: str) -> bool:
        """验证结构正确性"""
        positive_indicators = ["结构正确", "符合规范", "语义化", "有效"]
        negative_indicators = ["错误", "问题", "不符合", "缺失"]

        positive_score = sum(1 for indicator in positive_indicators if indicator in result)
        negative_score = sum(1 for indicator in negative_indicators if indicator in result)

        return positive_score >= negative_score

    def _calculate_semantic_score(self, result: str) -> float:
        """计算语义化分数"""
        score = 60.0

        semantic_elements = [
            "header", "nav", "main", "article", "section",
            "aside", "footer", "figure", "figcaption"
        ]

        for element in semantic_elements:
            if element in result:
                score += 2.5

        return max(0.0, min(100.0, score))

    def _check_seo_friendliness(self, result: str) -> bool:
        """检查SEO友好性"""
        seo_indicators = [
            "SEO友好", "搜索引擎", "标题", "元数据",
            "描述", "关键词", "结构化", "索引"
        ]

        return sum(1 for indicator in seo_indicators if indicator in result) >= 3