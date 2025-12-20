# 故障排查指南

## 📋 指南说明

**更新时间**：2025-12-19
**适用对象**：测试执行人员、开发人员、运维人员
**核心目标**：提供全面的故障诊断和解决方案

---

## 🔍 快速诊断流程

### 诊断路线图
```
┌─────────────────────────────────────────┐
│           问题发生                      │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│    1. 识别问题类型                      │
│  □ 环境问题  □ 配置问题                │
│  □ 网络问题  □ 功能问题                │
│  □ 性能问题  □ 质量问题                │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│    2. 查看错误日志                      │
│  □ test_bot.log                        │
│  □ browser.log                         │
│  □ generation.log                      │
│  □ validation.log                      │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│    3. 执行诊断命令                      │
│  □ validate_environment.py              │
│  □ check_dependencies.py                │
│  □ diagnose_workflow.py                │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│    4. 应用解决方案                      │
│  □ 根据问题类型选择对应解决方案         │
│  □ 记录解决方案效果                     │
│  □ 更新知识库                          │
└─────────────────────────────────────────┘
```

---

## 🚨 常见问题分类

### 1. 环境问题

#### 问题1：Python环境依赖缺失

**症状**：
```
ModuleNotFoundError: No module named 'xxx'
ImportError: cannot import name 'xxx'
```

**诊断步骤**：
```bash
# 检查Python版本
python --version

# 检查虚拟环境
echo $VIRTUAL_ENV

# 检查已安装包
pip list | grep -E "(playwright|yaml|requests)"

# 验证依赖完整性
python scripts/validate_environment.py --verbose
```

**解决方案**：
```bash
# 1. 创建或激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 2. 更新pip
pip install --upgrade pip

# 3. 安装所有依赖
pip install -r requirements.txt

# 4. 安装Playwright浏览器
playwright install

# 5. 验证安装
python scripts/validate_environment.py
```

#### 问题2：浏览器驱动问题

**症状**：
```
PlaywrightError: Executable doesn't exist
BrowserType.launch: Executable doesn't exist
```

**诊断步骤**：
```bash
# 检查Playwright安装
playwright install --dry-run

# 检查浏览器安装位置
ls ~/.cache/ms-playwright/
ls ~/Library/Caches/ms-playwright/  # Mac
ls %LOCALAPPDATA%\ms-playwright\  # Windows

# 测试浏览器启动
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('Browser started successfully')
    browser.close()
"
```

**解决方案**：
```bash
# 强制重装浏览器
playwright install --force
playwright install-deps

# 清理缓存后重装
rm -rf ~/.cache/ms-playwright/
playwright install

# 使用系统浏览器（如果可用）
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
```

### 2. 网络问题

#### 问题1：目标网站不可达

**症状**：
```
TimeoutError: Navigation timeout exceeded
net::ERR_CONNECTION_TIMED_OUT
```

**诊断步骤**：
```bash
# 1. 基础连通性测试
ping <NOWHI_HOST>

# 2. 端口可访问性
telnet <NOWHI_HOST> 80
curl -I http://<NOWHI_HOST>/nowhi/index.html

# 3. DNS解析
nslookup <NOWHI_HOST>
dig <NOWHI_HOST>

# 4. 代理设置检查
echo $http_proxy
echo $https_proxy
```

**解决方案**：
```bash
# 1. 配置代理（如需要）
export http_proxy=http://proxy.company.com:8080
export https_proxy=http://proxy.company.com:8080

# 2. 修改hosts文件（如需要）
sudo echo "<NOWHI_HOST> nowhi.test" >> /etc/hosts

# 3. 调整超时设置
# 编辑 config/config.yaml
test:
  timeout: 60000  # 增加到60秒
  page_load_timeout: 180000  # 3分钟

# 4. 使用本地镜像（如果有）
test:
  url: "http://localhost:8080/nowhi/index.html"
```

#### 问题2：AI服务连接失败

**症状**：
```
ConnectionError: Failed to establish connection
APIError: Service unavailable
```

**诊断步骤**：
```bash
# 1. 检查AI服务状态
curl http://ai-service.example.com/health
curl http://<NOWHI_HOST>/api/status

# 2. 检查API密钥
grep -r "api_key" config/
grep -r "token" config/

# 3. 检查服务日志
tail -f logs/ai_service.log
```

