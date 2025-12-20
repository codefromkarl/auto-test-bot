# Change: Refactor to Workflow-First Architecture

## Why
当前系统采用通用测试步骤架构，不符合系统宪章定义的Workflow-First原则。需要重构为以Workflow为最高抽象层级，Phase表示心智阶段，Action为最小交互单元的架构，明确系统边界和职责分工。

## What Changes
- **BREAKING**: 重构核心执行引擎从步骤驱动到工作流驱动
- 重构配置系统，支持Workflow DSL v1格式
- 明确Action边界，仅包含最小交互单元
- 重构Context模型，作为状态载体而非日志
- MCP严格作为观察者和证据采集器

## Impact
- Affected specs: workflow, execution, context, reporting
- Affected code: src/main.py, src/steps/, src/utils/, src/reporter/
- 需要重新设计配置文件格式
- 需要实现Workflow解析器