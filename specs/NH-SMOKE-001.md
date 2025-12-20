# Spec: NH-SMOKE-001 闹海核心功能冒烟测试

## Purpose
快速验证闹海系统核心功能的可用性和稳定性，确保系统基本功能正常，为后续详细测试提供基础保障。

## Scope
- 适用：日常系统健康检查、快速功能验证、发布前快速验证
- 不适用：详细功能测试、性能压力测试、端到端流程测试

## Preconditions
- 所有核心服务可用（创作、分析、生成、导出）
- 测试账号和权限正常
- 基础测试数据准备完成
- 冒烟测试环境干净且稳定

## Procedure (Gates)

### 1) Gate-Env: 冒烟环境就绪检查
**目的**: 确保冒烟测试环境纯净和稳定

**检查项**:
- ✅ 核心服务基础状态检查
- ✅ 测试环境清理（避免缓存干扰）
- ✅ 基础功能入口可用性
- ✅ 测试账号登录和权限
- ✅ 基础存储和计算资源

**成功标准**:
- 所有核心服务响应正常
- 测试环境无历史残留
- 功能入口页面可访问
- 测试账号权限正常
- 基础资源充足

---

### 2) Gate-Scope: 冒烟范围选择
**目的**: 选择轻量级、高价值的核心功能测试

**核心功能选择**:
| 功能模块 | 测试重点 | 预计耗时 | 优先级 |
|---------|----------|------------|---------|
| 剧本列表 | 页面加载、数据展示 | 1-2分钟 | P0 |
| 剧本创建 | 基础创建流程 | 1-2分钟 | P0 |
| 分镜编辑 | 基础编辑操作 | 2-3分钟 | P1 |
| 图像生成 | 简单生图功能 | 2-3分钟 | P1 |
| 视频导出 | 基础导出操作 | 1-2分钟 | P0 |

**测试深度控制**:
| 测试类型 | 覆盖深度 | 测试方式 |
|---------|----------|----------|
| 基础冒烟 | 核心路径验证 | 快速点击操作 |
| 功能冒烟 | 基本功能验证 | 简单数据创建 |
| 健康冒烟 | 系统状态检查 | 自动化检测 |

---

### 3) Gate-Run: 执行核心功能冒烟测试
**目的**: 快速执行核心功能验证，收集基础可用性数据

**剧本列表测试执行**:
- **页面加载验证**: 访问剧本列表页面
- **数据展示检查**: 验证剧本信息正确展示
- **基础操作测试**: 选择、搜索、排序功能
- **响应时间检查**: 页面加载和操作响应时间

**剧本创建测试执行**:
- **创建入口验证**: 进入剧本创建流程
- **基础信息填写**: 测试名称、画幅、风格设置
- **保存功能验证**: 测试剧本保存和编辑功能
- **权限检查**: 验证创建权限和保存权限

**分镜编辑测试执行**:
- **编辑器加载**: 验证分镜编辑器可用
- **基础编辑操作**: 测试添加、删除、修改分镜
- **资源绑定**: 测试角色和场景的绑定功能
- **提示词编辑**: 验证提示词编辑和保存功能

**图像生成测试执行**:
- **生图功能入口**: 验证图像生成功能可访问
- **基础参数设置**: 测试分辨率、风格等基础参数
- **简单生成测试**: 执行基础图像生成操作
- **结果查看**: 验证生成结果展示和保存

**视频导出测试执行**:
- **导出功能入口**: 验证视频导出功能可用
- **基础导出操作**: 测试简单视频的导出流程
- **格式检查**: 验证导出文件格式正确
- **下载功能**: 测试导出文件的下载操作

**快速监控**:
- 操作成功率实时统计
- 响应时间持续监测
- 错误日志自动记录
- 系统资源使用监控
- 功能可用性状态更新

---

### 4) Gate-Report: 生成冒烟测试质量报告
**目的**: 快速生成核心功能状态评估报告

**报告组件**:
```python
SmokeResult:
├─ core_modules: Dict (核心模块状态)
├─ health_metrics: Dict (健康指标)
├─ performance_snapshot: Dict (性能快照)
├─ error_summary: Dict (错误汇总)
├─ availability_score: float (可用性评分)
└─ basic_functionality: Dict (基础功能验证)
```

**输出产物**:
- ✅ `smoke_report.html` - 冒烟测试可视化报告
- ✅ `smoke_logs.txt` - 简化执行日志
- ✅ `health_status.json` - 系统健康状态数据
- ✅ `core_functionality.csv` - 核心功能验证表
- ✅ `quick_screenshots/` - 关键操作截图

**报告内容**:
- 核心功能可用性汇总
- 系统健康状态评估
- 响应时间对比分析
- 错误和异常汇总
- 冒烟测试通过率
- 系统就绪状态判定

