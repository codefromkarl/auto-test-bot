# 端到端测试指南

## 📋 指南说明

**更新时间**：2025-12-19
**适用对象**：需要执行端到端测试的QA和开发人员
**核心目标**：提供完整的端到端测试执行和质量验证方案

---

## 🎯 E2E测试概览

### 测试范围
端到端测试覆盖从用户输入到最终内容生成的完整流程：
1. **用户导航流程** - 从首页到AI创作页面
2. **内容创建流程** - 文本输入、参数设置、生成触发
3. **质量验证流程** - 自动化内容质量评估
4. **结果管理流程** - 下载、保存、分享功能

### 测试架构
```
┌─────────────────────────────────────────────────┐
│                  E2E Test架构                    │
├─────────────────────────────────────────────────┤
│  用户层: User Actions & Navigation                │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  页面导航   │  │  文本输入   │  │  参数设置  │  │
│  └─────────────┘  └─────────────┘  └───────────┘  │
│                                                    │
│  业务层: Business Logic Validation                │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  剧本验证   │  │  生成验证   │  │  状态管理  │  │
│  └─────────────┘  └─────────────┘  └───────────┘  │
│                                                    │
│  质量层: Content Quality Validation               │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  图片验证   │  │  视频验证   │  │  一致性验证│  │
│  └─────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 📁 测试文件结构

### 核心文件
```
E2E测试框架/
├── 工作流定义/
│   ├── workflows/e2e/                 # E2E测试用例
│   │   ├── user_journey.yaml         # 用户旅程测试
│   │   ├── content_creation.yaml     # 内容创建测试
│   │   └── quality_validation.yaml   # 质量验证测试
│   └── workflows/rt/                 # 回归测试套件
│
├── 验证模块/
│   └── src/validation/               # 内容验证器
│       ├── content_validator.py      # 主验证器
│       ├── image_validator.py        # 图片验证
│       ├── video_validator.py        # 视频验证
│       ├── consistency_validator.py  # 一致性验证
│       └── relevance_scorer.py       # 相关性评分
│
├── 执行脚本/
│   ├── scripts/run_e2e_suite.py      # E2E测试执行器
│   └── scripts/run_regression_suite.py # 回归测试执行器
│
└── 测试数据/
    ├── test_data/                     # 测试数据
    ├── test_artifacts/               # 测试产物
    └── validation_reports/           # 验证报告
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install

# 验证环境
python scripts/validate_environment.py
```

### 2. 执行基础E2E测试

```bash
# 执行完整用户旅程
python scripts/run_workflow_test.py \
  --workflow workflows/e2e/user_journey.yaml \
  --config config/e2e_config.yaml

# 执行内容创建测试
python scripts/run_workflow_test.py \
  --workflow workflows/e2e/content_creation.yaml \
  --config config/e2e_config.yaml
```

### 3. 查看测试结果

```bash
# 查看测试报告
open reports/latest/e2e_report.html

# 查看测试截图
open screenshots/

# 查看验证报告
open validation_reports/latest/validation_report.html
```

---

## 📊 详细测试流程

### Phase 1：用户旅程测试

测试目标：验证用户从进入网站到完成创作的完整流程

```yaml
# workflows/e2e/user_journey.yaml
name: "用户旅程端到端测试"
description: "验证完整用户操作流程"

test_steps:
  - step: "访问首页"
    action: "navigate"
    target: "http://<NOWHI_HOST>/nowhi/index.html"
    expected: "首页正常加载"

  - step: "导航到AI创作"
    action: "click"
    selector: "[data-testid='ai-create-btn']"
    expected: "跳转到创作页面"

  - step: "输入创作文本"
    action: "input"
    selector: "[data-testid='prompt-input']"
    text: "一只可爱的小猫在花园里玩耍"
    expected: "文本输入成功"

  - step: "选择创作风格"
    action: "select"
    selector: "[data-testid='style-select']"
    value: "cartoon"
    expected: "风格选择成功"

  - step: "开始生成"
    action: "click"
    selector: "[data-testid='generate-btn']"
    expected: "开始生成流程"

  - step: "等待生成完成"
    action: "wait"
    condition: "element_visible"
    selector: "[data-testid='result-container']"
    timeout: 60000
    expected: "生成完成"
```

执行命令：
```bash
python scripts/run_workflow_test.py \
  --workflow workflows/e2e/user_journey.yaml \
  --config config/e2e_config.yaml \
  --with-validation
```

### Phase 2：内容创建验证

测试目标：验证各类内容创建功能的正确性

```yaml
# workflows/e2e/content_creation.yaml
name: "内容创建功能测试"
description: "验证文生图、图生视频等功能"

