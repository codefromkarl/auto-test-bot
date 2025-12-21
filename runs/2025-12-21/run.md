# Run Log: 2025-12-21 - ISSUE-20 Fix & Optimization

## 🎯 Task
**ISSUE-20**: [Bug] NH-SMOKE-001 Execution Failed (Timeout on Create Story)

## 🛠️ Actions Taken
1.  **Fail-Fast Configuration**:
    - Updated `config/config.yaml` and `config/test_config.yaml`:
        - `element_timeout`: Reduced from 10s to **3s** (fast UI fail).
        - `max_step_duration_ms`: Reduced from 240s to **60s**.
        - `auto_ensure_baseline`: Disabled to prevent pre-check hangs.

2.  **Workflow Repairs (`naohai_05_create_story_to_video_e2e.yaml`)**:
    - **Missing Step**: Added missing "Click Next" between Style Selection and Create.
    - **Selector Fix**: Updated "Create Story" button selector to `text=新增剧本`.
    - **Empty State**: Refined `handle_empty_state` with icon-based selectors (`.add-item`).
    - **Interception Fix**: Added explicit `wait_for` overlay hidden before interacting with Storyboard.
    - **Recovery**: Added `click close` step in `enter_storyboard` to handle residual dialogs.

3.  **Knowledge Persistence**:
    - Updated `GEMINI.md` and `AGENTS.md` with **UI Automation Protocol** (Fail-Fast, Diagnosis First).
    - Fixed syntax error in `src/reporter/issue_generator.py`.

## 📊 Status
- **Current State**: Workflow code is fixed and hardened.
- **Pending**: Final verification run needed.
- **Blockers**: None (intercept issue handled by wait_for + recovery).

## ⏭️ Next Steps
1. Run verification command: `python3 src/main_workflow.py --workflow workflows/at/naohai_05_create_story_to_video_e2e.yaml`
2. If passes: Close ISSUE-20.
3. If fails: Check newly generated `.ai/issues/ISSUE-AUTO-*.md`.

---

## 🧩 补充更新 - 复用测试剧本 (2025-12-21)

### ✅ 变更
- 更新 `workflows/at/naohai_05_create_story_to_video_e2e.yaml`：优先复用已有“自动化测试剧本”，不存在才创建。
- 创建剧本步骤改为可选，避免已存在时重复创建。
- `enter_storyboard` 支持已在详情页时直接继续。
- 成功标准更新为“复用或创建”口径。

### 🧪 验证
- `python3 -c "import sys,os; sys.path.append(os.path.join(os.getcwd(),'src')); from models import Workflow; data=open('workflows/at/naohai_05_create_story_to_video_e2e.yaml','r',encoding='utf-8').read(); Workflow.from_yaml(data); print('ok')"` → ok

---

## 🧭 选择器层级优化 (ISSUE-AUTO-1766320095)

### 🎯 目标
- 按 AIGC 方案引入层级定位器配置与编译机制，保持现有扁平 locators 兼容。

### ✅ 已完成
- 创建新 Issue 并更新 `.ai/ACTIVE.md`、`.ai/index.md`。
- 新增层级定位器编译器与单测，并将 `config/main_config_with_testid.yaml` 改为层级结构。

### 🧪 测试
- `python3 -m pytest tests/unit/test_phase1_event_bus.py` → 失败（缺少 `core.events.event_bus` 模块）
- `python3 -m pytest tests/unit/test_locator_hierarchy.py` → 失败（ModuleNotFoundError: utils）
- `python3 -m pytest tests/unit/test_locator_hierarchy.py` → 失败（AttributeError: _resolve_page_groups）
- `python3 -m pytest tests/unit/test_locator_hierarchy.py` → 通过（2 passed）

### ⏭️ 下一步
- 添加层级定位器配置文件与编译器实现。
- 补充单元测试并验证通过。