**解决方案**：
```bash
# 1. 更新API配置
# 编辑 config/config.yaml
ai_service:
  api_key: "your-new-api-key"
  endpoint: "http://new-endpoint.example.com"
  timeout: 30000

# 2. 实现重试机制
# 在代码中添加
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_ai_service():
    # API调用逻辑
    pass
```

### 3. 配置问题

#### 问题1：选择器定位失败

**症状**：
```
TimeoutError: Element not found
SelectorError: No element matches selector
```

**诊断步骤**：
```bash
# 1. 使用MCP调试工具
python -m src.mcp.dom_debugger \
  --url http://<NOWHI_HOST>/nowhi/index.html \
  --selector "[data-testid='ai-create-btn']"

# 2. 检查页面结构
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('http://<NOWHI_HOST>/nowhi/index.html')
    page.pause()  # 手动检查
    browser.close()
"

# 3. 查看实际选择器
# 在浏览器控制台执行
document.querySelectorAll('[data-testid*=\"btn\"]')
document.querySelectorAll('button')
```

**解决方案**：
```yaml
# 1. 更新选择器配置
# 编辑 config/config.yaml
selectors:
  generate_image_button:
    - "[data-testid='generate-image-btn']"  # 优先使用data-testid
    - "button[data-action='generate-image']"
    - ".btn-generate:has-text('生成图片')"  # 使用文本定位
    - "xpath=//button[contains(text(), '生成图片')]"  # 使用XPath

# 2. 添加等待策略
steps:
  generate_image:
    wait_strategy:
      type: "selector"
      value: "[data-testid='generate-image-btn']"
      timeout: 10000
```

#### 问题2：配置文件格式错误

**症状**：
```
yaml.scanner.ScannerError
ConfigError: Invalid configuration
```

**诊断步骤**：
```bash
# 1. 验证YAML语法
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 2. 检查配置结构
python scripts/validate_config.py --file config/config.yaml

# 3. 查看配置差异
diff config/config.yaml config/config.yaml.backup
```

**解决方案**：
```bash
# 1. 使用YAML验证工具
pip install pyyaml
python -c "
import yaml
try:
    with open('config/config.yaml') as f:
        config = yaml.safe_load(f)
    print('Config is valid')
except yaml.YAMLError as e:
    print(f'YAML Error: {e}')
"

# 2. 重新生成配置模板
python scripts/generate_config_template.py > config/config.yaml.new

# 3. 合并配置
python scripts/merge_configs.py \
  --base config/config.yaml.new \
  --override config/config.yaml.override \
  --output config/config.yaml
```

### 4. 功能问题

#### 问题1：内容生成失败

**症状**：
```
GenerationError: Failed to generate content
TaskTimeout: Generation task timed out
```

**诊断步骤**：
```bash
# 1. 检查生成状态
python -m src.monitoring.generation_monitor \
  --workflow-id <id> \
  --status

# 2. 查看生成日志
tail -f logs/generation.log | grep -E "(ERROR|WARN)"

# 3. 检查资源使用
python scripts/resource_monitor.py --duration 60
```

**解决方案**：
```python
# 1. 添加重试机制
# 在生成代码中添加
from src.utils.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3, base_delay=5)
def generate_content(prompt, style):
    # 生成逻辑
    pass

# 2. 实现降级策略
def generate_with_fallback(prompt, style):
    try:
        # 尝试正常生成
        return normal_generate(prompt, style)
    except Exception:
        # 降级到简化生成
        return simple_generate(prompt, style)
```

#### 问题2：验证评分过低

**症状**：
```
ValidationError: Quality score below threshold
RelevanceError: Low relevance score
```

**诊断步骤**：
```bash
# 1. 手动验证内容
python -m src.validation.content_validator \
  --images <path> \
  --prompt "<prompt>" \
  --verbose

# 2. 分析评分细节
python -m src.validation.analyzer \
  --report validation_reports/latest.json \
  --details

# 3. 对比基准
python scripts/compare_with_baseline.py \
  --current <current_content> \
  --baseline <baseline_content>
```

**解决方案**：
```yaml
# 1. 调整验证阈值
# 编辑 config/validation_config.yaml
validation:
  mode: "relaxed"  # 或 "normal", "strict"
  thresholds:
    image_quality: 60  # 降低阈值
    relevance_score: 0.6

# 2. 优化提示词
# 改进测试提示词
test_prompt: "一只可爱的小猫在花园里玩耍，卡通风格，高清"

# 3. 添加预处理
# 在验证前添加内容优化
def preprocess_content(content):
    # 应用图像增强
    # 调整视频参数
    return optimized_content
```

