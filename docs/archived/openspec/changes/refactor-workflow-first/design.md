## Context
基于系统宪章和ADR决策，系统需要从当前的通用测试架构重构为Workflow-First架构。当前系统混合了业务逻辑和执行逻辑，需要明确分离关注点。

## Goals / Non-Goals
- Goals:
  - Workflow作为最高抽象层级
  - Phase表示用户心智阶段
  - Action仅做最小交互（open_page, click, input, wait_for）
  - Context作为状态载体
  - MCP严格作为观察者
- Non-Goals:
  - 通用工作流编排
  - UI自愈
  - 内容质量评估
  - API单测

## Decisions
- Decision: 采用Workflow DSL v1作为配置格式，约束线性执行、无分支并行
- Decision: 重构main.py为WorkflowExecutor，专注工作流编排
- Decision: 将steps目录重构为actions，实现原子交互
- Decision: Context模型必须包含workflow_name, current_phase, current_step, current_url, last_error字段
- Decision: MCP模块仅负责证据采集，不参与流程控制

## Risks / Trade-offs
- Risk: 配置格式变更可能导致用户迁移困难
  Mitigation: 提供配置迁移工具
- Risk: 重构范围较大，可能引入新bug
  Mitigation: 分阶段实施，保持向后兼容
- Trade-off: 简化性vs功能完整性，优先简化性

## Migration Plan
1. 实现新的Workflow解析器
2. 创建Action基类和具体实现
3. 重构Context模型
4. 更新配置文件格式
5. 修改main执行引擎
6. 保持MCP观察者模式
7. 更新报告格式适配新架构

## Open Questions
- 是否需要保持当前配置格式的向后兼容？
- 如何处理工作流执行中的异常恢复？