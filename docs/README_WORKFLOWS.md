# NowHi网站测试工作流使用指南

## 🎯 测试目标

基于 http://<NOWHI_HOST>/nowhi/index.html 的完整功能测试，验证从文本输入到视频生成的用户流程。

---

## 📁 文件结构

```
auto-test-bot/
├── config/
│   ├── config.yaml              # 主配置文件
│   └── mcp_config.yaml         # MCP观测配置
├── workflows/
│   ├── at/                         # 冒烟用例（AT）
│   │   ├── naohai_01_story_list_smoke.yaml
│   │   ├── naohai_02_create_story_smoke.yaml
│   │   └── naohai_03_storyboard_smoke.yaml
│   ├── fc/                         # 功能点覆盖用例（FC）
│   │   ├── naohai_FC_NH_002.yaml
│   │   ├── ...
│   │   ├── naohai_FC_NH_060.yaml
│   │   └── FC_INDEX.md             # FC 用例索引
│   ├── rt/                         # 回归用例（RT，预留）
│   └── archive/                    # 归档（旧版/示例）
├── scripts/
│   ├── validate_environment.py   # 环境验证脚本
│   └── run_workflow_test.py     # 测试执行脚本
└── screenshots/                    # 测试截图保存目录
```

---

## 🚀 快速开始

### 1. 环境验证
```bash
# 检查测试环境是否就绪
python scripts/validate_environment.py
```

### 2. 基础导航测试
```bash
# 测试网站可达性和页面加载
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_basic_navigation.yaml \
  --config config/test_config.yaml
```

### 3. 文本到图像测试
```bash
# 测试AI图像生成功能
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_text_to_image.yaml \
  --config config/test_config.yaml
```

### 4. 图像到视频测试
```bash
# 测试视频转换功能
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_image_to_video.yaml \
  --config config/test_config.yaml
```

### 5. 完整集成测试
```bash
# 测试完整的用户流程
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_complete_test.yaml \
  --config config/test_config.yaml
```

## 🎬 闹海当前版本（剧本/分镜）冒烟用例

前置条件：
- 需要有效的登录态文件（`auth_session.json` + `auth_state_real.json`），并在 `config/config.yaml` 的 `browser.storage_state/session_state` 中指向它们。

### 1) 剧本列表冒烟（进入 AI创作/剧本列表）
```bash
python scripts/run_workflow_test.py \
  --workflow workflows/at/naohai_01_story_list_smoke.yaml \
  --config config/config.yaml
```

### 2) 新建剧本冒烟（打开弹窗并填写基础信息）
```bash
python scripts/run_workflow_test.py \
  --workflow workflows/at/naohai_02_create_story_smoke.yaml \
  --config config/config.yaml
```

### 3) 分镜管理冒烟（进入分镜管理页）
```bash
python scripts/run_workflow_test.py \
  --workflow workflows/at/naohai_03_storyboard_smoke.yaml \
  --config config/config.yaml
```

## 🧾 FC 用例索引

- FC 用例目录：`workflows/fc/`
- 索引文件：`workflows/fc/FC_INDEX.md`
- 单条执行示例：
```bash
python scripts/run_workflow_test.py \
  --workflow workflows/fc/naohai_FC_NH_002.yaml \
  --config config/config.yaml
```

---

## ⚙️ 配置说明

### URL配置
在执行命令中通过 `--workflow` 参数指定目标URL：

```bash
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_basic_navigation.yaml \
  --config config/test_config.yaml \
  # URL会自动从工作流中读取，也可以通过环境变量覆盖
  TEST_URL="http://your-target-url.com"
```

### 超时配置
配置文件中的超时设置（毫秒）：
- `page_load_timeout`: 页面加载超时（默认30000ms）
- `element_load_timeout`: 元素等待超时（默认10000ms）
- `image_generation_timeout`: 图像生成超时（默认30000ms）
- `video_generation_timeout`: 视频生成超时（默认45000ms）

---

## 📊 测试报告

执行完成后，测试报告将保存在以下位置：
- **JSON报告**: `test_reports/workflow_test_YYYYMMDD_HHMMSS.json`
- **HTML报告**: `test_reports/workflow_test_YYYYMMDD_HHMMSS.html`
- **截图文件**: `screenshots/` 目录下

### 报告内容
- **执行摘要**: 成功/失败状态、执行时间、各阶段耗时
- **阶段详情**: 每个阶段的步骤执行情况
- **错误分析**: 失败原因、重试次数、错误上下文
- **MCP观测数据**: 网络请求、性能指标、DOM变化
- **截图证据**: 关键步骤的可视化证据

---

## 🔧 自定义配置

### 选择器配置
如需测试不同的页面元素，修改 `config/config.yaml` 中的选择器：

```yaml
selectors:
  prompt_input: "#user-input"          # 自定义提示词输入框
  generate_image_button: ".submit-btn"    # 自定义生成按钮
  image_result: ".result-container img"  # 自定义结果区域
  generate_video_button: ".video-btn"     # 自定义视频按钮
  video_result: ".video-player video"    # 自定义视频播放器
```

### 测试提示词
在 `config/test_config.yaml` 中自定义测试提示词：

```yaml
test:
  prompt: "现在测试时间：${timestamp}"    # 支持变量替换
  # 可以添加更多测试用例
```

---

## 🚨 故障排除

### 常见问题

1. **网站无法访问**
   - 检查网络连接：`ping <NOWHI_HOST>`
   - 检查防火墙设置
   - 确认目标网站状态

2. **元素找不到**
   - 检查页面是否完全加载
   - 增加等待时间
   - 检查选择器是否正确
   - 查看页面源码确认元素存在

3. **MCP观测异常**
   - 确认MCP配置正确
   - 检查观测器权限
   - 查看MCP日志输出

4. **超时问题**
   - 根据网络状况调整超时值
   - 检查服务器响应时间
   - 考虑启用性能监控

---

## 📞 最佳实践

1. **测试环境隔离**
   - 使用独立的测试配置
   - 每次测试前清理缓存
   - 使用干净的网络环境

2. **渐进式测试**
   - 先通过基础测试验证核心功能
   - 逐步集成复杂功能
   - 最后执行完整端到端测试

3. **监控和日志**
   - 保留所有测试报告用于对比
   - 关注性能指标变化
   - 设置适当的日志级别

4. **截图策略**
   - 关键步骤必须有截图证据
   - 使用有意义的截图文件名
   - 定期清理旧截图文件

---

## 🎓 高级功能

### 自定义工作流
可以创建自定义的 `.yaml` 工作流文件，参考现有模板：

```yaml
workflow:
  name: "custom_test"
  description: "自定义测试流程"

  phases:
    - name: "custom_phase"
      steps:
        - action: "custom_action"
          # 自定义参数
```

### 批量测试
创建批量测试脚本来自动执行多个测试用例：

```bash
# 批量执行所有基础测试
for workflow in workflows/archive/nowhi_*.yaml; do
  python scripts/run_workflow_test.py --workflow $workflow --config config/test_config.yaml
done
```

---

这套工作流系统提供了从简单验证到复杂集成的完整测试覆盖，支持灵活配置和扩展。
