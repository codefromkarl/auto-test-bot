# Spec: NH-SMOKE-001 闹海核心功能冒烟测试

## 🎯 Purpose
快速验证闹海系统核心功能的可用性和稳定性，确保系统基本功能正常，为后续详细测试提供基础保障。

## 🔭 Scope
- **适用**：系统可用性快速检查、发布前冒烟测试、CI/CD集成
- **包含**：
  1. 系统导航和认证检查
  2. 核心页面访问验证
  3. 基础功能操作测试
  4. 关键流程端到端验证
- **不适用**：详细功能测试、性能测试、边界条件测试

## 🔌 Preconditions & Gates
- **Env**: AI创作服务可用（Port 9020），用户已登录且Token有效
- **Config**: 使用`config/main_config_with_testid.yaml`或对应环境配置
- **Account**: 测试账号具有基础访问权限
- **System**: 系统基础服务正常，数据库连接可用

**Gates**:
1. **Gate-Env**: 系统健康检查，核心服务响应正常
2. **Gate-Auth**: 用户认证成功，会话有效
3. **Gate-Access**: 关键页面可访问，基础UI元素存在
4. **Gate-Function**: 核心功能可执行，无阻塞错误

## ✅ Acceptance Criteria
- **核心成功率**: Quick模式≥80%，Full模式≥90%，Health模式100%
- **响应时间**: 页面加载≤5秒，操作响应≤3秒
- **稳定性**: 关键功能可重复执行，无明显随机失败
- **覆盖度**: 涵盖主要用户路径和核心业务功能
- **产物完整**: 必须生成`report.html`和`logs.txt`，包含冒烟测试摘要

## 🗺️ Mapping
- **Workflows**:
  - **导航和基础访问**:
    - `workflows/fc/naohai_FC_NH_051_rf.yaml` (导航项展示验证)
    - `workflows/fc/naohai_FC_NH_052_rf.yaml` (AI创作只读验证)
  - **基础功能UI验证**:
    - `workflows/fc/naohai_FC_NH_053_rf.yaml` (Tab项存在验证)
    - `workflows/fc/naohai_FC_NH_054_rf.yaml` (新增按钮存在验证)
    - `workflows/fc/naohai_FC_NH_055_rf.yaml` (创建弹窗只读验证)
    - `workflows/fc/naohai_FC_NH_056_rf.yaml` (输入框存在验证)
    - `workflows/fc/naohai_FC_NH_057_rf.yaml` (上传组件存在验证)
    - `workflows/fc/naohai_FC_NH_058_rf.yaml` (比例选项存在验证)
    - `workflows/fc/naohai_FC_NH_059_rf.yaml` (下一步按钮存在验证)
    - `workflows/fc/naohai_FC_NH_060_rf.yaml` (默认步骤验证)
  - **快速冒烟测试**:
    - `workflows/at/naohai_01_story_list_smoke.yaml` (剧本列表冒烟)
    - `workflows/at/naohai_02_create_story_smoke.yaml` (剧本创建冒烟)
    - `workflows/at/naohai_03_storyboard_smoke.yaml` (分镜管理冒烟)
    - `workflows/at/naohai_05_create_story_to_video_e2e.yaml` (端到端冒烟)
  - **端到端集成**:
    - `workflows/e2e/naohai_E2E_GoldenPath.yaml` (完整流程冒烟验证)
- **Robot Tags**: `@smoke`, `@health`, `@critical`, `@access`
- **Command**: 
  ```bash
  # 快速冒烟检查 (5分钟)
  python src/main_workflow.py --spec NH-SMOKE-001 --mode quick
  
  # 完整冒烟验证 (10分钟)
  python src/main_workflow.py --spec NH-SMOKE-001 --mode full
  
  # 系统健康检查 (3分钟)
  python src/main_workflow.py --spec NH-SMOKE-001 --mode health
  ```

### 详细 Workflow 映射
| 测试场景 | Workflow文件 | 关键Steps | 验证点 |
|---------|-------------|-----------|--------|
| 导航验证 | naohai_FC_NH_051_rf.yaml | open_site | 导航项展示、页面加载 |
| 创作页面 | naohai_FC_NH_052_rf.yaml | precondition | AI创作访问、剧本列表展示 |
| UI组件检查 | naohai_FC_NH_053-060_rf.yaml | 各组件验证 | 输入框、按钮、上传组件等 |
| 快速冒烟 | naohai_01-03_smoke.yaml | 核心功能 | 剧本列表、创建、分镜访问 |
| 端到端冒烟 | naohai_05_e2e.yaml | 完整流程 | 创建到视频的快速验证 |

### 冒烟测试层级
- **Level 1 - Health Check**: 系统健康和认证状态
- **Level 2 - Access Check**: 关键页面和组件可访问性
- **Level 3 - Function Check**: 基础功能操作验证
- **Level 4 - Integration Check**: 端到端流程可用性

### 执行模式说明
- **Quick模式**: 执行Level 1-2检查，快速判断系统基本可用性
- **Full模式**: 执行Level 1-3检查，验证核心功能完整性
- **Health模式**: 仅执行Level 1检查，专注系统健康状态

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-SMOKE-001-run.md`
- **Required Content**:
  - Execution Command & Commit SHA
  - Smoke Test Summary (各模式执行结果)
  - System Health Check Results (系统健康状态)
  - UI Component Verification Screenshots (UI组件验证截图)
  - Critical Function Test Results (关键功能测试结果)
  - Performance Metrics (响应时间统计)
  - Error Logs (如有失败的详细信息)
  - Standard Output/Error Logs
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-21: 标准化更新 - 对齐NH-CREATE-001格式，细化冒烟测试功能映射
- 2025-12-20: 架构重构 - 从Gate结构改为Tree-based Architecture，支持多模式执行
- 2025-03-08: 初版 - 基于闹海AT冒烟测试设计