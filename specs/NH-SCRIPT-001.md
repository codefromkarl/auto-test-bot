# Spec: NH-SCRIPT-001 闹海分镜分析与编辑
Issue: #9

## 🎯 Purpose
验证闹海创作流程核心环节（分镜分析与编辑）的准确性和可用性，确保剧本能够有效转化为可执行的拍摄脚本。

## 🔭 Scope
- **适用**：剧本到分镜的转化流程、AI智能分析、资源绑定验证
- **包含**：
  1. 剧本AI分析和分镜生成（步骤3）
  2. 分镜增删改查编辑操作
  3. 分镜资源绑定（角色+场景，步骤4）
  4. 提示词生成和编辑
  5. 参考图上传和管理
- **不适用**：剧本创建（由NH-CREATE-001覆盖）、图像生成、视频制作环节

## 🔌 Preconditions & Gates
- **Env**: AI创作服务可用（Port 9020），用户已登录且Token有效
- **Precondition**: 剧本基础信息已创建（NH-CREATE-001 Passed），角色/场景资产库已准备就绪
- **Config**: 使用`config/main_config_with_testid.yaml`或对应环境配置
- **Service**: AI分析服务可用，分镜编辑器功能正常

**Gates**:
1. **Gate-Env**: AI分析服务健康检查，分镜编辑器加载成功
2. **Gate-Run**: 成功执行分析并生成分镜列表，无阻塞错误
3. **Gate-Analysis**: AI分析结果准确，分镜结构逻辑清晰
4. **Gate-Binding**: 资源绑定无冲突，角色/场景关联正确
5. **Gate-Data**: 分镜数据正确保存，提示词生成完整

## ✅ Acceptance Criteria
- **AI分析准确性**: 建议分镜数量合理（符合剧本长度），结构逻辑清晰
- **编辑功能正常**: 支持增删改查分镜，撤销重做功能正常
- **资源绑定准确**: 角色/场景绑定准确率 ≥ 98%，无重复/冲突
- **提示词生成**: 每个分镜均生成有效的Prompt，支持编辑优化
- **性能指标**: AI分析耗时 ≤ 2分钟，分镜编辑响应 ≤ 1秒
- **产物完整**: 必须生成`report.html`和`logs.txt`，包含分析摘要

## 🗺️ Mapping
- **Workflows**:
  - **分镜编辑基础**:
    - `workflows/fc/naohai_FC_NH_026_rf.yaml` (新增分镜)
    - `workflows/fc/naohai_FC_NH_027_rf.yaml` (编辑分镜入口)
    - `workflows/fc/naohai_FC_NH_028_rf.yaml` (编辑提示词入口)
    - `workflows/fc/naohai_FC_NH_029_rf.yaml` (分镜删除入口)
  - **剧本与AI分析**:
    - `workflows/fc/naohai_FC_NH_030_rf.yaml` (剧本输入)
    - `workflows/fc/naohai_FC_NH_031_rf.yaml` (分析参数：目标时长)
    - `workflows/fc/naohai_FC_NH_032_rf.yaml` (建议分镜数量)
    - `workflows/fc/naohai_FC_NH_033_rf.yaml` (开始分析按钮)
    - `workflows/fc/naohai_FC_NH_034_rf.yaml` (分析产出结果)
  - **提示词与资源绑定**:
    - `workflows/fc/naohai_FC_NH_035_rf.yaml` (提示词生成)
    - `workflows/fc/naohai_FC_NH_036_rf.yaml` (提示词展示与编辑)
    - `workflows/fc/naohai_FC_NH_037_rf.yaml` (绑定多个角色)
    - `workflows/fc/naohai_FC_NH_038_rf.yaml` (绑定1个场景)
    - `workflows/fc/naohai_FC_NH_039_rf.yaml` (上传参考图)
  - **端到端集成**:
    - `workflows/e2e/naohai_E2E_GoldenPath.yaml` (Phase 3: analyze_and_create_storyboard)
    - `workflows/e2e/naohai_E2E_GoldenPath.yaml` (Phase 4: bind_storyboard_assets)
- **Robot Tags**: `@script`, `@analysis`, `@binding`, `@storyboard`
- **Command**: `python src/main_workflow.py --spec NH-SCRIPT-001`

### 详细 Workflow 映射
| 测试场景 | Workflow文件 | 关键Steps | 验证点 |
|---------|-------------|-----------|--------|
| 剧本输入 | naohai_FC_NH_030_rf.yaml | script_input | 剧本文本输入、文件导入功能 |
| 分析参数 | naohai_FC_NH_031_rf.yaml | target_duration | 目标时长设置、建议分镜数量 |
| AI分析 | naohai_FC_NH_033_rf.yaml | start_analysis | 分析触发、加载状态、结果等待 |
| 分析结果 | naohai_FC_NH_034_rf.yaml | analysis_result | 分析产出、角色场景提取、导入分镜 |
| 分镜管理 | naohai_FC_NH_026_rf.yaml | add_storyboard_entry | 新增分镜、表单填写、保存验证 |
| 提示词生成 | naohai_FC_NH_035_rf.yaml | prompt_generation | 提示词生成、列表展示、内容验证 |
| 资源绑定 | naohai_FC_NH_037_rf.yaml | bind_multiple_characters | 多角色绑定、选择确认 |
| 场景绑定 | naohai_FC_NH_038_rf.yaml | bind_single_scene | 场景绑定、关联验证 |

### AI分析参数配置
- **目标时长**: 1分钟/3分钟/5分钟/10分钟/30分钟
- **建议分镜数**: 基于时长自动计算，支持手动调整
- **分析深度**: 简单分析/详细分析/深度分析
- **角色提取**: 自动识别主要角色和配角
- **场景提取**: 自动识别场景变化和地点转换

### 分镜编辑功能
- **基础操作**: 新增、编辑、删除、复制、重排序
- **内容字段**: 分镜标题、描述、时长、角色、场景、提示词
- **高级功能**: 批量编辑、模板应用、撤销重做
- **导入导出**: 支持JSON/CSV格式，与外部工具集成

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-SCRIPT-001-run.md`
- **Required Content**:
  - Execution Command & Commit SHA
  - AI Analysis Summary (分析准确性/质量评估)
  - Storyboard Export JSON (分镜数据导出)
  - Binding Conflict Logs (绑定冲突记录，如有)
  - Performance Metrics (分析耗时、编辑响应时间)
  - Generated Prompts Examples (生成的提示词样例)
  - Resource Binding Verification (资源绑定验证结果)
  - Standard Output/Error Logs
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-21: 标准化更新 - 对齐NH-CREATE-001格式，细化分镜分析功能映射
- 2025-12-20: 格式标准化 - 对齐GitHub Issue Template格式
- 2025-03-08: 初版 - 基于闹海关键流程文档设计
