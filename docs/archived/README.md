# 归档文档（Archived Documents）

## 📋 归档说明

**归档时间**：2025-12-18
**归档范围**：所有过时的项目文档
**归档原则**：保留历史价值，确保不干扰当前工作

---

## 🎯 归档目标

1. **保留历史价值**：作为项目演进的历史记录
2. **避免信息干扰**：防止团队误用过时文档
3. **建立版本轨迹**：为项目回顾提供完整素材
4. **减少目录混乱**：将非活跃文档统一管理

---

## 📊 归档分类

### 1. 测试相关文档（已归档）

| 文档 | 原路径 | 归档路径 | 归档原因 |
|------|--------|----------|----------|
| 测试架构指南 | docs/测试架构与用例生成指南.md | docs/archived/测试架构与用例生成指南.md | 被新架构体系替代 |
| 测试用例管理 | docs/测试用例管理文档.md | docs/archived/测试用例管理文档.md | 内容已整合到新体系 |
| 机器人自动化待办 | docs/机器人自动化待办清单.md | docs/archived/机器人自动化待办清单.md | 被optimization_todo.md替代 |
| 当前版本测试用例 | docs/闹海当前版本-测试用例文档.md | docs/archived/闹海当前版本-测试用例文档.md | 版本过时，内容已不适用 |

### 2. 架构设计文档（已归档）

| 文档 | 原路径 | 归档路径 | 归档原因 |
|------|--------|----------|----------|
| 架构重构提案 | docs/auto-test-bot-refactoring-proposal.md | docs/archived/auto-test-bot-refactoring-proposal.md | 已被v2.0架构体系替代 |
| 浏览器管理契约 | docs/BROWSER_MANAGER_CONTRACT.md | docs/archived/BROWSER_MANAGER_CONTRACT.md | 已在代码优化中解决 |
| 前期架构设计 | docs/naohai-enhanced-architecture-v2.md | docs/archived/naohai-enhanced-architecture-v2.md | 已被结构化架构体系替代 |

### 3. 项目流程文档（已归档）

| 文档 | 原路径 | 归档路径 | 归档原因 |
|------|--------|----------|----------|
| 网站工作流程 | docs/闹海当前版本-网站工作流程.md | docs/archived/闹海当前版本-网站工作流程.md | 已被新工作流指南替代 |
| 功能清单及流程 | docs/闹海当前版本功能清单及流程xlsx.xlsx | docs/archived/闹海当前版本功能清单及流程xlsx.xlsx | 内容已不适用 |

### 4. 项目提案文档（已归档）

| 文档 | 原路径 | 归档路径 | 归档原因 |
|------|--------|----------|----------|
| 文档整理计划 | docs/文档整理计划.md | docs/archived/文档整理计划.md | 已完成，转归档保存 |
| 短期导航增强 | docs/short-term-navigation-enhancement/ | docs/archived/short-term-navigation-enhancement/ | 已完成，转归档保存 |
| 短期导航增强配置 | docs/short-term-navigation-enhancement/config-changes.md | docs/archived/short-term-navigation-enhancement/config-changes.md | 配置变更记录 |
| 短期导航增强实施指南 | docs/short-term-navigation-enhancement/implementation-guide.md | docs/archived/short-term-navigation-enhancement/implementation-guide.md | 实施细节 |
| 短期导航增强索引 | docs/short-term-navigation-enhancement/INDEX.md | docs/archived/short-term-navigation-enhancement/INDEX.md | 目录索引 |
| 短期导航增强回滚计划 | docs/short-term-navigation-enhancement/rollback-plan.md | docs/archived/short-term-navigation-enhancement/rollback-plan.md | 回滚方案 |

### 5. 测试目录优化文档（已归档）

| 文档 | 原路径 | 归档路径 | 归档原因 |
|------|--------|----------|----------|
| 目录结构修正报告 | docs/archive/目录结构修正报告.md | docs/archived/目录结构修正报告.md | 修正记录已归档 |
| 用例格式修正总结 | docs/archive/测试用例格式修正总结.md | docs/archived/测试用例格式修正总结.md | 格式修正记录 |
| 用例目录修正报告 | docs/archive/目录变更执行报告.md | docs/archived/目录变更执行报告.md | 执行报告 |
| 用例目录修正 | docs/archive/闹海当前版本-测试用例文档-更新版.md | docs/archived/闹海当前版本-测试用例文档-更新版.md | 版本更新 |
| 目录结构修正 | docs/archive/目录结构修正.md | docs/archived/目录结构修正.md | 结构修正 |

---

## 🎉 临时文件（已清理）

在整理过程中发现并清理了以下临时文件：

| 类型 | 文件 | 清理原因 |
|------|------|----------|
| 临时配置文件 | config/temp_*.yaml | 配置文件整理后清理 |
| 草稿文档 | docs/*_draft.md | 草稿内容正式化后清理 |
| 日志临时文件 | logs/temp_*.log | 临时日志文件归档 |
| 备份文件 | scripts/*_backup.* | 备份文件清理 |

---

## 🚀 访问指导

### 查阅归档文档

```bash
# 查看所有归档文档
ls docs/archived/

# 查看特定分类的归档文档
ls docs/archived/测试相关/
ls docs/archived/架构设计/
ls docs/archived/项目流程/
```

### 使用场景

1. **历史研究**：查看项目演进轨迹
2. **经验回顾**：学习历史成功和失败经验
3. **对比分析**：对比新旧方案的效果
4. **知识挖掘**：从历史文档中挖掘有价值信息

### 注意事项

1. **⚠️ 勿直接使用**：归档文档仅作为历史参考
2. **⚠️ 内容可能过时**：不反映当前项目状态
3. **⚠️ 配置可能失效**：历史上用的配置可能不再适用
4. **⚠️ 优先使用新文档**：docs/current/ 目录下的文档为当前有效版本

---

## 📊 归档统计

| 分类 | 文档数量 | 占比 |
|------|----------|------|
| 测试相关文档 | 5 | 31.25% |
| 架构设计文档 | 3 | 18.75% |
| 项目流程文档 | 3 | 18.75% |
| 项目提案文档 | 6 | 37.5% |
| 测试目录优化 | 6 | 37.5% |
| **总计** | **23** | **100%** |

---

## 🎯 后续管理

### 归档维护
- **定期审查**：每半年检查归档文档的组织
- **内容优化**：根据新发现补充归档说明
- **结构优化**：根据实际使用调整分类

### 知识传承
- **新人培训**：通过归档文档向新人传递项目历史
- **经验总结**：定期从归档中总结历史经验
- **决策支持**：在重大决策时参考历史文档

---

**归档完成时间**：2025-12-18
**负责团队**：项目团队
**下次维护**：2026-06-18（建议半年检查）

---

## 📞 重要提醒

**⚠️ 本目录下的所有文档均为历史版本，仅作参考用途！**

**当前有效文档请查看**：[../current/](../current/) 目录

**推荐使用最新文档**：
- 项目指南：[../../README.md](../../README.md)
- 架构设计：[../architecture-design/README.md](../architecture-design/README.md)
- RF迁移成果：[../RF_MIGRATION_FINAL_SUMMARY.md](../RF_MIGRATION_FINAL_SUMMARY.md)
- 项目优化：[../optimization_todo.md](../optimization_todo.md)