test_scenarios:
  - scenario: "文生图功能"
    test_cases:
      - name: "基础文生图"
        input:
          prompt: "科技感机器人"
          style: "realistic"
          size: "1024x1024"
        validation:
          - check_image_generated
          - check_quality_score > 70
          - check_relevance > 0.8

      - name: "多风格文生图"
        inputs:
          - prompt: "森林小屋"
            style: "anime"
          - prompt: "森林小屋"
            style: "realistic"
        validation:
          - check_style_consistency
          - compare_results

  - scenario: "图生视频功能"
    test_cases:
      - name: "基础图生视频"
        input:
          image: "test_data/sample_image.jpg"
          duration: 10
          motion: "smooth"
        validation:
          - check_video_generated
          - check_duration >= 8
          - check_fps >= 12
          - check_motion_quality
```

执行命令：
```bash
python scripts/run_workflow_test.py \
  --workflow workflows/e2e/content_creation.yaml \
  --config config/e2e_config.yaml \
  --validation-level strict
```

### Phase 3：质量验证流程

测试目标：自动化验证生成内容的质量

```python
# 使用内容验证器
from src.validation import ContentValidator

# 初始化验证器
validator = ContentValidator(config_path='config/e2e_config.yaml')

# 验证内容
content_paths = {
    'images': ['output/image_1.png', 'output/image_2.png'],
    'videos': ['output/video_1.mp4']
}

context = {
    'characters': ['小猫', '花园'],
    'scenes': ['户外', '晴天'],
    'style': 'cartoon'
}

# 执行验证
report = validator.validate_content(
    content_paths=content_paths,
    expected_prompt="一只可爱的小猫在花园里玩耍",
    context=context
)

# 查看结果
print(f"总体评分: {report.overall_score}")
print(f"通过项: {len(report.passed_items)}")
print(f"失败项: {len(report.failed_items)}")
```

---

## 🔧 配置参数说明

### E2E测试配置

```yaml
# config/e2e_config.yaml
e2e:
  # 测试环境配置
  environment:
    base_url: "http://<NOWHI_HOST>/nowhi/index.html"
    browser: "chromium"
    headless: false
    viewport: {"width": 1920, "height": 1080}

  # 超时配置
  timeouts:
    navigation: 30000
    element_wait: 10000
    generation: 120000
    validation: 60000

  # 测试数据
  test_data:
    prompts_file: "test_data/prompts.json"
    images_dir: "test_data/images"
    output_dir: "test_artifacts/e2e"

  # 验证配置
  validation:
    enabled: true
    strict_mode: false
    thresholds:
      image_quality: 70
      video_quality: 65
      relevance_score: 0.75
      consistency_score: 0.80

  # 报告配置
  reporting:
    formats: ["html", "json", "junit"]
    include_screenshots: true
    include_videos: true
    include_metrics: true
```

### 验证器配置

```yaml
validation:
  # 图片验证参数
  image:
    min_resolution: {"width": 512, "height": 512}
    max_resolution: {"width": 4096, "height": 4096}
    quality_metrics:
      - sharpness
      - contrast
      - brightness
      - color_balance
    supported_formats: ["jpg", "jpeg", "png", "webp"]

  # 视频验证参数
  video:
    min_duration: 3.0
    max_duration: 60.0
    min_fps: 12
    max_fps: 60
    quality_metrics:
      - resolution
      - fps
      - bitrate
      - stability
    supported_formats: ["mp4", "webm", "mov", "avi"]

  # 一致性验证
  consistency:
    character_similarity_threshold: 0.75
    scene_similarity_threshold: 0.70
    style_consistency_threshold: 0.75
    enable_cross_frame_analysis: true

  # 相关性评分
  relevance:
    model: "clip"
    similarity_threshold: 0.65
    visual_weight: 0.7
    semantic_weight: 0.3
```

---

## 📈 测试执行策略

### 1. 烟雾测试（Smoke Test）

```bash
# 快速验证核心功能
python scripts/run_e2e_suite.py \
  --suite smoke \
  --parallel \
  --max-workers 2
```

包含测试：
- 页面可访问性
- 基础导航功能
- 简单内容生成

### 2. 功能测试（Functional Test）

```bash
# 验证所有功能
python scripts/run_e2e_suite.py \
  --suite functional \
  --with-validation \
  --report-format html
```

包含测试：
- 完整用户流程
- 所有创作功能
- 基础质量验证

### 3. 回归测试（Regression Test）

```bash
# 对比基线版本
python scripts/run_regression_suite.py \
  --type baseline \
  --baseline-version v1.0.0 \
  --categories core performance \
  --parallel
```

包含测试：
- 性能回归检测
- 功能回归验证
- 基线对比分析

### 4. 压力测试（Stress Test）

```bash
# 并发测试
python scripts/run_e2e_suite.py \
  --suite stress \
  --concurrent-users 10 \
  --ramp-up-time 60
