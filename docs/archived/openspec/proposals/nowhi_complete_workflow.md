# 工作流提案：NowHi网站完整功能测试

**目标：** 为 http://115.29.232.120/nowhi/index.html 创建完整的自动化测试工作流，覆盖从导航到视频生成的完整流程。

## 现状分析

基于现有配置文件 `config/config.yaml`，项目已具备：
- ✅ 完整的网站选择器配置（prompt输入、生成按钮、结果区域）
- ✅ 浏览器自动化配置（Chromium、headless、视口设置）
- ✅ MCP观测系统（网络、性能、DOM、截图监控）
- ✅ 报告生成系统（JSON、HTML、决策导向格式）
- ✅ 重试机制和错误处理

## 提案内容

### 1. 基础导航工作流 (`workflows/archive/nowhi_basic_navigation.yaml`)

创建一个简单可靠的导航工作流，验证网站可达性和基本元素加载。

```yaml
workflow:
  name: "nowhi_basic_navigation"
  description: "NowHi网站基础导航测试 - 验证网站可达性和页面加载"

  phases:
    - name: "site_accessibility"
      description: "验证网站可访问性和页面基本结构"
      steps:
        - action: "open_page"
          url: "${test.url}"
          timeout: ${test.timeout.page_load}

        - action: "wait_for"
          condition:
            selector: "body"
            visible: true
          timeout: ${test.timeout.element_load}

        - action: "screenshot"
          name: "page_loaded"
          description: "页面加载完成后的截图"
          save_path: "screenshots/basic_navigation.png"

success_criteria:
  - phase_success: "成功加载页面并检测到body元素"
  - overall_success: "所有步骤成功完成"

data_requirements:
  - test_url: "需要提供测试目标URL"
  - test_timeout: "页面加载超时配置"
  - screenshot_path: "截图保存路径配置"
```

### 2. 文本到图像生成工作流 (`workflows/archive/nowhi_text_to_image.yaml`)

测试核心的文本输入和图像生成功能，验证AI生成能力。

```yaml
workflow:
  name: "nowhi_text_to_image"
  description: "NowHi网站文本到图像生成测试 - 验证提示词输入和图像生成功能"

  phases:
    - name: "prepare_generation"
      description: "准备图像生成环境"
      steps:
        - action: "wait_for"
          condition:
            selector: "${selectors.prompt_input}"
            visible: true
          timeout: ${test.timeout.element_load}

        - action: "clear_input"
          selector: "${selectors.prompt_input}"
          clear: true

        - action: "input"
          selector: "${selectors.prompt_input}"
          text: "${test.prompt}"
          clear: false

        - action: "screenshot"
          name: "prompt_entered"
          description: "输入提示词后的截图"
          save_path: "screenshots/prompt_entered.png"

    - name: "generate_image"
      description: "生成图像并等待结果"
      steps:
        - action: "click"
          selector: "${selectors.generate_image_button}"
          timeout: ${test.timeout.element_load}

        - action: "wait_for"
          condition:
            selector: "${selectors.image_result} img"
            visible: true
            timeout: ${test.timeout.image_generation}

        - action: "screenshot"
          name: "image_generated"
          description: "图像生成完成后的截图"
          save_path: "screenshots/image_generated.png"

    - name: "verify_image"
      description: "验证生成的图像内容"
      steps:
        - action: "wait_for"
          condition:
            selector: "${selectors.image_result}"
            attribute:
              data-result: "image"
            timeout: ${test.timeout.element_load}

        - action: "screenshot"
          name: "image_verified"
          description: "图像验证完成后的截图"
          save_path: "screenshots/image_verified.png"

success_criteria:
  - phase_success: "成功生成图像并通过验证"
  - overall_success: "完整的文本到图像流程成功"

data_requirements:
  - test_prompt: "测试用的提示词文本"
  - test_timeout: "各阶段超时配置"
  - selectors: "所有页面元素选择器配置"
  - screenshot_path: "截图保存路径配置"
```

### 3. 图像到视频生成工作流 (`workflows/archive/nowhi_image_to_video.yaml`)

测试图像到视频的转换功能，验证视频生成能力。

```yaml
workflow:
  name: "nowhi_image_to_video"
  description: "NowHi网站图像到视频生成测试 - 验证图像到视频转换功能"

  phases:
    - name: "prepare_video_generation"
      description: "准备视频生成环境"
      steps:
        - action: "wait_for"
          condition:
            selector: "${selectors.image_result} img[data-result='image']"
            visible: true
          timeout: ${test.timeout.element_load}

        - action: "click"
          selector: "${selectors.generate_video_button}"
          timeout: ${test.timeout.element_load}

    - name: "generate_video"
      description: "生成视频并等待结果"
      steps:
        - action: "wait_for"
          condition:
            selector: "${selectors.video_result} video"
            visible: true
            timeout: ${test.timeout.video_generation}

        - action: "screenshot"
          name: "video_generated"
          description: "视频生成完成后的截图"
          save_path: "screenshots/video_generated.png"

    - name: "verify_video"
      description: "验证生成的视频内容"
      steps:
        - action: "wait_for"
          condition:
            selector: "${selectors.video_result} video[data-result='video']"
            attribute:
              data-result: "video"
            timeout: ${test.timeout.element_load}

        - action: "extract_video_info"
          description: "提取视频信息（时长、格式等）"
          selector: "${selectors.video_result} video[data-result='video']"
          attributes:
            - "duration"
            - "format"
            - "size"
          timeout: ${test.timeout.element_load}

        - action: "screenshot"
          name: "video_verified"
          description: "视频验证完成后的截图"
          save_path: "screenshots/video_verified.png"

success_criteria:
  - phase_success: "成功生成视频并通过验证"
  - overall_success: "完整的图像到视频流程成功"

data_requirements:
  - test_timeout: "视频生成专用超时配置"
  - screenshot_path: "视频截图保存路径配置"
```

