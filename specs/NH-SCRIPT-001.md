# Spec: NH-SCRIPT-001 闹海分镜分析与编辑

## 🎯 Purpose
验证闹海创作流程核心环节（分镜分析与编辑）的准确性和可用性，确保剧本能够有效转化为可执行的拍摄脚本。

## 🔭 Scope
- **适用**：剧本到分镜的转化流程、资源绑定验证
- **包含**：
  1. 分集内容分析制作（步骤3）
  2. 分镜资源绑定（步骤4）
- **不适用**：剧本创建、图像生成、视频制作环节

## 🔌 Preconditions & Gates
- **Preconditions**:
  - 剧本基础信息已创建 (NH-CREATE-001 Passed)。
  - 角色/场景资产库已准备就绪。
  - AI分析服务可用。
- **Gates**:
  1. **Gate-Env**: AI分析服务响应正常，分镜编辑器加载成功。
  2. **Gate-Run**: 成功执行分析并生成分镜列表。
  3. **Gate-Binding**: 资源绑定无冲突。

## ✅ Acceptance Criteria
- **AI分析准确性**: 建议分镜数量合理，结构逻辑清晰。
- **编辑功能正常**: 支持增删改查分镜，撤销重做功能正常。
- **资源绑定准确**: 角色/场景绑定准确率 ≥ 98%，无重复/冲突。
- **提示词生成**: 每个分镜均生成有效的 Prompt。

## 🗺️ Mapping
- **Workflows**:
  - `workflows/fc/naohai_FC_NH_011.yaml` (AI分析)
  - `workflows/fc/naohai_FC_NH_012.yaml` (分镜编辑)
  - `workflows/fc/naohai_FC_NH_013.yaml` (资源绑定)
  - `workflows/fc/naohai_FC_NH_014.yaml` (提示词生成)
- **Robot Tags**: `@script`, `@analysis`, `@binding`
- **Command**: `python src/main_workflow.py --spec NH-SCRIPT-001`

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-SCRIPT-001-run.md`
- **Required Content**:
  - AI Analysis Summary (Accuracy/Quality)
  - Binding Conflict Logs (if any)
  - Storyboard Export JSON
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-20: 标准化 - 对齐 GitHub Issue Template 格式。
- 2025-03-08: 初版 - 基于闹海关键流程文档设计。
