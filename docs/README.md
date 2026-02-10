# 闹海自动化测试平台文档

## 📚 文档导航

### 🏗️ 架构设计
- **[Architecture Overview](architecture-design/01-architecture-overview.md)** - 系统整体架构概览
- **[Three-Tier Architecture](architecture-design/02-three-tier-architecture.md)** - 三层架构设计
- **[AIGC Enhanced Solution](architecture-design/03-aigc-enhanced-solution.md)** - AIGC场景增强方案
- **[Implementation Details](architecture-design/04-implementation-details.md)** - 实现细节
- **[Migration Plan](architecture-design/05-migration-plan.md)** - 迁移计划

### 📋 当前文档
- **[Documentation Guide](current/DOCUMENTATION_GUIDE.md)** - 文档编写指南
- **[E2E Golden Path](current/E2E_GOLDEN_PATH_IMPLEMENTATION_GUIDE.md)** - 端到端黄金路径实现
- **[Workflow Guide](current/WORKFLOW_GUIDE.md)** - 工作流使用指南
- **[Testing & Bug Guide](current/TESTING_AND_BUG_GUIDE.md)** - 测试和缺陷处理指南
- **[Troubleshooting Guide](current/TROUBLESHOOTING_GUIDE.md)** - 问题排查指南
- **[Structure Summary](current/STRUCTURE_SUMMARY.md)** - 项目结构总结

### 🔧 高级功能
- **[Advanced Features Guide](advanced_features_guide.md)** - 高级功能使用指南
- **[Boundary Condition Guide](boundary_condition_guide.md)** - 边界条件测试指南
- **[Complex Scenario Guide](complex_scenario_guide.md)** - 复杂场景测试指南
- **[Chrome DevTools MCP Guide](chrome-devtools-mcp-guide.md)** - Chrome DevTools集成指南
- **[Test Data Management](test_data_management_best_practices.md)** - 测试数据管理最佳实践
- **[Optimization TODO](optimization_todo.md)** - 优化待办事项

### 📖 业务文档
- **[闹海关键流程](闹海关键流程.md)** - 闹海核心业务流程
- **[闹海工作流清单](NAOHAI_WORKFLOW_MANIFEST.md)** - 工作流清单说明
- **[README Workflows](README_WORKFLOWS.md)** - 工作流使用说明

### 🏛️ 架构决策
- **[ADR-001: System Mission and Scope](adr/ADR-001-system-mission-and-scope.md)** - 系统使命和范围
- **[ADR-002: Workflow-First Architecture](adr/ADR-002-workflow-first-architecture.md)** - 工作流优先架构

### 📜 历史文档
- **[Legacy Documents](legacy/)** - 历史归档文档

---

## 🚀 快速开始

1. **新手入门**: 阅读 [Architecture Overview](architecture-design/01-architecture-overview.md) 了解系统架构
2. **测试执行**: 参考 [E2E Golden Path](current/E2E_GOLDEN_PATH_IMPLEMENTATION_GUIDE.md) 执行端到端测试
3. **问题排查**: 使用 [Troubleshooting Guide](current/TROUBLESHOOTING_GUIDE.md) 解决常见问题
4. **高级用法**: 查看 [Advanced Features Guide](advanced_features_guide.md) 掌握高级功能

---

## 📊 文档维护状态

| 文档类型 | 维护状态 | 更新频率 |
|---------|---------|---------|
| 架构设计 | ✅ 活跃维护 | 按需更新 |
| 当前文档 | ✅ 活跃维护 | 定期更新 |
| 高级功能 | ✅ 活跃维护 | 功能迭代时更新 |
| 业务文档 | ✅ 活跃维护 | 业务变更时更新 |
| 架构决策 | 📝 历史记录 | 不变 |

---

## 📝 贡献指南

- 新增文档请参考 [Documentation Guide](current/DOCUMENTATION_GUIDE.md)
- 架构变更需要先创建 ADR
- 文档命名遵循约定：kebab-case.md
- 重要变更需要更新本导航页面