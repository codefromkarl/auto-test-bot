# 测试文档格式说明

## 概述

本项目采用**三层测试文档体系**，实现从业务需求到自动化执行的完整映射。

```
业务需求 → Spec文档 → Spec Registry → Workflow YAML → 自动化执行
```

## 三层文档体系

### 1. 业务规范层 (Spec Documents)

**位置**: `specs/` 目录

**文件命名**: `NH-{ID}-{TYPE}.md`

#### 文档结构模板

```markdown
# Spec: NH-XXX-XXX {测试名称}

## 🎯 Purpose
测试目的描述

## 🔭 Scope
- **适用**: 适用场景
- **包含**: 测试范围列表
- **不适用**: 排除范围

## 🔌 Preconditions & Gates
- **Env**: 环境要求
- **Config**: 配置文件路径
- **Account**: 账号权限

**Gates**:
1. **Gate-xxx**: 描述
2. **Gate-xxx**: 描述

## ✅ Acceptance Criteria
- **成功率**: 数值要求
- **响应时间**: 性能要求
- **稳定性**: 可重复性要求
- **覆盖度**: 功能覆盖要求
- **产物完整**: 输出要求

## 🗺️ Mapping
- **Workflows**: 关联的工作流列表
- **Robot Tags**: 标签列表
- **Command**: 执行命令

### 详细 Workflow 映射表格

| 测试场景 | Workflow文件 | 关键Steps | 验证点 |
|---------|-------------|-----------|--------|
| 场景1 | file1.yaml | steps | point |

## 🧾 Evidence Policy
- **Runs Directory**: 运行记录目录
- **File Naming**: 文件命名规则
- **Required Content**: 必需内容列表

## 📝 ChangeLog
- 日期: 变更说明
```

#### 实例参考

- `specs/NH-SMOKE-001.md` - 冒烟测试规范
- `specs/NH-CREATE-001.md` - 创建功能规范
- `specs/NH-SCRIPT-001.md` - 分镜功能规范

---

### 2. 注册配置层 (Spec Registry)

**位置**: `config/spec_registry.yaml`

#### 配置结构

```yaml
spec_registry:
  version: "1.0"

  # 默认策略
  defaults:
    leaf:
      retry: 0
      timeout_sec: 600
      evidence:
        screenshots: "on_failure"
        log: "always"
    suite:
      gate: "fail_fast"
      parallel: false

  # Spec定义
  NH-XXX-XXX:
    spec_id: "NH-XXX-XXX"
    name: "测试名称"
    description: "测试描述"

    # 执行模式
    modes:
      quick:
        description: "快速模式描述"
        include: ["TC.xxx.aaa", "TC.xxx.bbb"]
        exit_criteria:
          min_success_rate: 0.8

      full:
        description: "完整模式描述"
        include: ["TC.xxx.aaa", "TC.xxx.bbb", "TC.xxx.ccc"]
        exit_criteria:
          min_success_rate: 0.9

    # Leaf节点（可执行测试用例）
    leaf_tests:
      TC.xxx.aaa:
        id: "TC.xxx.aaa"
        name: "测试用例名称"
        description: "测试用例描述"
        type: "test"
        executor:
          kind: "workflow"
          ref: "workflows/xxx/yyy.yaml"

        assertions:
          - kind: "ui_element_present"
            target: "selector"
            severity: "critical"

        evidence:
          screenshots: "always"
          log: "always"

        tags: ["tag1", "tag2"]
        retry: 1
        timeout_sec: 300
```

#### 配置字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spec_id` | string | 是 | 规范唯一标识 |
| `name` | string | 是 | 规范名称 |
| `modes` | dict | 是 | 执行模式定义 |
| `leaf_tests` | dict | 是 | 具体测试用例定义 |

##### 执行模式字段

| 字段 | 说明 |
|------|------|
| `description` | 模式描述 |
| `include` | 包含的测试用例ID列表 |
| `exit_criteria.min_success_rate` | 最小成功率阈值 |

##### Leaf节点字段

| 字段 | 说明 |
|------|------|
| `id` | 测试用例唯一标识 |
| `executor.kind` | 执行器类型（目前仅支持workflow） |
| `executor.ref` | Workflow YAML文件路径 |
| `assertions` | 断言配置列表 |
| `evidence.screenshots` | 截图策略（always/on_failure/on_success） |
| `tags` | 标签列表 |
| `retry` | 重试次数 |
| `timeout_sec` | 超时时间（秒） |

---

### 3. 工作流定义层 (Workflow YAML)

**位置**: `workflows/` 目录（按类型分类）

- `workflows/at/` - 冒烟测试（Acceptance Test）
- `workflows/fc/` - 功能测试（Feature Test）
- `workflows/e2e/` - 端到端测试
- `workflows/rt/` - 回归测试（Regression Test）
- `workflows/resilience/` - 稳定性测试

#### YAML结构模板

