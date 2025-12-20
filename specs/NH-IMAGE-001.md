# Spec: NH-IMAGE-001 闹海融图生成素材

## 🎯 Purpose
验证闹海创作核心环节（融图生成素材）的质量和效率，确保角色、场景与提示词的有效融合生成高质量图片素材。

## 🔭 Scope
- **适用**：角色场景融合生图、图片素材管理
- **包含**：
  1. 融图生成图片素材（步骤5）
- **不适用**：分镜编辑、视频制作环节

## 🔌 Preconditions & Gates
- **Preconditions**:
  - 分镜分析与资源绑定已完成 (NH-SCRIPT-001 Passed)。
  - 融图生成服务可用，GPU 资源充足。
- **Gates**:
  1. **Gate-Env**: 生图服务健康，素材库访问正常。
  2. **Gate-Run**: 成功触发融合任务并返回结果。
  3. **Gate-Quality**: 图片分辨率符合标准 (e.g., ≥512x512)。

## ✅ Acceptance Criteria
- **融合成功率**: ≥ 95%。
- **素材管理**: 候选图片生成正常 (2-8张)，最佳选择功能可用。
- **性能指标**: 单张生成耗时 ≤ 30秒。
- **质量标准**: 图片无明显崩坏，符合提示词描述。

## 🗺️ Mapping
- **Workflows**:
  - `workflows/fc/naohai_FC_NH_021.yaml` (简单融合)
  - `workflows/fc/naohai_FC_NH_022.yaml` (多角色融合)
  - `workflows/fc/naohai_FC_NH_024.yaml` (多候选生成)
- **Robot Tags**: `@image`, `@fusion`, `@generation`
- **Command**: `python src/main_workflow.py --spec NH-IMAGE-001`

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-IMAGE-001-run.md`
- **Required Content**:
  - Sample Generated Images (Thumbnails or Paths)
  - Generation Parameters (Prompt, Seed)
  - Failure Logs (for crashed tasks)
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-20: 标准化 - 对齐 GitHub Issue Template 格式。
- 2025-03-08: 初版 - 基于闹海关键流程文档设计。
