# 测试流程、映射与 Bug 管理指南

本指南整合了测试执行、Spec 规范与测试用例的映射关系，以及 Bug 报告与修复的标准流程。

## 📚 1. 测试执行指南

详细的端到端（E2E）测试执行指南请参考：[E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)

### 核心测试类型
- **冒烟测试 (Smoke)**: 快速验证核心功能（如 `NH-SMOKE-001`）。
- **端到端测试 (E2E)**: 覆盖完整用户旅程（如 `NH-E2E-001`）。
- **功能组件测试 (FC)**: 针对具体功能模块的细粒度测试（如 `NH-CREATE-001`）。

### 执行命令示例
```bash
# 执行冒烟测试
python src/main_workflow.py --workflow workflows/at/naohai_05_create_story_to_video_e2e.yaml

# 执行特定功能测试 (如剧本创建)
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_012_rf.yaml
```

---

## 🗺️ 2. Spec 流程与测试用例映射

下表列出了 Spec 文档与实际 Workflow 测试用例文件的对应关系。

> **注意**: 带有 `_rf.yaml` 后缀的文件是集成了 Robot Framework 语义的新架构测试用例。

| Spec ID | 功能领域 | 核心 Workflow (示例) | 备注 |
| :--- | :--- | :--- | :--- |
| **NH-SMOKE-001** | 冒烟测试 | `workflows/at/naohai_05_create_story_to_video_e2e.yaml` | 覆盖核心链路 |
| **NH-CREATE-001** | 剧本创建 | `workflows/fc/naohai_FC_NH_012_rf.yaml` (完整创建)<br>`workflows/fc/naohai_FC_NH_002_rf.yaml` (列表展示) | 包含 FC-002 至 FC-025, FC-051 至 FC-060 |
| **NH-SCRIPT-001** | 分镜编辑 | `workflows/fc/naohai_FC_NH_034_rf.yaml` (分析产出)<br>`workflows/fc/naohai_FC_NH_026_rf.yaml` (新增分镜) | 包含 FC-026 至 FC-039 |
| **NH-IMAGE-001** | 融图生成 | `workflows/fc/naohai_FC_NH_040_rf.yaml` (融合生图) | 包含 FC-040 至 FC-041 |
| **NH-VIDEO-001** | 视频制作 | `workflows/fc/naohai_FC_NH_042_rf.yaml` (视频创作) | 包含 FC-042 至 FC-049 |
| **NH-EXPORT-001** | 导出二创 | `workflows/fc/naohai_FC_NH_050_rf.yaml` (导出资源) | 包含 FC-050 |
| **NH-E2E-001** | 端到端全流程 | `workflows/e2e/naohai_E2E_GoldenPath.yaml` | 覆盖 Golden Path |

*完整的映射关系请查看各个 Spec 文件中的 `Mapping` 章节。*

---

## 🐞 3. Bug 提交与修复方案

当测试执行失败时，请遵循以下流程进行报告和修复。

### 3.1 Bug 提交规范

本项目使用 GitHub Issues 进行 Bug 追踪。请使用标准模板 `.github/ISSUE_TEMPLATE/bug.yaml`。

**必填字段说明**:
- **Title**: `[Bug] <简短描述>` (例如: `[Bug] NH-SMOKE-001 Execution Failed: Token Expired`)
- **Symptom (现象)**: 详细描述发生了什么，包含错误消息的关键部分。
- **Repro Command (复现命令)**: 能够 100% 复现该问题的具体命令。
- **Expected vs Actual**: 预期结果与实际结果的对比。
- **Logs / Evidence**: 粘贴相关的堆栈跟踪、日志片段或截图链接。

**标签 (Labels)**:
- `bug` (自动添加)
- `status:needs-triage` (自动添加)

### 3.2 常见 Bug 类型与修复方案

| Bug 类型 | 典型症状 | 修复方案 |
| :--- | :--- | :--- |
| **Auth Token 过期** | Log 中出现 `code: 50008` 或 `请求令牌已过期` | 运行 `python scripts/auth/save_real_auth_state.py --config config/config.yaml` 手动刷新登录态。 |
| **选择器失效** | Log 中出现 `Timeout ... exceeded` 或 `Element not found` | 1. 检查页面 DOM 结构是否变更。<br>2. 在 Workflow YAML 中更新 `selector`。<br>3. 尝试使用更稳健的选择器 (如 `has-text`, `xpath`)。 |
| **页面遮罩拦截** | Log 中出现 `intercepts pointer events` | 1. 增加 `wait_for` 步骤等待遮罩消失。<br>2. 在 `click` 动作中尝试 `force: true` (如果支持)。<br>3. 检查是否有弹窗未关闭。 |
| **YAML 语法错误** | Log 中出现 `parsing a block collection` 等解析错误 | 检查 `config.yaml` 或 Workflow 文件的缩进和格式，确保列表和字典结构正确。 |
| **服务不可用** | Log 中出现 `Connection refused` 或 `502 Bad Gateway` | 检查测试环境服务状态，确认 URL 配置是否正确。 |

### 3.3 修复流程

1.  **复现**: 使用 Issue 中的 Repro Command 在本地复现问题。
2.  **定位**: 分析日志，确定是环境问题、代码问题还是配置问题。
3.  **修复**:
    *   **环境问题**: 按照上述方案修复（如刷新 Token）。
    *   **代码/配置问题**: 创建修复分支，修改代码或 YAML。
4.  **验证**: 再次运行 Repro Command 确认修复。
5.  **关闭**: 在 Issue 中评论修复详情并关闭 Issue。
