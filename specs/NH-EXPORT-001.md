# Spec: NH-EXPORT-001 闹海视频导出二创

## 🎯 Purpose
验证闹海创作最终环节（视频导出和剪映二创）的完整性和兼容性，确保创作成果能够有效导出并进行二次创作。

## 🔭 Scope
- **适用**：视频素材下载、项目导出、二创集成
- **包含**：
  1. 视频导出二创（步骤7）
- **不适用**：视频生成环节

## 🔌 Preconditions & Gates
- **Preconditions**:
  - 视频片段生成完成 (NH-VIDEO-001 Passed)。
  - 导出/下载服务可用。
- **Gates**:
  1. **Gate-Env**: 导出服务健康，存储空间充足。
  2. **Gate-Run**: 下载/导出请求成功响应。
  3. **Gate-Format**: 文件格式正确 (MP4/MOV/ZIP)。

## ✅ Acceptance Criteria
- **导出成功率**: 批量下载/项目导出 ≥ 95%。
- **文件完整性**: 下载文件完整可播放，无损坏。
- **二创兼容性**: 剪映集成/导入功能正常。
- **性能指标**: 单视频下载 ≤ 2分钟。

## 🗺️ Mapping
- **Workflows**:
  - `workflows/fc/naohai_FC_NH_041.yaml` (批量下载)
  - `workflows/fc/naohai_FC_NH_042.yaml` (项目导出)
  - `workflows/fc/naohai_FC_NH_043.yaml` (剪映集成)
- **Robot Tags**: `@export`, `@download`, `@integration`
- **Command**: `python src/main_workflow.py --spec NH-EXPORT-001`

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-EXPORT-001-run.md`
- **Required Content**:
  - Download Speed Statistics
  - Exported File Checksums (Integrity)
  - Integration Test Results
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-20: 标准化 - 对齐 GitHub Issue Template 格式。
- 2025-03-08: 初版 - 基于闹海关键流程文档设计。
