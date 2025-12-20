### 🎯 Goal
在 Bug Form 中新增可机器判断字段（component/ai_action），并新增 Issue 自动打标签的 GitHub Actions workflow，用于 agent/AI 路由。

### ✅ Scope
- 修改 `.github/ISSUE_TEMPLATE/bug.yaml`：新增 component/ai_action 两个 dropdown。
- 新增 `.github/workflows/issue-auto-label.yml`：issues opened/edited 触发，基于表单字段自动打标签。
- 仅加 label，不做 assignee。
- 组件标签按脚本规范生成（`component:*`），默认策略为动态短标签。

### 📥 Inputs
- Playbook: `AI_EXECUTION_PLAYBOOK.md`
- 参考：现有 Bug Form 与 workflows（如有）

### 📤 Outputs
- 更新后的 Bug Form
- 新的自动打标 workflow

### ✅ DoD
- [ ] Bug Form 增加 component / ai_action dropdown（必填）
- [ ] 自动打标 workflow 生效（addLabels, agent/ai/component 规则）
- [ ] 不自动 assignee
- [ ] 记录变更与测试结果
