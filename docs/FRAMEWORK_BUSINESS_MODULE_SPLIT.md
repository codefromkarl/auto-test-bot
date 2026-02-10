# 功能模块与业务模块拆分总结

> 基于RF架构，实现功能框架与业务适配器的完全解耦

## 目录

- [架构概述](#架构概述)
- [拆分后的目录结构](#拆分后的目录结构)
- [使用 Bot 的方式](#使用-bot-的方式)
- [数据格式规范](#数据格式规范)
- [测试验证结果](#测试验证结果)

---

## 架构概述

### 设计原则

| 原则 | 应用说明 |
|------|----------|
| **KISS** | 配置驱动，最小化代码侵入 |
| **DRY** | 通用功能模块化，业务配置统一管理 |
| **SOLID-S** | 每个业务适配器（Adapter）单一职责 |
| **SOLID-O** | 扩展新业务无需修改框架代码 |
| **SOLID-D** | 业务模块依赖抽象接口（AdapterProtocol） |

### 分层架构

```
┌─────────────────────────────────────────────────────────┐
│  【功能模块】Framework - 通用测试框架             │
├─────────────────────────────────────────────────────────┤
│  framework/core/protocol/     # AdapterProtocol 接口   │
│  framework/core/adapter_loader.py  # 动态加载器        │
│  framework/core/executor/        # WorkflowExecutor     │
│  src/models/semantic_variables.py  # 语义变量解析        │
│  src/executor/workflow_executor.py  # 执行引擎(增强)     │
│  src/browser_manager.py           # 浏览器管理        │
│  src/reporter/                   # 报告生成          │
└─────────────────────────────────────────────────────────┘
                    ↓ 实现
┌─────────────────────────────────────────────────────────┐
│  【业务模块】Adapters - 业务适配器                  │
├─────────────────────────────────────────────────────────┤
│  adapters/base.py              # BaseAdapter 基类    │
│  adapters/naohai/adapter.py   # NaohaiAdapter 实现  │
│  adapters/naohai/selectors.yaml # Selector 配置      │
│  adapters/naohai/semantic_actions/ # 语义 Action    │
│  adapters/example/               # 示例适配器       │
│  adapters/default/               # 默认适配器       │
└─────────────────────────────────────────────────────────┘
```

---

## 拆分后的目录结构

```
auto-test-bot/
│
├── framework/                    # 【新增】功能框架目录
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── adapter_loader.py      # 适配器动态加载器
│       ├── protocol/
│       │   ├── __init__.py
│       │   └── adapter.py       # AdapterProtocol 接口
│       └── executor/             # 执行器模块（待迁移）
│           └── __init__.py
│
├── adapters/                    # 【新增】业务适配器目录
│   ├── __init__.py
│   ├── base.py                  # BaseAdapter 抽象基类
│   ├── default/
│   │   ├── __init__.py
│   │   └── adapter.py         # 默认适配器
│   ├── example/
│   │   ├── __init__.py
│   │   └── adapter.py         # 示例适配器
│   └── naohai/                 # 闹海业务适配器
│       ├── __init__.py
│       ├── adapter.py             # NaohaiAdapter 实现
│       ├── selectors.yaml         # Selector 映射配置
│       ├── semantic_actions/      # 语义 Action
│       │   ├── __init__.py
│       │   └── actions.py       # 所有语义 Action
│       └── workflows/            # 测试用例目录
│           ├── at/              # 冒烟测试
│           ├── fc/              # 功能测试
│           └── e2e/             # 端到端测试
│
├── src/                         # 【保留】原有源码
│   ├── models/
│   │   └── semantic_variables.py # 【新增】语义变量解析
│   ├── executor/
│   │   └── workflow_executor.py  # 【修改】支持适配器
│   ├── models/action.py          # 【修改】语义变量支持
│   ├── models/workflow.py        # 【修改】语义变量支持
│   └── ... (其他现有文件)
│
├── tests/
│   ├── unit/
│   │   └── test_framework_adapter_selector_shorthand.py  # 【新增】
│   └── integration/
│       └── test_workflow_executor.py                   # 【扩展】
│
└── bot.py                       # 【新增】主入口（可选）
```

---

## 使用 Bot 的方式

### 1. 配置驱动方式（推荐）

#### 适配器配置文件 - `adapters/naohai/selectors.yaml`

```yaml
# 支持层级结构的 selector 映射
navigation:
  ai_creation: '.nav-routerTo-item:has-text("AI创作"), text=AI创作'
  story_list: 'text=剧本列表'
  storyboard: '.step-item:has-text("分镜管理"), text=分镜管理'

story_list:
  card: 'div.list-item:not(.add-item)'
  add_btn: '.add-item'

storyboard:
  container: '.storyboard-section'
  suggest_btn: '.suggest-count, text=建议分镜'
```

#### 工作流定义 - `adapters/naohai/workflows/at/smoke.yaml`

```yaml
workflow:
  name: naohai_smoke
  description: 冒烟测试
  adapter: naohai  # 指定使用的适配器

  phases:
    - name: enter_story_list
      steps:
        # 使用映射 selector (.xxx 简写)
        - action: click
          selector: .navigation.ai_creation
        - action: wait_for
          condition:
            selector: .story_list.card
            visible: true
```

### 2. 代码扩展方式

#### 创建新业务适配器

```python
# adapters/newsite/adapter.py
from adapters.base import BaseAdapter

class NewSiteAdapter(BaseAdapter):
    """新站点业务适配器"""

    def register_selectors(self) -> Mapping[str, str]:
        return {
            "navigation.login": "#btn-login",
            "login.username": "input[name='username']",
            "login.password": "input[name='password']",
        }

    def register_semantic_actions(self) -> Mapping[str, Type[SemanticAction]]:
        from .semantic_actions import LoginAction, NavigateHomeAction
        return {
            "login": LoginAction,
            "navigate_home": NavigateHomeAction,
        }

    def get_config(self) -> Dict[str, Any]:
        return {
            "base_url": "https://example.com",
            "timeout": 30000,
        }
```

#### 适配器配置 - `adapters/newsite/selectors.yaml`

```yaml
selectors:
  navigation:
    login: "#btn-login"
    home: "#nav-home"

  login:
    username: "input[name='username']"
    password: "input[name='password']"
    submit: "button[type='submit']"
```

### 3. 命令行使用

```bash
# 使用指定适配器运行测试
python src/main_workflow.py --adapter naohai --workflow workflows/at/smoke.yaml

# 使用环境变量指定适配器
export AUTO_TEST_BOT_ADAPTER=naohai
python src/main_workflow.py --workflow workflows/at/smoke.yaml

# 指定模块:类名格式
python src/main_workflow.py --adapter adapters.naohai.adapter:NaohaiAdapter --workflow test.yaml

# 调试模式
python src/main_workflow.py --adapter naohai --debug

# 并行执行多个工作流
python src/main_workflow.py --adapter naohai --workflows workflows/at/*.yaml
```

### 4. Python API 使用

```python
from framework.core.adapter_loader import load_adapter
from src.executor import WorkflowExecutor

# 动态加载适配器
adapter = load_adapter("naohai")  # 支持多种格式

# 创建执行器
executor = WorkflowExecutor(
    config={"adapter": "naohai", "test": {"url": "..."}},
    browser_manager=browser_manager,
    mcp_observer=None
)

# 执行工作流
result = await executor.execute_workflow(workflow)
print(result["overall_success"])
```

---

## 数据格式规范

### 1. 适配器配置格式

#### `selectors.yaml` - Selector 映射

```yaml
# 层级结构映射（支持点路径引用）
selectors:
  navigation:
    ai_creation: '.nav-routerTo-item:has-text("AI创作")'
    story_list: 'text=剧本列表'

  story_list:
    card: 'div.list-item:not(.add-item)'
    add_btn: '.add-item'

  storyboard:
    tab: '.step-item:has-text("分镜管理")'
    new_btn: 'text=新增分镜'

# 或扁平映射
flat_selectors:
  story_list_item: 'div.list-item:not(.add-item)'
  add_story_button: '.add-item'
```

#### `config.yaml` - 业务配置

```yaml
adapter:
  name: naohai
  version: "1.0.0"
  description: "闹海AI创作平台适配器"

test:
  url: "https://example.com"
  timeout:
    page_load: 30000
    element_load: 10000
```

### 2. 工作流数据格式

```yaml
workflow:
  name: test_workflow
  description: 测试描述
  adapter: naohai  # 适配器名称
  version: "1.0"

  # 全局变量
  variables:
    test_url: "https://example.com"
    timeout: 30000

  # 前置条件
  setup:
    - action: semantic.login
      username: ${config.user}
      password: ${config.pass}

  # 主流程
  phases:
    - name: phase_name
      steps:
        # 原子 Action
        - action: open_page
          url: ${variables.test_url}

        # 使用映射 Selector (.xxx 简写)
        - action: click
          selector: .navigation.ai_creation

        # 使用模板变量
        - action: wait_for
          condition:
            selector: ${selectors.story_list.card}
            visible: true

        # 语义 Action (适配器注册)
        - action: semantic.enter_ai_creation

        # 可选步骤（失败不影响整体）
        - action: click
          selector: .story_list.add_btn
          optional: true

  # 后置清理
  teardown:
    - action: logout

  # 成功标准
  success_criteria:
    - 进入指定页面
    - 操作完成无错误

  # 错误恢复
  error_recovery:
    - action: semantic.recover_to_home
      timeout: 10000
```

### 3. 语义变量语法

| 语法 | 说明 | 示例 |
|------|------|------|
| `.xxx` | 引用适配器 selector（点路径支持） | `.navigation.ai_creation` |
| `.a.b.c` | 多层路径引用 | `.story_list.card` |
| `${path}` | 模板变量查找 | `${test.url}` |
| `${selectors.xxx}` | 显式引用 selectors | `${selectors.navigation.login}` |

---

## 测试验证结果

### 单元测试

```bash
$ python -m pytest tests/unit/test_framework_adapter_selector_shorthand.py -v

============================= test session starts ==============================
platform linux -- Python 3.13.9, pytest-9.0.2
collected 1 item

tests/unit/test_framework_adapter_selector_shorthand.py::test_dot_selector_shorthand_resolves_from_loaded_adapter PASSED [100%]

============================== 1 passed in 0.03s ===============================
```

### 集成测试

```bash
$ python -m pytest tests/integration/test_workflow_executor.py -v

collected 11 items

tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_single_action_execution PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_wait_for_tries_all_candidates PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_semantic_action_step_name_fallback PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_suite_setup_is_executed PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_error_recovery_runs_on_failure PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_workflow_execution_success PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_workflow_execution_failure PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_workflow_validation PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_phase_validation PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_context_operations PASSED
tests/integration/test_workflow_executor.py::TestWorkflowExecutor::test_yaml_parsing PASSED

============================== 11 passed in 0.05s ===============================
```

**测试结果**: ✅ 所有测试通过（12/12）

---

## Codex 与 Gemini 任务分工

### Codex 任务 - Framework 核心代码

| 文件 | 内容 |
|------|------|
| `framework/core/protocol/adapter.py` | AdapterProtocol 接口定义 |
| `framework/core/adapter_loader.py` | 适配器动态加载器（支持多种格式） |
| `src/models/semantic_variables.py` | 语义变量解析（`.xxx` 和 `${path}`） |
| `src/models/action.py` | 修改支持语义变量 |
| `src/models/workflow.py` | 修改支持语义变量 |
| `tests/unit/test_framework_adapter_selector_shorthand.py` | 单元测试 |
| `adapters/default/` | 默认适配器 |
| `adapters/example/` | 示例适配器 |

### Gemini 任务 - Adapters 业务结构

| 文件 | 内容 |
|------|------|
| `adapters/base.py` | BaseAdapter 抽象基类 |
| `adapters/naohai/adapter.py` | NaohaiAdapter 实现 |
| `adapters/naohai/selectors.yaml` | Selector 映射配置（层级结构） |
| `adapters/naohai/semantic_actions/actions.py` | 所有闹海语义 Action |

---

## 关键设计决策

### 1. 适配器加载器支持多种格式

```python
# 支持的格式
"naohai"                    # -> adapters.naohai.adapter
"adapters.naohai.adapter"      # -> 直接导入
"naohai:NaohaiAdapter"       # -> 模块:类名
"adapters.naohai.adapter:Naohai"  # -> 模块.文件:类名
```

### 2. Selector 支持点路径

```yaml
selectors:
  navigation:
    ai_creation: '#btn-ai'
    story_list: '#nav-story'

# 工作流中可引用
selector: .navigation.ai_creation  # 展开为 '#btn-ai'
selector: .navigation.story_list   # 展开为 '#nav-story'
```

### 3. 语义变量统一解析

```python
# 支持 .xxx 选择器简写
".navigation.ai_creation" -> 从 adapters selectors 查找

# 支持 ${path} 模板变量
"${test.url}" -> 从 config/test/url 查找
"${timestamp}" -> 从 template_context 查找

# 类型保持：完整字符串占位时保留类型
"${test.timeout}" -> 30000 (int) 而非 "30000"
```

### 4. 向后兼容

- 保留原有的 `src/models/semantic_action.py` 中的语义 Action
- 保留原有工作流格式不变
- 保留 `naohai_adapter_v2.py` 的功能（事件系统、插件等）

---

## 下一步建议

1. **迁移 framework 模块** - 将 `src/` 中的通用代码逐步移到 `framework/`
2. **扩展 selectors.yaml** - 完善闹海的 selector 映射
3. **创建更多适配器** - 为其他业务创建独立适配器
4. **添加集成测试** - 验证真实工作流在新架构下运行
5. **文档完善** - 补充 API 参考和最佳实践

---

**文档版本**: v1.0
**创建日期**: 2026-01-03
**测试状态**: ✅ 所有单元/集成测试通过
