# Spec: NH-CREATE-001 闹海剧本创建与资源准备

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
  - `workflows/fc/naohai_FC_NH_001.yaml` (空白剧本)
  - `workflows/fc/naohai_FC_NH_002.yaml` (剧本复制)
  - `workflows/fc/naohai_FC_NH_005.yaml` (角色生成)
  - `workflows/fc/naohai_FC_NH_008.yaml` (场景生成)
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
