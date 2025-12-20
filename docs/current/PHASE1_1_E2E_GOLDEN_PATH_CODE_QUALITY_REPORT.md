# Phase 1.1 E2E 黄金路径测试框架 - 代码质量评估报告

**评估时间**：2025-12-18  
**评估范围**：
- `workflows/e2e/naohai_E2E_GoldenPath.yaml`
- `scripts/run_e2e_test.py`
- 新增静态校验与单测（保证可解析、可评估覆盖）

---

## Phase 1：Observation（可观察事实）

1. `workflows/e2e/naohai_E2E_GoldenPath.yaml` 在解析阶段失败：`Workflow.from_yaml` 报错 `Unknown action type: open_site`（suite_setup 内存在执行器不识别的 action）。
2. `scripts/run_e2e_test.py` 无法导入：导入 `src/main_workflow.py` 时触发 `ModuleNotFoundError: No module named 'utils'`（原因是 `src/` 未被优先插入到 `sys.path`，`utils` 实际位于 `src/utils`）。
3. 原黄金路径 workflow 使用了多处不存在的 action/占位符（例如 `navigate_to_ai_create`、`${test.timeout.ai_generation}`、`${test.timeout.download}`），即便 YAML 语法正确，也会在解析/执行阶段失败。
4. 现有仓库中已存在可复用的 FC workflow 片段（剧本创建、分集新增、分镜/提示词、融合生图、视频创作入口、导出资源包等），并且这些片段使用的 action 均为执行器支持的 atomic action。

---

## Phase 2：Root Cause Analysis（根因分析）

**症状**：
- E2E workflow 无法解析/无法执行
- E2E 运行脚本无法启动

**触发条件**：
- 调用 `Workflow.from_yaml` 解析黄金路径文件
- 运行/导入 `scripts/run_e2e_test.py`

**根因**（最小充分原因）：
1. **DSL 与执行器动作集合不一致**：黄金路径 YAML 使用了 `open_site` 等未被 `models.action.Action.create()` 支持的 action，导致解析阶段失败。
2. **运行器导入路径策略错误**：`scripts/run_e2e_test.py` 通过导入 `src/main_workflow.py` 间接依赖 `utils` 顶层包，但没有将 `src/` 放入 `sys.path`，从而模块解析失败。
3. **占位符命名与模板上下文不一致**：workflow 使用了未在模板上下文提供的 `${test.timeout.*}` 键，执行时会触发 unresolved template variable。

---

## Phase 3：Planning（最小修改方案）

**目标**（成功标准）：
- `workflows/e2e/naohai_E2E_GoldenPath.yaml` 可被 `Workflow.from_yaml` 成功解析
- `scripts/run_e2e_test.py --dry-run` 能完成：配置加载 + workflow 校验 + 覆盖度评估 + 生成汇总报告
- 静态评估覆盖 7 个关键阶段（Phase 1.1）

**方案**：
1. 重写 E2E workflow：仅使用已支持的 atomic/rf_* action 与已存在占位符键（page_load/element_load/image_generation/video_generation）。
2. 重构 E2E 运行脚本：复用 `scripts/run_workflow_test.py` 的导入/执行路径与执行器组件，增加 `--dry-run` 与汇总 JSON 报告输出。
3. 新增黄金路径静态校验器与单测：确保长期不会回归到“YAML 写了但解析不了”的状态。

---

## Phase 4：Execution（已实施修改）

1. `workflows/e2e/naohai_E2E_GoldenPath.yaml`
   - 替换 `open_site` / `navigate_to_ai_create` 等未知 action → `open_page` / `rf_enter_ai_creation` 等已支持 action
   - 7 个 phase 保留并对齐 FC 现有用例选择器，确保“可执行 + 可静态校验”
   - `error_recovery` 移除未知 action，仅保留可执行的通用回退步骤
2. `scripts/run_e2e_test.py`
   - 修复 import 与 `sys.path`（优先插入 `src/`），避免 `utils`/`models`/`executor` 等顶层包找不到
   - 新增 `--dry-run`：只解析 + 校验 + 覆盖评估，不启动浏览器
   - 生成 `reports/e2e/golden_path_summary_*.json` 汇总报告，并在执行时复用 `DecisionReporter` 输出详细 json/html 报告
3. 新增 `src/e2e/golden_path_validator.py`
   - 校验 7 阶段是否齐全、是否包含 screenshot 证据步骤、success_criteria 数量建议
   - 输出静态覆盖度（present/evidence ratio）
4. 新增单测 `tests/unit/test_phase1_1_e2e_golden_path_workflow.py`
   - 保障黄金路径 workflow 可解析且覆盖 7 阶段不回归

---

## Phase 5：Verification（验证步骤与结果）

在本仓库内可无网络验证的内容：
1. `Workflow.from_yaml` 能解析黄金路径 YAML（单测覆盖）
2. `python scripts/run_e2e_test.py --dry-run` 能运行并生成汇总报告（无需浏览器/网络）

说明：真实 E2E（启动浏览器访问站点）属于在线依赖场景，需要在具备可访问目标站点的环境中执行验证。

---

## 代码质量评估（结论）

### 1) 可维护性
- ✅ 新增了静态校验与单测，避免“配置文件漂移”导致的不可执行状态
- ✅ `run_e2e_test.py` 与 `run_workflow_test.py` 使用一致的导入路径策略，降低未来维护成本

### 2) 正确性风险
- ⚠️ workflow 中部分步骤标记为 `optional: true`（best-effort），可减少脆弱性，但也意味着“业务强校验”程度有限；如需严格验收，应逐步将关键断言从 optional 提升为必选（并补齐更可靠的 selector/testid）。
- ⚠️ 真实 AI 生成（分析/融合/视频）存在时延与波动，建议通过配置/标志位支持“只读黄金路径”和“全量黄金路径”两种模式。

### 3) 一致性与工程化
- ✅ 引入 `src/e2e/` 作为 E2E 校验逻辑归属，结构清晰
- ✅ 汇总报告结构化输出，利于后续接入 CI 或质量门禁