```

包含测试：
- 并发用户访问
- 高负载生成
- 系统稳定性

---

## 🔍 故障排查指南

### 常见问题诊断

#### 1. 页面加载超时

**症状**：测试在页面加载阶段超时

**排查步骤**：
```bash
# 检查网络连接
curl -I http://<NOWHI_HOST>/nowhi/index.html

# 增加超时时间
# 编辑 config/e2e_config.yaml
timeouts:
  navigation: 60000  # 增加到60秒

# 启用详细日志
python scripts/run_workflow_test.py \
  --workflow workflows/e2e/user_journey.yaml \
  --log-level debug
```

#### 2. 元素定位失败

**症状**：找不到页面元素

**排查步骤**：
```bash
# 使用MCP调试工具
python -m src.mcp.dom_debugger \
  --url http://<NOWHI_HOST>/nowhi/index.html \
  --selector "[data-testid='ai-create-btn']"

# 检查元素是否存在
# 在浏览器控制台执行：
document.querySelector('[data-testid="ai-create-btn"]')
```

#### 3. 生成任务失败

**症状**：内容生成过程中断

**排查步骤**：
```bash
# 检查生成状态
python -m src.monitoring.status_checker \
  --workflow-id <workflow-id>

# 查看错误日志
tail -f logs/generation.log

# 重试机制
python scripts/run_workflow_test.py \
  --workflow workflows/e2e/content_creation.yaml \
  --retry-count 3 \
  --retry-delay 5
```

#### 4. 验证评分过低

**症状**：内容质量验证不通过

**排查步骤**：
```bash
# 手动验证内容
python -m src.validation.content_validator \
  --images <image-path> \
  --prompt <original-prompt> \
  --verbose

# 调整验证阈值
# 编辑 config/e2e_config.yaml
validation:
  thresholds:
    image_quality: 60  # 降低阈值
    relevance_score: 0.6

# 生成详细报告
python -m src.validation.content_validator \
  --images <image-path> \
  --report-format html \
  --include-metrics
```

### 性能问题排查

#### 1. 响应时间过长

**诊断工具**：
```bash
# 性能分析
python -m src.monitoring.performance_tracer \
  --workflow <workflow-id> \
  --output perf_report.json

# 瓶颈分析
python -m src.utils.bottleneck_analyzer \
  --report perf_report.json
```

#### 2. 并发执行失败

**排查步骤**：
```bash
# 检查资源使用
python scripts/resource_monitor.py \
  --interval 1 \
  --duration 60

# 调整并发数
python scripts/run_regression_suite.py \
  --parallel \
  --workers 2  # 减少并发数
```

---

## 📊 测试报告解读

### HTML报告结构

```
E2E测试报告/
├── 执行摘要
│   ├── 测试概览
│   ├── 通过率统计
│   └── 执行时间
├── 详细结果
│   ├── 测试用例详情
│   ├── 失败截图
│   └── 错误日志
├── 性能指标
│   ├── 响应时间
│   ├── 资源使用
│   └── 趋势分析
└── 质量验证
    ├── 图片质量评分
    ├── 视频质量评分
    └── 一致性分析
```

### 关键指标说明

| 指标 | 说明 | 合格范围 |
|------|------|----------|
| **测试通过率** | 通过用例/总用例 | > 95% |
| **平均响应时间** | 页面加载平均时间 | < 3秒 |
| **生成成功率** | 成功生成/尝试次数 | > 90% |
| **内容质量分** | 综合质量评分 | > 70分 |
| **一致性得分** | 内容一致性评分 | > 0.75 |

---

## 🎯 最佳实践

### 测试设计原则

1. **独立性**：每个测试用例应该独立运行，不依赖其他用例
2. **可重复性**：测试结果应该稳定可重复
3. **清晰性**：测试步骤和断言应该清晰明确
4. **完整性**：覆盖所有关键业务流程

### 测试数据管理

```bash
# 测试数据准备
python scripts/test_data_manager.py \
  --action prepare \
  --dataset standard

# 测试数据清理
python scripts/test_data_manager.py \
  --action cleanup \
  --older-than 7d
```

### 持续集成集成

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install

      - name: Run E2E tests
        run: |
          python scripts/run_e2e_suite.py \
            --suite smoke \
            --format junit \
            --output test-results.xml

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: e2e-results
          path: test_artifacts/e2e/
```

---

## 📞 支持与维护

### 获取帮助

```bash
# 查看命令帮助
python scripts/run_workflow_test.py --help
python scripts/run_regression_suite.py --help
python -m src.validation.content_validator --help

# 生成诊断信息
python scripts/generate_diagnostics.py \
  --output diagnostics.json
```

### 联系方式

- **技术支持**：创建GitHub Issue
- **测试咨询**：联系QA团队
- **文档反馈**：提交PR或Issue

---

**指南版本**：v1.0
**最后更新**：2025-12-19
**维护团队**：测试开发团队
**下次更新**：重大功能更新时