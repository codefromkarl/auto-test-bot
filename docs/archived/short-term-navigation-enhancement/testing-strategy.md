# 测试策略和验证方法

## 概述

本文档描述了短期导航增强方案的全面测试策略，包括单元测试、集成测试、边界测试和性能测试。

## 测试目标

1. **功能正确性**：验证新增导航逻辑正常工作
2. **向后兼容性**：确保现有功能不受影响
3. **异常处理**：验证各种异常情况的处理
4. **性能指标**：确保导航时间在可接受范围内

## 测试层级

### 1. 单元测试

#### 测试范围
- 新增方法的功能验证
- 配置加载器的增强功能
- 错误处理逻辑

#### 关键测试用例

```python
class TestNavigationMethods:
    """导航方法单元测试"""

    @pytest.mark.asyncio
    async def test_create_button_navigation_success(self):
        """测试创建按钮导航成功场景"""

    @pytest.mark.asyncio
    async def test_create_button_navigation_failure(self):
        """测试创建按钮导航失败场景"""

    @pytest.mark.asyncio
    async def test_navigation_sequence_execution(self):
        """测试导航序列执行"""

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""

    @pytest.mark.asyncio
    async def test_wait_after_timing(self):
        """测试等待时间准确性"""
```

#### 运行命令
```bash
# 运行单元测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py -v

# 运行覆盖率测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py --cov=src/steps/navigate_to_text_image

# 运行性能测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py::TestPerformance -v
```

### 2. 集成测试

#### 测试场景
1. **完整流程测试**
2. **多策略切换测试**
3. **配置变更影响测试**

#### 测试环境准备
```python
# tests/integration/test_navigation_integration.py
class TestNavigationIntegration:

    @pytest.fixture
    async def test_browser(self):
        """准备测试浏览器环境"""
        browser = BrowserManager()
        await browser.setup()
        await browser.login()  # 如果需要
        yield browser
        await browser.cleanup()

    @pytest.fixture
    async def test_config(self):
        """准备测试配置"""
        config_loader = ConfigLoader('config/test_config.yaml')
        return config_loader.get_config()
```

#### 集成测试用例

```python
class TestNavigationIntegration:

    @pytest.mark.asyncio
    async def test_full_navigation_flow(self, test_browser, test_config):
        """测试完整导航流程"""
        # 1. 导航到AI创作页
        # 2. 尝试各种导航策略
        # 3. 验证最终到达文生图页
        # 4. 检查页面元素完整性

    @pytest.mark.asyncio
    async def test_strategy_fallback(self, test_browser, test_config):
        """测试策略回退机制"""
        # 模拟各种失败场景
        # 验证回退到下一个策略

    @pytest.mark.asyncio
    async def test_configuration_driven_behavior(self, test_browser):
        """测试配置驱动的行为"""
        # 测试不同配置下的行为差异
        # 验证配置变更的效果
```

#### 运行集成测试
```bash
# 运行集成测试
python -m pytest tests/integration/ -v -s

# 运行特定集成测试
python -m pytest tests/integration/test_navigation_integration.py::TestNavigationIntegration::test_full_navigation_flow -v

# 运行并行集成测试
python -m pytest tests/integration/ -n auto
```

### 3. 边界测试

#### 测试场景

1. **网络延迟测试**
   ```python
   async def test_network_latency(self):
       """测试网络延迟情况"""
       # 模拟慢网络
       # 验证超时处理
   ```

2. **元素不存在测试**
   ```python
   async def test_missing_elements(self):
       """测试页面元素不存在"""
       # 模拟创建按钮不存在
       # 模拟文生图选项不存在
   ```

3. **页面加载异常测试**
   ```python
   async def test_page_load_issues(self):
       """测试页面加载异常"""
       # 模拟页面加载缓慢
       # 模拟页面加载失败
   ```

4. **并发访问测试**
   ```python
   async def test_concurrent_access(self):
       """测试并发访问"""
       # 多个导航操作同时执行
   ```

### 4. 性能测试

#### 性能指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 导航成功时间 | < 3秒 | 计时器测量 |
| 单次点击响应 | < 500ms | 浏览器API测量 |
| 页面加载完成 | < 2秒 | DOM Ready事件 |
| 内存使用增长 | < 50MB | 内存分析工具 |

#### 性能测试用例

```python
class TestPerformance:

    @pytest.mark.asyncio
    async def test_navigation_performance(self):
        """测试导航性能"""
        start_time = time.time()
        # 执行导航
        end_time = time.time()
        assert end_time - start_time < 3.0

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """测试内存使用"""
        # 测量操作前后内存使用
        # 确保没有内存泄漏

    @pytest.mark.asyncio
    async def test_stress_testing(self):
        """压力测试"""
        # 重复执行导航操作
        # 验证性能稳定性
```

## 测试数据管理

### 1. 测试配置文件

```yaml
# tests/fixtures/test_navigation_config.yaml
test:
  flow_name: "test_navigation"
  url: "http://localhost:9020/#/home/dashboard"
  timeout: 10000
  element_timeout: 5000

locators:
  test_create_button:
    - "[data-testid='test-create-button']"
    - ".test-create-btn"

  test_text_image_option:
    - "[data-testid='test-text-image']"
    - ".test-text-image"

navigation_sequences:
  test_sequence:
    description: "测试序列"
    steps:
      - locator: "test_create_button"
        wait_after: 100
      - locator: "test_text_image_option"
        wait_after: 200
```