```yaml
workflow:
  name: "workflow_name"
  description: "工作流描述"
  version: "rf-v1.0"

  # 可选：公共前置步骤（RF语义化）
  suite_setup:
    - action: "action_name"
      timeout: ${test.timeout.element_load}

  # 核心执行阶段
  phases:
    - name: "phase_name"
      description: "阶段描述"
      steps:
        - action: "action_type"
          param1: "value1"
          param2: "value2"
          timeout: ${test.timeout.element_load}

        - action: "wait_for"
          condition:
            selector: "css_selector"
            visible: true
          timeout: ${test.timeout.element_load}

  # 可选：成功标准
  success_criteria:
    - "成功条件描述1"
    - "成功条件描述2"

  # 可选：错误恢复策略
  error_recovery:
    - action: "recovery_action"
      timeout: ${test.timeout.element_load}
```

#### 支持的Action类型

| Action | 参数 | 说明 |
|--------|------|------|
| `open_page` | `url`, `timeout` | 打开页面 |
| `wait_for` | `condition.{selector, visible, not_visible}`, `timeout` | 等待元素 |
| `click` | `selector`, `timeout`, `optional` | 点击元素 |
| `input` | `selector`, `text`, `clear`, `timeout` | 输入文本 |
| `clear_input` | `selector`, `timeout` | 清空输入 |
| `screenshot` | `save_path`, `full_page`, `timeout`, `required` | 截图 |
| `assert_element_exists` | `selector`, `visible`, `timeout` | 断言元素存在 |
| `assert_element_count` | `selector`, `expected_count/min_count/max_count` | 断言元素数量 |
| `assert_logged_in` | 无 | 断言已登录 |
| `upload_file` | `selector`, `file_path`, `timeout` | 上传文件 |
| `move_slider` | `selector`, `value` | 移动滑块 |
| `save_data` | `key`, `value` | 保存数据到上下文 |

#### 语义化Actions（Semantic Actions）

项目支持通过`adapters/`注册业务语义化Actions，简化测试编写。

**示例**（引用自`workflows/fc/naohai_FC_NH_002_rf.yaml`）:

```yaml
workflow:
  suite_setup:
    - action: "rf_enter_ai_creation"
      timeout: ${test.timeout.element_load}

  phases:
    - name: "verify_story_cards_display"
      steps:
        - action: "rf_ensure_story_exists"
          timeout: ${test.timeout.element_load}

        - action: "rf_open_first_story_card"
          timeout: ${test.timeout.element_load}
```

语义化Actions在执行时会被展开为原子Action序列。

#### 变量替换

支持模板变量替换，格式为 `${variable.path}`。

| 变量 | 说明 | 示例 |
|------|------|------|
| `${test.url}` | 测试URL | `http://localhost:9020` |
| `${test.timeout.page_load}` | 页面加载超时 | `60000` |
| `${test.timeout.element_load}` | 元素加载超时 | `10000` |
| `${test.timeout.image_generation}` | 图片生成超时 | `30000` |
| `${test.timeout.video_generation}` | 视频生成超时 | `45000` |
| `${selectors.xxx}` | 选择器变量 | 来自adapter注册 |

---

## 创建新测试的完整流程

### 步骤1: 创建Spec文档

```bash
# 在specs/目录下创建新文档
vi specs/NH-FEATURE-001.md
```

### 步骤2: 在Spec Registry中注册

```bash
# 编辑config/spec_registry.yaml
vi config/spec_registry.yaml
```

添加Spec定义和leaf_tests。

### 步骤3: 创建Workflow YAML

```bash
# 在workflows/对应目录下创建
vi workflows/fc/naohai_FC_NH_XXX_rf.yaml
```

### 步骤4: 执行测试

```bash
# 通过Spec ID执行
python src/main_workflow.py --spec NH-FEATURE-001 --mode full

# 或直接执行单个Workflow
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_XXX_rf.yaml
```

---

## 执行方式对比

| 方式 | 命令 | 适用场景 |
|------|------|----------|
| Spec执行 | `python src/main_workflow.py --spec NH-XXX-001 --mode full` | 按业务规范批量执行 |
| Workflow执行 | `python src/main_workflow.py --workflow workflows/xxx/yyy.yaml` | 单个测试用例调试 |
| Spec引擎 | `python src/core/spec_execution_engine.py --spec NH-XXX-001 --mode full` | 通过引擎解析执行 |

---

## 文档最佳实践

### Spec文档编写

1. **Purpose简洁明确**: 用一句话说明测试的核心目的
2. **Scope边界清晰**: 明确包含和不包含的内容
3. **Gates可验证**: 每个Gate都有明确的判断条件
4. **Criteria可度量**: 成功标准必须可量化

### Workflow编写

1. **使用suite_setup**: 公共前置步骤提取到suite_setup
2. **step粒度适中**: 每个step只做一件事
3. **selector优先级**: 优先使用`data-testid`，其次使用稳定的选择器
4. **设置合理timeout**: 根据操作类型设置合适的超时时间

### Spec Registry配置

1. **模式分离**: quick/full/health模式有明显差异
2. **exit_criteria合理**: 成功率阈值要有实际意义
3. **tags规范使用**: 便于后续按标签筛选执行

---

## 验证清单

创建新测试时确认：

- [ ] Spec文档已创建，包含完整字段
- [ ] Spec Registry中已注册
- [ ] Workflow YAML已创建，语法正确
- [ ] Workflow可独立执行成功
- [ ] 通过Spec模式执行成功
- [ ] 截图和日志正确生成
- [ ] 失败场景下错误恢复有效
