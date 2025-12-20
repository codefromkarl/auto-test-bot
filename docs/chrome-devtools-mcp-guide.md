# Chrome DevTools MCP 使用指南

> **核心原则**: MCP 只用于"看清楚发生了什么"，不是"替我们做事情"

## 📋 目录

1. [核心原则](#核心原则)
2. [使用场景](#使用场景)
3. [禁止用途](#禁止用途)
4. [正确使用流程](#正确使用流程)
5. [配置说明](#配置说明)
6. [数据采集规范](#数据采集规范)
7. [最佳实践](#最佳实践)

## 🎯 核心原则

### MCP 在架构中的定位

```
【执行层 - 确定】
├── Playwright（唯一执行引擎）
├── 固定 selectors
├── 固定等待条件
└── 可 CI / 可复现

【观察层 - 探索】
├── Chrome DevTools MCP
├── 人工观察
└── AI 分析

【智能层 - 建议】
├── AI 分析失败原因
├── AI 提供修复建议
└── AI 生成报告
```

### 必须遵守的铁律

- ✅ **执行层绝不依赖 MCP**
- ✅ **MCP 永远不出现在主执行路径中**
- ✅ **MCP 只用于调试和证据采集**

## 🔍 使用场景

### ✅ 1. 行为观测（核心用途）

当测试失败时，使用 MCP 回答：

- 点击是否真的触发了 router？
- DOM 是否发生变化？
- 是否发起了网络请求？
- JS 是否抛出异常？

**触发信号**:
```yaml
# 当出现这些情况时启用 MCP
debug_triggers:
  - element_not_found
  - timeout_exceeded
  - assertion_failed
  - unexpected_navigation
```

### ✅ 2. Selector 探索与冻结

用途：
- 高亮 selector 对应元素
- 确认是否唯一
- 确认是否被遮挡/disabled

**工作流程**:
```python
# 1. 使用 MCP 探索
element_info = mcp_helper.explore_selector(".nav-routerTo-item")

# 2. 验证稳定性
if element_info.is_stable and element_info.is_unique:
    # 3. 写回 Playwright 代码
    update_test_case(selector=".nav-routerTo-item")
    # 4. 以后不再用 MCP 跑这个用例
```

### ✅ 3. 失败证据采集

当测试失败时，自动收集：

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "click",
  "selector": ".nav-routerTo-item",
  "expected": {
    "element": ".ai-create-root",
    "router_change": true,
    "network_request": "/api/ai/create"
  },
  "actual": {
    "dom_change": "none",
    "router_event": false,
    "network_requests": [],
    "console_errors": ["TypeError: Cannot read property 'push' of undefined"]
  },
  "evidence": {
    "before_screenshot": "before_click.png",
    "after_screenshot": "after_click.png",
    "dom_snapshot": "dom_snapshot.json",
    "network_log": "network.json"
  }
}
```

## ❌ 禁止用途

### 1. 不得作为执行引擎

```python
# ❌ 错误 - MCP 参与执行决策
if mcp_helper.is_element_visible(selector):
    result = await mcp_click(selector)
else:
    result = await playwright_click(selector)

# ✅ 正确 - 只有 Playwright 执行
result = await page.click(selector)
```

### 2. 不得参与自动决策

```python
# ❌ 错误 - 让 MCP 决定流程
elements = mcp_helper.get_interactive_elements()
chosen = ai.choose_element(elements)
await mcp_click(chosen)

# ✅ 正确 - 人类定义的流程
await page.click("#generate-button")  # 固定的、明确的
```

### 3. 不得作为长期依赖

- MCP 是调试工具，不是系统组件
- MCP 是探索工具，不是运行时服务
- MCP 是一次性工具，不是架构核心

## 🔄 正确使用流程

### 场景1: 日常开发调试

```bash
# 1. 正常测试（纯 Playwright）
python src/main.py --config config/test_config.yaml

# 2. 失败后启用调试
python src/main.py --debug --mcp-diagnostic

# 3. 分析 MCP 采集的证据
# 4. 修复 Playwright 代码
# 5. 再次用纯 Playwright 验证
```

### 场景2: CI 环境

```yaml
# ci_config.yaml
ci:
  # CI 永远不启用 MCP
  enable_mcp: false
  # 但失败时保存现场
  save_failure_evidence: true
```

### 场景3: AI 自动修复

```python
async def auto_fix_test_failure(test_result):
    # 1. MCP 采集事实
    evidence = await mcp_collector.collect_evidence(test_result)

    # 2. AI 分析
    analysis = await ai_analyzer.analyze(evidence)

    # 3. 生成修复建议
    fix_suggestion = await ai_advisor.suggest_fix(analysis)

    # 4. 人工 Review
    if human_review_approves(fix_suggestion):
        # 5. 更新 Playwright 代码
        update_test_code(fix_suggestion)

    # MCP 不参与执行！
```

## ⚙️ 配置说明

### 调试模式开关

```yaml
# config/config.yaml
debug:
  # 开发/调试时启用
  enable_devtools_mcp: true

  # 失败时自动采集证据
  capture_on_failure: true

  # MCP 工具开关
  mcp_tools:
    console: true
    network: true
    performance: false  # 除非性能问题
    dom_debug: true
    screenshot: true
```

### CI/生产模式

```yaml
# config/ci_config.yaml
debug:
  # CI/生产永远不启用 MCP
  enable_devtools_mcp: false

  # 但保留失败现场
  capture_on_failure: true

  # 仅用 Playwright 保存证据
  evidence_tools:
    playwright_screenshot: true
    playwright_dom: true
```

## 📊 数据采集规范

### 最小上下文集

用于 AI 分析的最小数据集：

```python
class MinimumEvidenceSet:
    """AI 自动修复需要的最小证据集"""

    def __init__(self):
        self.action = None          # 执行的动作
        self.selector = None         # 使用的 selector
        self.expected = None         # 期望结果
        self.actual = None          # 实际结果
        self.timestamp = None        # 时间戳

    # 必须包含的结构化事实
    def to_dict(self):
        return {
            "action": self.action,
            "selector": self.selector,
            "expected": {
                "element": self.expected.get("element"),
                "router_event": self.expected.get("router_change"),
                "network_request": self.expected.get("api_call")
            },
            "actual": {
                "dom_change": self.actual.get("dom_change"),
                "router_event": self.actual.get("router_event"),
                "network_requests": self.actual.get("network_requests"),
                "console_errors": self.actual.get("console_errors")
            },
            "evidence_files": self.get_evidence_files()
        }
```

### 证据文件命名规范

```
evidence/
├── 20240115_1030_click_nav/
│   ├── before.png              # 操作前截图
│   ├── after.png               # 操作后截图
│   ├── dom_before.json         # 操作前 DOM
│   ├── dom_after.json          # 操作后 DOM
│   ├── network.json            # 网络请求
│   └── context.json            # 上下文信息
```

## 💡 最佳实践

### 1. 用完 MCP 就"冻结结论"

每次使用 MCP 后，必须能回答：

> "以后我不需要再用 MCP 跑这个 case 了"

**检查清单**：
- [ ] Selector 已经稳定
- [ ] 等待条件已明确
- [ ] 错误处理已添加
- [ ] 用例可独立复现

### 2. MCP 代码隔离

```
src/
├── browser/              # Playwright - 主执行路径
├── steps/               # 测试步骤 - 主执行路径
└── debug/               # MCP - 仅调试路径
    ├── mcp_helper.py
    ├── evidence_collector.py
    └── analyzer.py
```

**规则**：
- `browser/` 和 `steps/` 绝不 import MCP
- 只有 `debug/` 可以调用 MCP
- 主流程通过配置决定是否调用 debug/

### 3. 渐进式调试

```python
class DebugStrategy:
    """渐进式调试策略"""

    def investigate_failure(self, failure):
        # Level 1: 基础证据（Playwright）
        if not self.is_complex_failure(failure):
            return self.collect_basic_evidence(failure)

        # Level 2: DOM 分析（MCP）
        if failure.type == "element_not_found":
            return self.collect_dom_evidence(failure)

        # Level 3: 网络分析（MCP）
        if failure.type == "api_timeout":
            return self.collect_network_evidence(failure)

        # Level 4: 全面分析（MCP）
        if failure.is_intermittent:
            return self.collect_full_evidence(failure)
```

### 4. 防止 MCP 滥用

```python
# config/mcp_guardrails.yaml
guardrails:
  max_mcp_calls_per_session: 50
  max_evidence_size_mb: 100
  require_human_review_after: 10
  auto_disable_on_ci: true

  # 强制降级条件
  force_playwright_only:
    - known_stable_selector
    - regression_test
    - performance_test
```

## 🚨 红线警告

### 如果你发现自己在做这些，立即刹车：

1. **"让 AI 通过 MCP 看页面，然后决定点什么"**
   - ❌ 这是探索，不是测试
   - ✅ 应该固定 selector，用 Playwright 执行

2. **"根据 MCP 返回的页面状态，动态选择执行路径"**
   - ❌ 这是不可复现的
   - ✅ 应该明确所有路径，用断言验证

3. **"每次测试都开启 MCP，以获得更多信息"**
   - ❌ 这是性能浪费
   - ✅ 应该只在失败时开启 MCP

### 正确的心态

- **MCP 是显微镜**，不是手术刀
- **MCP 是黑匣子记录器**，不是飞行员
- **MCP 是法医工具**，不是医生

## 📚 相关文档

- [架构设计文档](docs/architecture.md)
- [API 参考](docs/api.md)
- [故障排查指南](docs/troubleshooting.md)

## 🆘 获取帮助

- 查看 `logs/mcp_*.log` 了解 MCP 调用
- 检查 `evidence/` 目录收集的证据
- 使用 `--mcp-diagnostic` 获取详细诊断信息

---

**记住一句话**：

> **MCP 用来"看清楚"，
> 代码用来"跑稳定"，
> AI 用来"帮人更快修"。**