### 2. 测试数据生成

```python
# tests/fixtures/data_generator.py
class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def create_test_config(custom_config=None):
        """创建测试配置"""
        base_config = {
            'locators': {...},
            'navigation_sequences': {...}
        }
        if custom_config:
            base_config.update(custom_config)
        return base_config

    @staticmethod
    def create_mock_browser_page():
        """创建模拟浏览器页面"""
        page = MagicMock()
        # 设置常用的模拟返回值
        page.locator.return_value.wait_for.return_value = None
        page.locator.return_value.click.return_value = None
        return page
```

## 自动化测试流程

### 1. CI/CD 集成

```yaml
# .github/workflows/test-navigation-enhancement.yml
name: Test Navigation Enhancement

on:
  push:
    paths:
      - 'src/steps/navigate_to_text_image.py'
      - 'config/data_testid_config.yaml'
  pull_request:
    paths:
      - 'src/steps/navigate_to_text_image.py'
      - 'config/data_testid_config.yaml'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run unit tests
        run: python -m pytest tests/test_navigate_to_text_image_enhanced.py --cov=src/steps/navigate_to_text_image
      - name: Run integration tests
        run: python -m pytest tests/integration/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### 2. 测试报告生成

```python
# scripts/generate_test_report.py
import pytest
import json
from datetime import datetime

def generate_test_report():
    """生成测试报告"""
    result = pytest.main([
        'tests/',
        '--json=tests/report.json',
        '--html=tests/report.html',
        '--self-contained-html'
    ])

    # 处理测试结果
    with open('tests/report.json', 'r') as f:
        report_data = json.load(f)

    # 生成摘要报告
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': report_data['summary']['total'],
        'passed': report_data['summary']['passed'],
        'failed': report_data['summary']['failed'],
        'success_rate': report_data['summary']['passed'] / report_data['summary']['total'] * 100
    }

    with open('tests/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"测试完成，成功率: {summary['success_rate']:.2f}%")

if __name__ == "__main__":
    generate_test_report()
```

## 测试环境管理

### 1. 测试环境配置

```python
# tests/conftest.py
import pytest
import asyncio
from browser import BrowserManager
from utils.config_loader import ConfigLoader

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_browser():
    """测试浏览器环境"""
    browser = BrowserManager(headless=True)  # 无头模式
    await browser.setup()
    yield browser
    await browser.cleanup()

@pytest.fixture
def test_config():
    """测试配置"""
    config_loader = ConfigLoader('tests/fixtures/test_config.yaml')
    return config_loader
```

### 2. 测试数据清理

```python
# tests/helpers/cleanup.py
class TestCleanup:
    """测试清理工具"""

    @staticmethod
    async def cleanup_browser_state(browser):
        """清理浏览器状态"""
        await browser.clear_cookies()
        await browser.clear_local_storage()
        await browser.clear_session_storage()

    @staticmethod
    async def cleanup_test_files():
        """清理测试文件"""
        import os
        import glob

        # 清理测试报告文件
        report_files = glob.glob('tests/reports/*.tmp')
        for file in report_files:
            os.remove(file)

    @staticmethod
    async def reset_config():
        """重置配置到默认状态"""
        # 恢复配置文件的备份
        pass
```

## 测试执行脚本

### 1. 完整测试脚本

```bash
#!/bin/bash
# scripts/run_all_tests.sh

echo "开始执行导航增强方案测试..."

# 1. 代码静态检查
echo "1. 执行代码静态检查..."
flake8 src/steps/navigate_to_text_image.py
pylint src/steps/navigate_to_text_image.py

# 2. 单元测试
echo "2. 执行单元测试..."
python -m pytest tests/test_navigate_to_text_image_enhanced.py -v --cov=src/steps/navigate_to_text_image

# 3. 集成测试
echo "3. 执行集成测试..."
python -m pytest tests/integration/ -v -s

# 4. 性能测试
echo "4. 执行性能测试..."
python -m pytest tests/performance/ -v

# 5. 生成测试报告
echo "5. 生成测试报告..."
python scripts/generate_test_report.py

echo "测试完成！查看报告：tests/report.html"
```

### 2. 快速验证脚本

```bash
#!/bin/bash
# scripts/quick_test.sh

echo "快速验证导航增强功能..."

# 只运行核心功能测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py::TestNavigateToTextImageEnhanced::test_navigate_via_create_button_success -v

# 验证配置文件
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))"

echo "快速验证完成！"
```

## 质量保证检查清单

### 功能检查
- [ ] 创建按钮定位器正确
- [ ] 文生图选项定位器正确
- [ ] 导航序列执行正常
- [ ] 等待时间设置合理
- [ ] 超时处理有效

### 兼容性检查
- [ ] 现有导航逻辑未受影响
- [ ] 配置文件向后兼容
- [ ] API接口保持不变

### 性能检查
- [ ] 导航时间在可接受范围内
- [ ] 内存使用无异常增长
- [ ] 无明显性能回退

### 安全检查
- [ ] 没有新的安全漏洞
- [ ] 敏感信息正确处理
- [ ] 错误信息不泄露敏感数据

## 最后更新

2025-12-17