### 5. 性能问题

#### 问题1：执行速度慢

**症状**：
```
PerformanceWarning: Slow execution detected
Test timeout exceeded
```

**诊断步骤**：
```bash
# 1. 性能分析
python -m src.utils.profiler \
  --workflow <workflow_id> \
  --output perf_report.json

# 2. 瓶颈识别
python -m src.utils.bottleneck_analyzer \
  --report perf_report.json

# 3. 资源监控
python scripts/monitor_resources.py \
  --interval 1 \
  --duration 300
```

**解决方案**：
```yaml
# 1. 启用并行执行
# 编辑配置
execution:
  parallel: true
  max_workers: 4

# 2. 优化超时设置
test:
  timeout: 30000
  element_timeout: 5000
  page_load_timeout: 60000

# 3. 启用缓存
cache:
  enabled: true
  ttl: 3600
  dir: ".cache"
```

#### 问题2：内存占用过高

**症状**：
```
MemoryError: Unable to allocate memory
OOMError: Out of memory
```

**诊断步骤**：
```bash
# 1. 监控内存使用
python -m memory_profiler scripts/run_workflow_test.py

# 2. 检查内存泄漏
python scripts/memory_leak_detector.py \
  --iterations 10 \
  --threshold 100MB

# 3. 分析对象生命周期
python -m objgraph <process_id>
```

**解决方案**：
```python
# 1. 优化内存使用
# 及时释放资源
def process_large_image(image_path):
    with Image.open(image_path) as img:
        # 处理图像
        result = process(img)
    # 自动释放内存

# 2. 批处理优化
def batch_process(items, batch_size=10):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        yield process_batch(batch)

# 3. 使用生成器
def stream_results():
    for item in large_dataset:
        yield process(item)
```

---

## 🔧 高级诊断工具

### 1. 系统诊断脚本

```python
#!/usr/bin/env python3
# scripts/diagnose_system.py

import os
import sys
import psutil
import platform
import subprocess
from pathlib import Path

def diagnose_system():
    """全面系统诊断"""
    print("=== 系统诊断报告 ===\n")

    # 系统信息
    print("1. 系统信息:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version}")
    print(f"   CPU: {psutil.cpu_count()} cores")
    print(f"   Memory: {psutil.virtual_memory().total // (1024**3)} GB\n")

    # 环境检查
    print("2. 环境检查:")
    print(f"   虚拟环境: {os.getenv('VIRTUAL_ENV', 'None')}")
    print(f"   当前目录: {os.getcwd()}")
    print(f"   PATH: {os.getenv('PATH')}\n")

    # 依赖检查
    print("3. 依赖检查:")
    required_packages = ['playwright', 'pyyaml', 'requests', 'pillow']
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f"   ✓ {pkg}")
        except ImportError:
            print(f"   ✗ {pkg} (missing)")

    # 网络检查
    print("\n4. 网络检查:")
    test_url = "http://<NOWHI_HOST>/nowhi/index.html"
    try:
        result = subprocess.run(['curl', '-I', test_url],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✓ 目标网站可访问")
        else:
            print(f"   ✗ 目标网站不可访问")
    except Exception as e:
        print(f"   ✗ 网络检查失败: {e}")

if __name__ == "__main__":
    diagnose_system()
```

### 2. 性能基准测试

```python
#!/usr/bin/env python3
# scripts/benchmark_performance.py

import time
import statistics
from contextlib import contextmanager
from src.utils.timer import Timer

@contextmanager
def benchmark(name):
    """性能测试上下文管理器"""
    times = []
    for _ in range(5):  # 运行5次取平均值
        with Timer() as t:
            yield
        times.append(t.duration)

    print(f"\n{name} 性能报告:")
    print(f"  平均: {statistics.mean(times):.2f}s")
    print(f"  最小: {min(times):.2f}s")
    print(f"  最大: {max(times):.2f}s")
    print(f"  中位数: {statistics.median(times):.2f}s")

def run_benchmarks():
    """运行性能基准测试"""
    print("=== 性能基准测试 ===")

    # 测试页面加载
    with benchmark("页面加载"):
        from src.steps.open_site import OpenSite
        step = OpenSite(config)
        step.execute()

    # 测试元素定位
    with benchmark("元素定位"):
        from src.utils.locator import Locator
        locator = Locator(page)
        locator.find_element("#prompt-input")

    # 测试内容验证
    with benchmark("内容验证"):
        from src.validation.image_validator import ImageValidator
        validator = ImageValidator({})
        validator.validate_basic("test_data/test_image.jpg")

if __name__ == "__main__":
    run_benchmarks()
```

