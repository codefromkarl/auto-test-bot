# Spec: NH-VIDEO-001 闹海图生视频制作
Issue: #11

## 🎯 Purpose
验证闹海创作核心环节（图生视频制作）的功能完整性和视频质量，确保图片素材能够有效转化为动态视频片段。

## 🔭 Scope
- **适用**：图生视频、首尾帧视频制作、视频片段选择和管理
- **包含**：
  1. 从分镜进入视频创作页面（步骤6）
  2. 视频制作模式选择（图生视频/首尾帧视频）
  3. 视频参数配置（模型、分辨率、数量等）
  4. 视频生成和预览
  5. 视频片段选择和保存
- **不适用**：图片生成（由NH-IMAGE-001覆盖）、导出环节

## 🔌 Preconditions & Gates
- **Env**: AI创作服务可用（Port 9020），用户已登录且Token有效
- **Precondition**: 图片素材已就绪（NH-IMAGE-001 Passed），视频生成服务可用
- **Config**: 使用`config/main_config_with_testid.yaml`或对应环境配置
- **Resource**: GPU显存充足（≥6GB），视频模型文件加载完成

**Gates**:
1. **Gate-Env**: 视频服务健康检查，模型加载成功
2. **Gate-Run**: 视频生成任务提交成功且完成，无阻塞错误
3. **Gate-Quality**: 视频可正常播放，无花屏、卡顿、音画不同步
4. **Gate-Data**: 视频参数正确保存，片段选择功能正常

## ✅ Acceptance Criteria
- **生成成功率**: 视频生成成功率 ≥ 95%
- **模式覆盖**: 图生视频/首尾帧视频两种模式功能正常
- **性能指标**: 720P生成 ≤ 2分钟/片段，1080P生成 ≤ 5分钟/片段
- **质量标准**: 视频流畅，清晰度符合分辨率设定，无明显噪点或扭曲
- **片段管理**: 支持多片段生成、预览、选择、保存等完整流程
- **产物完整**: 必须生成`report.html`和`logs.txt`，包含生成样例

## 🗺️ Mapping
- **Workflows**:
  - **视频创作入口**:
    - `workflows/fc/naohai_FC_NH_042_rf.yaml` (进入视频创作页)
  - **制作模式配置**:
    - `workflows/fc/naohai_FC_NH_043_rf.yaml` (选择制作模式)
    - `workflows/fc/naohai_FC_NH_044_rf.yaml` (视频模型选择)
    - `workflows/fc/naohai_FC_NH_047_rf.yaml` (视频分辨率选择)
    - `workflows/fc/naohai_FC_NH_048_rf.yaml` (生成数量选择)
  - **视频信息设置**:
    - `workflows/fc/naohai_FC_NH_045_rf.yaml` (视频名称设置)
    - `workflows/fc/naohai_FC_NH_046_rf.yaml` (视频描述设置)
  - **片段管理**:
    - `workflows/fc/naohai_FC_NH_049_rf.yaml` (选择视频片段)
  - **端到端集成**:
    - `workflows/e2e/naohai_E2E_GoldenPath.yaml` (Phase 6: generate_video_segments)
- **Robot Tags**: `@video`, `@img2vid`, `@generation`, `@production`
- **Command**: `python src/main_workflow.py --spec NH-VIDEO-001`

### 详细 Workflow 映射
| 测试场景 | Workflow文件 | 关键Steps | 验证点 |
|---------|-------------|-----------|--------|
| 进入创作页 | naohai_FC_NH_042_rf.yaml | enter_video_creation | 分镜上下文、视频创作页面加载 |
| 模式选择 | naohai_FC_NH_043_rf.yaml | production_mode | 图生视频/首尾帧切换、界面验证 |
| 模型选择 | naohai_FC_NH_044_rf.yaml | video_model_selection | 模型列表、选择确认、参数显示 |
| 参数配置 | naohai_FC_NH_047_rf.yaml | resolution_selection | 分辨率选项、质量设置、时长配置 |
| 数量设置 | naohai_FC_NH_048_rf.yaml | generation_quantity | 生成数量、批量配置、预估时间 |
| 片段选择 | naohai_FC_NH_049_rf.yaml | video_selection | 片段预览、选择操作、保存确认 |

### 视频生成参数配置
- **制作模式**:
  - 图生视频：单张图片生成动态视频
  - 首尾帧视频：两张图片间插帧过渡
- **视频模型**: 支持多种预训练模型，适配不同风格
- **分辨率选择**: 480P/720P/1080P/4K（可选）
- **生成数量**: 1/2/4/8个片段可选
- **视频时长**: 3秒/5秒/10秒/15秒可配置
- **运动强度**: 轻微/适中/强烈三档调节

### 视频质量标准
- **清晰度**: 符合设定分辨率，边缘清晰无模糊
- **流畅度**: 帧率稳定（≥24fps），无卡顿跳跃
- **色彩还原**: 保持原图色彩风格，无严重偏色
- **运动自然**: 动作过渡自然，无异常扭曲
- **无噪点**: 画面干净，无明显噪声或伪影

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-VIDEO-001-run.md`
- **Required Content**:
  - Execution Command & Commit SHA
  - Video Segment Previews/Paths (生成的视频片段预览或路径)
  - Performance Metrics (各片段生成耗时统计)
  - Model Configurations Used (使用的模型配置参数)
  - Quality Assessment Results (视频质量评估结果)
  - Generation Mode Test Results (不同模式测试结果)
  - Video Selection Screenshots (视频选择界面截图)
  - Standard Output/Error Logs
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-21: 标准化更新 - 对齐NH-CREATE-001格式，细化视频制作功能映射
- 2025-12-20: 格式标准化 - 对齐GitHub Issue Template格式
- 2025-03-08: 初版 - 基于闹海关键流程文档设计
