# Spec: NH-EXPORT-001 闹海视频导出二创
Issue: #13

## 🎯 Purpose
验证闹海创作最终环节（视频导出和剪映二创）的完整性和兼容性，确保创作成果能够有效导出并进行二次创作。

## 🔭 Scope
- **适用**：视频素材下载、项目导出、二创集成
- **包含**：
  1. 导出资源包配置和执行
  2. 下载链接生成和验证
  3. 文件格式兼容性测试
  4. 剪映二创集成验证
- **不适用**：视频生成环节（由NH-VIDEO-001覆盖）

## 🔌 Preconditions & Gates
- **Env**: AI创作服务可用（Port 9020），用户已登录且Token有效
- **Precondition**: 视频片段生成完成（NH-VIDEO-001 Passed），导出/下载服务可用
- **Config**: 使用`config/main_config_with_testid.yaml`或对应环境配置
- **Storage**: 存储空间充足（≥2GB）

**Gates**:
1. **Gate-Env**: 导出服务健康检查，存储空间充足
2. **Gate-Run**: 下载/导出请求成功响应，无阻塞错误
3. **Gate-Format**: 文件格式正确（MP4/MOV/ZIP），可正常播放
4. **Gate-Data**: 导出文件完整性验证，二创兼容性确认

## ✅ Acceptance Criteria
- **导出成功率**: 批量下载/项目导出成功率 ≥ 95%
- **文件完整性**: 下载文件完整可播放，无损坏，校验和正确
- **二创兼容性**: 剪映集成/导入功能正常，资源包结构标准
- **性能指标**: 单视频下载耗时 ≤ 2分钟，批量导出 ≤ 10分钟
- **产物完整**: 必须生成`report.html`和`logs.txt`，包含下载速度统计

## 🗺️ Mapping
- **Workflows**:
  - **导出功能测试**:
    - `workflows/fc/naohai_FC_NH_050_rf.yaml` (导出资源包RF版本)
    - `workflows/fc/naohai_FC_NH_050.yaml` (导出资源包原版)
  - **端到端集成**:
    - `workflows/e2e/naohai_E2E_GoldenPath.yaml` (Phase 7: export_final_video)
- **Robot Tags**: `@export`, `@download`, `@integration`, `@e2e`
- **Command**: `python src/main_workflow.py --spec NH-EXPORT-001`

### 详细 Workflow 映射
| 测试场景 | Workflow文件 | 关键Steps | 验证点 |
|---------|-------------|-----------|--------|
| 资源包导出 | naohai_FC_NH_050_rf.yaml | rf_export_resource_package | 导出操作触发、完成消息显示 |
| 导出配置验证 | naohai_FC_NH_050.yaml | resource_export | 导出选项、进度跟踪、完成状态 |
| 端到端导出 | naohai_E2E_GoldenPath.yaml | export_final_video | 完整流程导出、下载入口验证 |

### 导出格式支持
- **视频格式**: MP4, MOV, AVI
- **项目格式**: 剪映工程文件（.draft）、ZIP资源包
- **字幕格式**: SRT, ASS
- **素材格式**: PNG, JPG, MP3

## 🧾 Evidence Policy
- **Runs Directory**: `runs/YYYY-MM-DD/`
- **File Naming**: `NH-EXPORT-001-run.md`
- **Required Content**:
  - Execution Command & Commit SHA
  - Download Speed Statistics (下载速度统计)
  - Exported File Checksums (文件完整性校验)
  - Export Format Verification Results (格式验证结果)
  - Integration Test Results (剪映兼容性测试)
  - Export Progress Screenshots (导出过程截图)
  - Standard Output/Error Logs
  - Link to HTML Report

## 📝 ChangeLog
- 2025-12-21: 标准化更新 - 对齐NH-CREATE-001格式，细化导出功能映射
- 2025-12-20: 格式标准化 - 对齐GitHub Issue Template格式
- 2025-03-08: 初版 - 基于闹海关键流程文档设计