### 4. 完整功能测试工作流 (`workflows/archive/nowhi_complete_test.yaml`)

集成所有功能的端到端测试，验证完整的用户流程。

```yaml
workflow:
  name: "nowhi_complete_test"
  description: "NowHi网站完整功能测试 - 从文本输入到视频生成的完整用户流程"

  phases:
    - name: "navigation"
      ref: "workflows/archive/nowhi_basic_navigation.yaml"
      description: "使用基础导航工作流验证网站可达性"

    - name: "text_to_image"
      ref: "workflows/archive/nowhi_text_to_image.yaml"
      description: "使用文本到图像工作流测试AI生成能力"

    - name: "image_to_video"
      ref: "workflows/archive/nowhi_image_to_video.yaml"
      description: "使用图像到视频工作流测试视频转换能力"

success_criteria:
  - phase_success: "每个阶段成功完成"
  - overall_success: "所有阶段成功，完整用户流程验证通过"

data_requirements:
  - test_prompt: "完整的测试提示词"
  - all_selectors: "所有必需的选择器配置"
  - all_timeouts: "各阶段的超时配置"
  - screenshot_config: "所有阶段截图配置"
```

## 配套测试脚本

### 1. 环境验证脚本 (`scripts/validate_environment.py`)

```python
#!/usr/bin/env python3
"""
环境验证脚本 - 测试前检查环境就绪状态
"""

import sys
import requests
import time
from pathlib import Path

def check_environment():
    """检查测试环境是否就绪"""
    issues = []

    # 检查网站可达性
    try:
        response = requests.get('http://115.29.232.120/nowhi/index.html', timeout=10)
        if response.status_code == 200:
            print("✅ 网站可达性检查通过")
        else:
            issues.append(f"网站响应异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        issues.append(f"网络连接失败: {e}")

    # 检查依赖
    try:
        import playwright
        print("✅ Playwright依赖检查通过")
    except ImportError:
        issues.append("Playwright未安装：pip install playwright")

    # 检查配置文件
    config_files = [
        'config/config.yaml',
        'config/mcp_config.yaml'
    ]
    for config_file in config_files:
        if not Path(config_file).exists():
            issues.append(f"配置文件缺失: {config_file}")

    if issues:
        print("\n❌ 环境检查发现问题：")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("\n✅ 环境检查通过，可以开始测试")
    return True

if __name__ == "__main__":
    if not check_environment():
        sys.exit(1)
```

### 2. 测试执行脚本 (`scripts/run_workflow_test.py`)

```python
#!/usr/bin/env python3
"""
工作流测试执行脚本 - 统一的测试执行入口
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='执行NowHi网站工作流测试')
    parser.add_argument('workflow', required=True, help='工作流配置文件路径')
    parser.add_argument('config', default='config/test_config.yaml', help='测试配置文件路径')
    parser.add_argument('report-dir', default='test_reports', help='测试报告输出目录')
    parser.add_argument('dry-run', action='store_true', help='仅验证配置，不执行测试')

    args = parser.parse_args()

    # 验证工作流文件存在
    if not Path(args.workflow).exists():
        print(f"❌ 工作流文件不存在: {args.workflow}")
        sys.exit(1)

    # 创建报告目录
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    # 生成测试执行命令
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"workflow_test_{timestamp}"

    cmd = [
        "python", "main.py",
        "--workflow", args.workflow,
        "--config", args.config,
        "--mcp-diagnostic"  # 启用MCP诊断模式
    ]

    if not args.dry_run:
        print(f"🚀 执行工作流测试: {Path(args.workflow).stem}")
        print(f"📁 报告将保存到: {report_dir}")
        print(f"⚙️ 执行命令: {' '.join(cmd)}")

        # 这里可以添加实际的执行逻辑
        # os.system(' '.join(cmd))

    else:
        print("✅ 配置验证通过（干运行模式）")

if __name__ == "__main__":
    main()
```

## 优先级建议

### 高优先级（立即实施）
1. **创建基础导航工作流** - 验证网站基本功能
2. **实现环境验证脚本** - 确保测试前环境就绪
3. **完善错误处理** - 增强网络超时、元素缺失等异常处理

### 中优先级（后续实施）
1. **文本到图像工作流** - 测试AI生成核心功能
2. **图像到视频工作流** - 验证视频转换能力
3. **完整集成测试** - 端到端流程验证

### 低优先级（可选）
1. **性能基准测试** - 对各阶段进行性能分析
2. **并发测试** - 验证多工作流并行执行
3. **回归测试套件** - 自动化回归测试

## 实施计划

1. **第一阶段**（1-2天）
   - 创建基础导航工作流和验证脚本
   - 测试网站可达性和基本元素加载
   - 收集基础性能数据

2. **第二阶段**（3-5天）
   - 实现文本到图像工作流
   - 测试AI生成功能稳定性
   - 优化MCP观测数据收集

3. **第三阶段**（1周）
   - 实现图像到视频工作流
   - 测试视频生成质量
   - 创建完整集成测试

4. **第四阶段**（持续）
   - 性能优化和监控增强
   - 回归测试自动化
   - 报告系统完善

这个提案基于你现有的配置和架构，提供了从简单到复杂的渐进式实施方案，确保每个阶段都能独立验证和交付。