---

### 5) Gate-Judge: 判定冒烟测试结果
**目的**: 基于快速验证标准判定系统基本可用性

**判定标准**:

**核心功能可用性**:
- 剧本列表功能正常 = 100% ✅
- 剧本创建功能正常 ≥ 90% ✅
- 分镜编辑功能正常 ≥ 90% ✅
- 图像生成功能正常 ≥ 90% ✅
- 视频导出功能正常 ≥ 90% ✅

**系统健康指标**:
- 页面响应时间 < 5秒 ✅
- 功能加载成功率 = 100% ✅
- 基础操作成功率 ≥ 95% ✅
- 系统错误率 ≤ 5% ✅

**测试执行质量**:
- 冒烟测试完成时间 ≤ 10分钟 ✅
- 核心功能覆盖率 = 100% ✅
- 测试数据清理效果良好 ✅
- 监控数据完整性 ≥ 98% ✅

**系统就绪评估**:
- 无阻塞性错误 ✅
- 核心服务健康度 ≥ 4.5/5.0 ✅
- 性能基线达标率 ≥ 90% ✅
- 用户体验基础评分 ≥ 4.0/5.0 ✅

**结果判定**:
- **PASS**: 核心功能正常，系统健康，可继续详细测试
- **WARN**: 部分核心功能异常，功能可用但需关注
- **FAIL**: 核心功能严重异常或系统不稳定，需要立即修复

## Acceptance Criteria
- 必须产物：smoke_report.html / smoke_logs.txt / health_status.json
- Pass：核心功能正常率≥90% + 系统健康度≥4.5/5.0 + 测试时间≤10分钟
- Fail：核心功能正常率<80% 或 系统出现阻塞性错误 或 测试严重超时

## Mapping

### Workflow 文件映射
| 测试场景 | 对应 Workflow 文件 | 执行命令 |
|---------|-------------------|----------|
| 剧本列表冒烟 | `workflows/at/naohai_01_story_list_smoke.yaml` | `python src/main_workflow.py --workflow workflows/at/naohai_01_story_list_smoke.yaml --spec NH-SMOKE-001` |
| 剧本创建冒烟 | `workflows/at/naohai_02_create_story_smoke.yaml` | `python src/main_workflow.py --workflow workflows/at/naohai_02_create_story_smoke.yaml --spec NH-SMOKE-001` |
| 分镜编辑冒烟 | `workflows/at/naohai_03_storyboard_smoke.yaml` | `python src/main_workflow.py --workflow workflows/at/naohai_03_storyboard_smoke.yaml --spec NH-SMOKE-001` |
| 图像生成冒烟 | `workflows/at/naohai_04_video_editor_probe.yaml` | `python src/main_workflow.py --workflow workflows/at/naohai_04_video_editor_probe.yaml --spec NH-SMOKE-001` |
| 视频导出冒烟 | `workflows/at/naohai_05_create_story_to_video_e2e.yaml` | `python src/main_workflow.py --workflow workflows/at/naohai_05_create_story_to_video_e2e.yaml --spec NH-SMOKE-001` |
| 完整功能冒烟 | `workflows/smoke/naohai_full_functionality_smoke.yaml` | `python src/main_workflow.py --workflow workflows/smoke/naohai_full_functionality_smoke.yaml --spec NH-SMOKE-001` |

### Entry Point 执行入口
```bash
# 完整冒烟测试
python src/main_workflow.py --spec NH-SMOKE-001 --mode full

# 快速功能检查
python src/main_workflow.py --spec NH-SMOKE-001 --mode quick

# 健康状态检查
python src/main_workflow.py --spec NH-SMOKE-001 --mode health

# 核心功能验证
python src/main_workflow.py --spec NH-SMOKE-001 --focus core
```

### 测试数据绑定
- 冒烟测试配置：`test_data/smoke/smoke_test_configs.json`
- 基础功能数据：`test_data/smoke/basic_functionality_data.json`
- 健康检查脚本：`test_data/smoke/health_check_scripts/`
- 性能基线数据：`test_data/smoke/performance_baseline.json`
- 期望冒烟结果：`test_data/expected/smoke_expected_results.json`

## Evidence Policy
- 每次执行必须在 runs/<date>/ 下生成 NH-SMOKE-001-run.md 记录
- 冒烟测试的核心操作截图必须保存
- 系统健康状态数据必须完整记录
- 响应时间和性能数据必须统计
- 若核心功能异常，必须在紧急 Bug Issue 中引用对应的 Smoke Run 文件
- 测试环境清理结果必须记录，避免缓存干扰

## ChangeLog
- 2025-03-08: 初版 - 基于闹海AT冒烟测试设计
- 2025-03-08: 绑定具体workflow文件和测试数据
- 2025-03-08: 增加系统健康检查和性能快照功能