# Spec: NH-VIDEO-001 闹海图生视频制作

## 🎯 Purpose
验证闹海创作核心环节（图生视频制作）的功能完整性和视频质量，确保图片素材能够有效转化为动态视频片段。

## 🔭 Scope
- **适用**：图生视频、首尾帧视频制作
- **包含**：
  1. 图生视频制作（步骤6）
- **不适用**：图片生成、导出环节

## 🔌 Preconditions & Gates
- **Preconditions**:
  - 图片素材已就绪 (NH-IMAGE-001 Passed)。
  - 视频生成服务可用，GPU 显存充足 (≥6GB)。
- **Gates**:
  1. **Gate-Env**: 视频服务响应正常，模型加载成功。
  2. **Gate-Run**: 视频生成任务提交成功且完成。
  3. **Gate-Quality**: 视频可播放，无花屏。

## ✅ Acceptance Criteria
- **生成成功率**: ≥ 95%。
- **模式覆盖**: 图生视频 / 首尾帧视频均功能正常。
- **性能指标**: 720P生成 ≤ 2分钟/片段。
- **质量标准**: 视频流畅，清晰度符合分辨率设定。

## 🗺️ Mapping
- **Workflows**:
  - `workflows/fc/naohai_FC_NH_031.yaml` (基础图生视频)
  - `workflows/fc/naohai_FC_NH_034.yaml` (首尾帧视频)
  - `workflows/fc/naohai_FC_NH_035.yaml` (多片段管理)
- **Robot Tags**: `@video`, `@img2vid`, `@generation`
- **Command**: `python src/main_workflow.py --spec NH-VIDEO-001`

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-VIDEO-001-run.md`
- **Required Content**:
  - Video Segment Previews/Paths
  - Performance Metrics (Time per segment)
  - Model Configurations Used
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-20: 标准化 - 对齐 GitHub Issue Template 格式。
- 2025-03-08: 初版 - 基于闹海关键流程文档设计。
