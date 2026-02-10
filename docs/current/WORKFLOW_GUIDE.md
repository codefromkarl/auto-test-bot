# 测试流程使用指南

## 📋 指南说明

**更新时间**：2025-12-18
**适用对象**：需要了解NowHi项目测试流程的团队成员
**核心目标**：提供清晰、完整的测试流程使用指导

---

## 🎯 测试流程概览

### 项目目标
基于 `http://<NOWHI_HOST>/nowhi/index.html` 的完整功能测试，验证从文本输入到视频生成的用户流程。

### 核心测试场景
1. **基础导航测试** - 验证页面可访问性和关键元素存在
2. **文生图测试** - 输入提示词，生成图片并验证结果
3. **图生视频测试** - 基于图片生成视频并验证结果

---

## 📁 测试流程文件位置

### 主要文档
| 文档 | 位置 | 状态 | 用途 |
|------|--------|------|------|
| **测试流程指南** | `docs/current/WORKFLOW_GUIDE.md` | ✅ 当前有效 | 完整流程说明 |
| **端到端测试指南** | `docs/current/E2E_TESTING_GUIDE.md` | ✅ 新增 | E2E测试详细指南 |
| **配置说明** | `README.md` | ✅ 最新 | 基础配置方法 |
| **环境验证** | `scripts/validate_environment.py` | ✅ 有效 | 环境检查脚本 |
| **测试执行** | `scripts/run_workflow_test.py` | ✅ 有效 | 测试执行脚本 |
| **回归测试套件** | `scripts/run_regression_suite.py` | ✅ 新增 | 回归测试执行器 |

### 测试用例
| 用例类型 | 位置 | 状态 | 说明 |
|-----------|--------|------|------|
| **冒烟用例** | `workflows/at/` | ✅ 有效 | 基础功能验证 |
| **功能用例** | `workflows/fc/` | ✅ 有效 | 完整功能覆盖 |
| **回归用例** | `workflows/rt/` | ✅ 新增 | 回归测试套件 |
| **用例索引** | `workflows/fc/FC_INDEX.md` | ✅ 有效 | 用例查找工具 |

---

## 📖 详细测试流程

### Phase 1：环境准备

```bash
# 1.1 验证环境就绪
python scripts/validate_environment.py

# 1.2 检查配置文件
ls -la config/config.yaml config/test_config.yaml

# 1.3 确认浏览器安装
playwright install --dry-run
```

**环境要求**：
- Python 3.8+
- Node.js (用于 MCP 服务器)
- Chrome/Chromium 浏览器
- 网络连接到目标服务器

---

### Phase 2：基础导航测试

```bash
# 2.1 执行基础导航
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_basic_navigation.yaml \
  --config config/test_config.yaml

# 2.2 验证页面加载
# 检查关键元素是否正确加载
# 验证页面响应时间是否在合理范围内
```

**验证内容**：
- 网站可达性
- 页面加载完整性
- 关键元素可见性
- 基础交互功能

---

### Phase 3：文生图测试

```bash
# 3.1 执行文生图测试
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_text_to_image.yaml \
  --config config/test_config.yaml

# 3.2 验证图片生成
# 检查图片是否成功生成
# 验证生成时间是否在预期范围内
# 验证图片质量和内容相关性
```

**测试要点**：
- AI创作页面导航
- 提示词输入功能
- 图片生成触发机制
- 结果验证和错误处理

---

### Phase 4：图生视频测试

```bash
# 4.1 执行图生视频测试
python scripts/run_workflow_test.py \
  --workflow workflows/archive/nowhi_image_to_video.yaml \
  --config config/test_config.yaml

# 4.2 验证视频生成
# 检查视频是否成功生成
# 验证视频时长和质量
# 验证视频下载功能
```

**测试要点**：
- 图片上传功能
- 视频生成参数设置
- 生成进度监控
- 结果验证和保存

---

### Phase 5：内容质量验证（新增）

```bash
# 5.1 执行内容验证
python -m src.validation.content_validator \
  --images output/generated_images/ \
  --videos output/generated_videos/ \
  --prompt "测试提示词" \
  --config config/config.yaml

# 5.2 查看验证报告
ls validation_reports/
cat validation_reports/validation_report_YYYYMMDD_HHMMSS.json
```

**验证模块**：
- **图片质量验证** (`src/validation/image_validator.py`)
  - 分辨率和格式检查
  - 图像质量评分（清晰度、对比度、亮度）
  - 支持格式：JPG、PNG、WebP

- **视频质量验证** (`src/validation/video_validator.py`)
  - 时长和帧率验证
  - 视频稳定性检测
  - 支持格式：MP4、WebM、MOV、AVI

- **一致性验证** (`src/validation/consistency_validator.py`)
  - 角色一致性检测
  - 场景连贯性验证
  - 风格统一性评分

- **相关性评分** (`src/validation/relevance_scorer.py`)
  - 基于CLIP模型的内容相关性
  - 语义相似度计算
  - 综合评分机制

---

## 🔧 配置和使用

### 配置文件选择

