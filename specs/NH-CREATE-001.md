# Spec: NH-CREATE-001 闹海剧本创建与资源准备
Issue: #8

## 🎯 Purpose
验证闹海创作起点（剧本创建与资源准备）的完整性和质量，确保用户能够成功开始创作流程。

## 🔭 Scope
- **适用**：新剧本创建流程验证、资源资产准备测试（角色/场景）
- **包含**：
  1. 新建剧本与大纲（步骤1）
  2. 建立分集、角色、场景资产（步骤2）
- **不适用**：分镜编辑、图像生成、视频制作环节

## 🔌 Preconditions & Gates
- **Env**: AI创作服务可用 (Port 9020)，用户已登录且 Token 有效。
- **Account**: 用户具备剧本创建权限。
- **Storage**: 存储空间充足 (≥1GB)。
- **Config**: 使用 `config/main_config_with_testid.yaml` 或对应环境配置。

**Gates**:
1. **Gate-Env**: 服务健康检查 (Health Check passed).
2. **Gate-Run**: 执行创建脚本，无阻塞性错误。
3. **Gate-Data**: 资产数据正确写入数据库/文件系统。

## ✅ Acceptance Criteria
- **剧本信息完整**: 名称、大纲、画幅、风格、封面均正确保存。
- **资产生成成功**: 角色/场景资产生成成功率 ≥ 95%。
- **性能达标**: 剧本创建耗时 ≤ 2分钟，单资产生成 ≤ 30秒。
- **产物完整**: 必须生成 `report.html` 和 `logs.txt`。

## 🗺️ Mapping
- **Workflows**:
  - `<!-- workflows/fc/naohai_FC_NH_001.yaml (MISSING) -->` (空白剧本)
  - **剧本基础管理**:
    - `workflows/fc/naohai_FC_NH_002_rf.yaml` (剧本卡片展示)
    - `workflows/fc/naohai_FC_NH_003_rf.yaml` (剧本卡片菜单)
    - `workflows/fc/naohai_FC_NH_004_rf.yaml` (打开新建弹窗)
    - `workflows/fc/naohai_FC_NH_005_rf.yaml` (填写剧本名称)
    - `workflows/fc/naohai_FC_NH_006_rf.yaml` (编写说明/大纲)
    - `workflows/fc/naohai_FC_NH_007_rf.yaml` (上传封面)
    - `workflows/fc/naohai_FC_NH_008_rf.yaml` (选择画幅)
    - `workflows/fc/naohai_FC_NH_009_rf.yaml` (进入画风预览)
    - `workflows/fc/naohai_FC_NH_010_rf.yaml` (选择画风)
    - `workflows/fc/naohai_FC_NH_011_rf.yaml` (预览效果区)
    - `workflows/fc/naohai_FC_NH_012_rf.yaml` (完整创建剧本)
  - **分集管理**:
    - `workflows/fc/naohai_FC_NH_013_rf.yaml` (新增分集入口)
    - `workflows/fc/naohai_FC_NH_014_rf.yaml` (新增分集字段)
    - `workflows/fc/naohai_FC_NH_015_rf.yaml` (新增分集提交)
    - `workflows/fc/naohai_FC_NH_016_rf.yaml` (分集卡片菜单)
    - `workflows/fc/naohai_FC_NH_017_rf.yaml` (分集统计弹窗)
  - **资产管理 (角色/场景)**:
    - `workflows/fc/naohai_FC_NH_018_rf.yaml` (角色创建方式)
    - `workflows/fc/naohai_FC_NH_019_rf.yaml` (角色模型选择)
    - `workflows/fc/naohai_FC_NH_020_rf.yaml` (角色卡片展示)
    - `workflows/fc/naohai_FC_NH_021_rf.yaml` (删除角色)
    - `workflows/fc/naohai_FC_NH_022_rf.yaml` (场景创建方式)
    - `workflows/fc/naohai_FC_NH_023_rf.yaml` (场景模型选择)
    - `workflows/fc/naohai_FC_NH_024_rf.yaml` (场景卡片展示)
    - `workflows/fc/naohai_FC_NH_025_rf.yaml` (删除场景)
  - **只读验证 (Smoke/UI)**:
    - `workflows/fc/naohai_FC_NH_051_rf.yaml` (导航项展示)
    - `workflows/fc/naohai_FC_NH_052_rf.yaml` (AI创作只读)
    - `workflows/fc/naohai_FC_NH_053_rf.yaml` (Tab项存在)
    - `workflows/fc/naohai_FC_NH_054_rf.yaml` (新增按钮存在)
    - `workflows/fc/naohai_FC_NH_055_rf.yaml` (创建弹窗只读)
    - `workflows/fc/naohai_FC_NH_056_rf.yaml` (输入框存在)
    - `workflows/fc/naohai_FC_NH_057_rf.yaml` (上传组件存在)
    - `workflows/fc/naohai_FC_NH_058_rf.yaml` (比例选项存在)
    - `workflows/fc/naohai_FC_NH_059_rf.yaml` (下一步按钮存在)
    - `workflows/fc/naohai_FC_NH_060_rf.yaml` (默认步骤验证)
- **Robot Tags**: `@create`, `@assets`, `@smoke`
- **Command**: `python src/main_workflow.py --spec NH-CREATE-001`

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-CREATE-001-run.md`
- **Required Content**:
  - Execution Command & Commit SHA
  - Asset Quality Screenshots (for failed generations)
  - Standard Output/Error Logs
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-20: 标准化 - 对齐 GitHub Issue Template 格式。
- 2025-03-08: 初版 - 基于闹海关键流程文档设计。
