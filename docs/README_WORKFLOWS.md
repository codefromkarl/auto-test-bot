# Workflow 使用指南

## 🎯 快速开始

### 执行工作流

```bash
# 基本用法
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_002_rf.yaml

# 指定配置文件
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_002_rf.yaml --config config/config.yaml

# 调试模式
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_002_rf.yaml --debug

# MCP 深度诊断模式
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_002_rf.yaml --mcp-diagnostic
```

---

## 📁 Workflow 目录结构

```
workflows/
├── at/                         # 冒烟用例（AT）
│   ├── naohai_01_story_list_smoke.yaml
│   ├── naohai_02_create_story_smoke.yaml
│   └── naohai_03_storyboard_smoke.yaml
├── fc/                         # 功能点覆盖用例（FC）
│   ├── naohai_FC_NH_002.yaml         # 原版
│   ├── naohai_FC_NH_002_rf.yaml       # RF语义化版本（推荐）
│   ├── FC_INDEX.md                   # FC 用例索引
│   └── ...（共59个FC用例）
├── resilience/                   # 容错和恢复测试
│   ├── naohai_complex_multi_project_management.yaml
│   ├── naohai_boundary_condition_stress_test.yaml
│   └── naohai_enhanced_error_handling_test.yaml
└── shared/                     # 共享工作流组件（预留）
```

---

## 🎬 冒烟用例

前置条件：需要有效的登录态文件（`auth_session.json` + `auth_state_real.json`）

### 1) 剧本列表冒烟
```bash
python src/main_workflow.py --workflow workflows/at/naohai_01_story_list_smoke.yaml
```

### 2) 新建剧本冒烟
```bash
python src/main_workflow.py --workflow workflows/at/naohai_02_create_story_smoke.yaml
```

### 3) 分镜管理冒烟
```bash
python src/main_workflow.py --workflow workflows/at/naohai_03_storyboard_smoke.yaml
```

---

## 🧾 FC 用例

### RF 语义化版本（推荐）

```bash
# 执行单个 RF 版本
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_012_rf.yaml

# 执行所有 FC 用例
for wf in workflows/fc/naohai_FC_NH_*_rf.yaml; do
  python src/main_workflow.py --workflow "$wf"
done
```

### FC 用例索引

参考 `workflows/fc/FC_INDEX.md` 获取完整的用例清单和说明。

---

## 🔧 配置说明

### 主配置文件

`config/config.yaml` 包含以下配置：

```yaml
test:
  url: "http://your-test-url.com"
  timeout:
    page_load: 30000
    element_load: 10000

browser:
  headless: false
  storage_state:
    session_state: "scripts/auth/auth_state_real.json"
```

---

## 📊 测试报告

执行完成后，报告保存在 `runs/` 目录：

| 报告类型 | 位置 |
|---------|------|
| 执行日志 | `runs/YYYY-MM-DD/run.md` |
| 截图 | `screenshots/` |
| 错误截图 | `screenshots/errors/` |

---

## 🚨 故障排除

### 常见问题

1. **元素找不到**
   - 检查页面是否完全加载
   - 使用 `--debug` 模式查看详细日志
   - 查看截图确认页面状态

2. **超时问题**
   - 调整 `config.yaml` 中的超时值
   - 检查网络连接

3. **登录态失效**
   - 确认 `auth_session.json` 和 `auth_state_real.json` 存在
   - 重新运行登录流程更新认证文件

---

## 📚 相关文档

- **[架构设计](architecture-design/README.md)** - 系统架构
- **[工作流开发指南](current/WORKFLOW_GUIDE.md)** - 工作流开发
- **[测试与缺陷指南](current/TESTING_AND_BUG_GUIDE.md)** - 测试执行