| 场景 | 配置文件 | 用途 |
|------|---------|------|
| **本地开发** | `config/config.yaml` | 默认配置 |
| **测试环境** | `config/test_config.yaml` | 测试专用配置 |
| **生产环境** | `config/ci_config.yaml` | CI/CD配置 |

### 关键配置项

```yaml
# config/config.yaml 示例
test:
  url: "http://<NOWHI_HOST>/nowhi/index.html"
  timeout: 30000

  selectors:
    prompt_input: "#prompt-input"
    generate_image_button: "#generate-image-btn"
    video_result: ".video-result"

steps:
  open_site: true
  generate_image: true
  generate_video: true
```

---

## 📊 测试执行

### 批量执行

```bash
# 执行所有功能用例
for workflow in workflows/fc/naohai_FC_NH_*.yaml; do
  python scripts/run_workflow_test.py --workflow $workflow --config config/config.yaml
done

# 执行特定类型用例
python scripts/run_workflow_test.py --workflow workflows/fc/ --config config/config.yaml

# 执行回归测试套件
python scripts/run_regression_suite.py --type full --categories core performance

# 并行执行回归测试
python scripts/run_regression_suite.py --type incremental --parallel --workers 4

# 并行执行（高级用法）
python scripts/parallel_executor.py --max-jobs 4
```

### 结果查看

```bash
# 查看测试报告
ls reports/latest/

# 查看测试截图
ls screenshots/

# 查看详细日志
tail -f logs/test_bot.log

# 查看验证报告
ls validation_reports/

# 查看回归测试报告
ls test_artifacts/regression/reports/
```

---

## 🔍 故障排查

### 常见问题及解决

| 问题类型 | 症状 | 解决方法 | 相关文档 |
|---------|--------|----------|----------|
| **页面加载失败** | 超时错误 | 检查网络、增加timeout | [配置说明](../README.md) |
| **元素定位失败** | Selector不存在 | 使用RF语义化版本 | [RF迁移总结](../RF_MIGRATION_FINAL_SUMMARY.md) |
| **生成任务失败** | AIGC服务错误 | 检查服务状态、重试机制 | [错误诊断](../chrome-devtools-mcp-guide.md) |
| **截图失败** | 权限问题 | 检查目录权限、磁盘空间 | [环境验证](../../scripts/validate_environment.py) |
| **内容验证失败** | 验证评分低 | 检查内容质量、调整阈值 | [E2E测试指南](E2E_TESTING_GUIDE.md) |
| **回归测试异常** | 性能下降 | 对比基线、检查变更 | [回归测试报告](test_artifacts/regression/reports/) |

### 调试工具

```bash
# 启用MCP调试
python scripts/run_workflow_test.py --workflow XXX --config config/debug_config.yaml

# 开启详细日志
python scripts/run_workflow_test.py --workflow XXX --config config/config.yaml --verbose

# 生成调试报告
python scripts/debug_workflow.py --workflow XXX --debug-level deep
```

---

## 📈 性能优化

### 并行测试

```bash
# 使用并行执行提升效率
python scripts/parallel_executor.py \
  --max-concurrent-jobs 4 \
  --workflow-dir workflows/fc/ \
  --config config/config.yaml
```

### 缓存优化

- 使用浏览器实例复用
- 启用页面缓存机制
- 优化资源加载策略

---

## 🎯 最佳实践

### 测试编写
1. **使用RF语义化版本** - 优先使用 `*_rf.yaml` 文件
2. **遵循命名规范** - 使用清晰的用例名称
3. **添加断言验证** - 确保测试结果准确
4. **处理异常情况** - 添加适当的错误处理

### 执行策略
1. **环境一致性** - 确保测试环境配置一致
2. **数据管理** - 使用标准化的测试数据
3. **结果记录** - 完整记录测试结果和日志
4. **定期清理** - 定期清理测试数据和缓存

---

## 📞 支持和帮助

### 获取帮助
```bash
# 查看命令帮助
python scripts/run_workflow_test.py --help

# 查看配置帮助
python scripts/validate_environment.py --help

# 查看完整文档
cat docs/current/WORKFLOW_GUIDE.md
```

### 联系支持
- **技术问题**：联系开发团队
- **环境问题**：联系运维团队
- **用例问题**：联系测试团队
- **文档问题**：查看项目文档或联系文档维护

---

## 🔗 相关资源

### 快速链接
- **📋 项目总览**：[../../README.md](../../README.md)
- **📖 架构设计**：[../architecture-design/README.md](../architecture-design/README.md)
- **🚀 E2E测试指南**：[E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)
- **🔧 故障排查指南**：[TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
- **🎉 RF迁移成果**：[../RF_MIGRATION_FINAL_SUMMARY.md](../RF_MIGRATION_FINAL_SUMMARY.md)
- **⚡ 项目优化**：[../optimization_todo.md](../optimization_todo.md)

### 外部文档
- **Playwright文档**：https://playwright.dev/docs
- **Python最佳实践**：团队内部文档
- **测试环境配置**：运维团队文档

---

**指南版本**：v1.0
**最后更新**：2025-12-18
**维护团队**：项目团队
**下次更新**：重大功能变更时更新