---

## 📊 故障排查检查清单

### 执行前检查

- [ ] **环境准备**
  - [ ] Python 3.8+ 已安装
  - [ ] 虚拟环境已激活
  - [ ] 依赖包已完整安装
  - [ ] Playwright浏览器已安装

- [ ] **配置验证**
  - [ ] config.yaml 语法正确
  - [ ] 选择器配置准确
  - [ ] 超时设置合理
  - [ ] API密钥有效

- [ ] **网络连接**
  - [ ] 目标网站可访问
  - [ ] 代理配置正确（如需要）
  - [ ] DNS解析正常
  - [ ] 防火墙规则允许

### 执行中检查

- [ ] **资源监控**
  - [ ] CPU使用率 < 80%
  - [ ] 内存使用率 < 80%
  - [ ] 磁盘空间充足
  - [ ] 网络带宽充足

- [ ] **日志监控**
  - [ ] ERROR级别日志数 = 0
  - [ ] WARNING级别日志数 < 5
  - [ ] 关键步骤都有日志
  - [ ] 异常有详细堆栈

### 执行后检查

- [ ] **结果验证**
  - [ ] 测试报告生成成功
  - [ ] 截图/视频保存正常
  - [ ] 验证分数达标
  - [ ] 资源清理完成

- [ ] **性能分析**
  - [ ] 执行时间在预期内
  - [ ] 无明显性能退化
  - [ ] 内存使用正常
  - [ ] 并发执行稳定

---

## 🚨 应急响应流程

### 生产环境故障

1. **立即响应（5分钟内）**
   - 停止当前测试执行
   - 保留现场（日志、截图）
   - 通知相关人员

2. **快速诊断（15分钟内）**
   - 执行系统诊断脚本
   - 查看最近的错误日志
   - 确定故障范围

3. **临时方案（30分钟内）**
   - 切换到备用环境
   - 使用降级测试方案
   - 实施快速修复

4. **根本解决（2小时内）**
   - 深入分析根本原因
   - 实施永久解决方案
   - 更新文档和流程

### 性能紧急情况

1. **系统过载**
   ```bash
   # 立即降低并发
   killall -9 python  # 终止所有Python进程
   # 或
   pkill -f run_workflow_test.py

   # 清理资源
   rm -rf .cache/
   rm -rf tmp/
   ```

2. **内存泄漏**
   ```bash
   # 监控内存使用
   top -p <pid>
   # 或
   ps aux | grep python

   # 重启服务
   systemctl restart test-bot  # 如果是服务
   ```

3. **磁盘空间不足**
   ```bash
   # 清理旧文件
   find test_artifacts/ -type f -mtime +7 -delete
   find screenshots/ -name "*.png" -mtime +3 -delete
   find logs/ -name "*.log" -mtime +1 -delete
   ```

---

## 📞 获取支持

### 自助资源

1. **文档中心**
   - [测试流程指南](WORKFLOW_GUIDE.md)
   - [E2E测试指南](E2E_TESTING_GUIDE.md)
   - [API文档](../api/)

2. **工具脚本**
   - `scripts/validate_environment.py` - 环境验证
   - `scripts/diagnose_system.py` - 系统诊断
   - `scripts/benchmark_performance.py` - 性能测试

### 联系方式

- **紧急故障**：创建Issue并标记"urgent"
- **技术问题**：联系开发团队
- **环境问题**：联系运维团队
- **用例问题**：联系QA团队

### 信息收集模板

提交问题时请包含：

```markdown
## 问题描述
[简要描述遇到的问题]

## 环境信息
- OS: [操作系统版本]
- Python: [Python版本]
- 浏览器: [浏览器版本]

## 错误日志
[粘贴相关错误日志]

## 复现步骤
1. 执行命令: [命令]
2. 配置文件: [配置]
3. 预期结果: [预期]
4. 实际结果: [实际]

## 尝试过的解决方案
[列出已尝试的解决方案]
```

---

**指南版本**：v1.0
**最后更新**：2025-12-19
**维护团队**：测试开发团队
**下次更新**：新增故障类型时