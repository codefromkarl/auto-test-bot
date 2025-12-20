# 详细实施指南

## 概述

本文档提供了短期导航增强方案的详细实施步骤，确保在最小风险的前提下完成功能增强。

## 准备工作

### 1. 环境准备

```bash
# 1. 创建开发分支
git checkout -b feature/navigation-enhancement-short-term

# 2. 备份关键文件
cp config/data_testid_config.yaml config/data_testid_config.yaml.backup
cp src/steps/navigate_to_text_image.py src/steps/navigate_to_text_image.py.backup

# 3. 安装开发依赖（如果需要）
pip install pytest pytest-cov pytest-asyncio
```

### 2. 工具验证

```bash
# 验证Python环境
python --version  # 应该是3.8+

# 验证配置文件语法
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))"

# 运行现有测试确保基线正常
python -m pytest tests/ -k "navigate_to_text_image" --tb=short
```

## 详细实施步骤

### 步骤1：配置文件更新（预计30分钟）

#### 1.1 备份和验证

```bash
# 确认当前配置正常
python -c "
from utils.config_loader import ConfigLoader
config = ConfigLoader('config/data_testid_config.yaml')
print('配置加载成功')
print(f'现有定位器数量: {len(config.get(\"locators\", {}))}')
"
```

#### 1.2 添加创建相关定位器

```bash
# 使用编辑器打开配置文件
vim config/data_testid_config.yaml

# 或者使用sed命令自动添加（谨慎使用）
sed -i '/nav_ai_tools_tab:/a\
\
  # 创建相关定位器\
  create_button:\
    - "[data-testid=\"create-button\"]"\
    - "[data-testid=\"add-button\"]"\
    - "button:has-text(\'+\')"\
    - ".create-btn"\
    - ".add-btn"\
\
  text_image_option:\
    - "[data-testid=\"text-image-option\"]"\
    - "[data-testid=\"create-text-image\"]"\
    - "menuitem:has-text(\"文生图\")"\
    - ".menu-item:has-text(\"文生图\")"\
\
  text_image_in_tools:\
    - "[data-testid=\"text-image-in-tools\"]"\
    - "menuitem:has-text(\"文生图\")"\
    - ".tool-item:has-text(\"文生图\")"' config/data_testid_config.yaml
```

#### 1.3 添加导航序列配置

```bash
# 在文件末尾添加导航序列
cat >> config/data_testid_config.yaml << 'EOF'

# 导航序列配置
navigation_sequences:
  create_text_image_flow:
    description: "通过创建按钮进入文生图"
    steps:
      - locator: "create_button"
        wait_after: 500  # 等待菜单展开（毫秒）
        timeout: 5000    # 元素等待超时（毫秒）
      - locator: "text_image_option"
        wait_after: 1000 # 等待页面跳转（毫秒）
        timeout: 5000    # 元素等待超时（毫秒）

  ai_tools_text_image_flow:
    description: "通过AI工具进入文生图"
    steps:
      - locator: "nav_ai_tools_tab"
        wait_after: 1000  # 等待页面加载（毫秒）
        timeout: 10000   # 元素等待超时（毫秒）
      - locator: "text_image_in_tools"
        wait_after: 1000 # 等待页面跳转（毫秒）
        timeout: 5000    # 元素等待超时（毫秒）
EOF
```

#### 1.4 验证配置文件

```bash
# 验证YAML语法
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))"

# 验证新配置加载
python -c "
from utils.config_loader import ConfigLoader
config = ConfigLoader('config/data_testid_config.yaml')
sequence = config.get_navigation_sequence('create_text_image_flow')
print(f'创建序列配置: {sequence}')
locators = config.get('locators', {})
print(f'create_button定位器: {locators.get(\"create_button\", [])}')
"
```

### 步骤2：代码实现（预计1.5小时）

#### 2.1 修改导航步骤文件

```bash
# 创建一个新的导航方法文件作为备份
cp src/steps/navigate_to_text_image.py src/steps/navigate_to_text_image_enhanced.py

# 编辑文件
vim src/steps/navigate_to_text_image.py
```

#### 2.2 添加新方法

在 `NavigateToTextToImageStep` 类中添加以下方法：

```python
async def _navigate_via_create_button(self) -> bool:
    """
    通过创建按钮进入文生图
    业务逻辑：先点击加号展开创建菜单，再选择文生图选项

    Returns:
        bool: 导航是否成功
    """
    try:
        # 获取导航序列配置
        sequence = self.config.get_navigation_sequence('create_text_image_flow')
        if not sequence:
            self.logger.warning("未找到创建文生图的导航序列配置")
            return False

        return await self._execute_navigation_sequence(sequence)

    except Exception as e:
        self.logger.error(f"通过创建按钮导航失败: {str(e)}")
        return False

async def _execute_navigation_sequence(self, sequence: Dict[str, Any]) -> bool:
    """
    执行导航序列

    Args:
        sequence: 导航序列配置

    Returns:
        bool: 执行是否成功
    """
    steps = sequence.get('steps', [])
    if not steps:
        self.logger.error("导航序列中没有配置步骤")
        return False

    import asyncio

    for i, step in enumerate(steps):
        locator_name = step.get('locator')
        wait_after = step.get('wait_after', 0)
        timeout = step.get('timeout', 5000)

        if not locator_name:
            self.logger.error(f"步骤 {i} 缺少 locator 配置")
            return False

        # 执行点击操作
        if not await self._click_locator_with_timeout(locator_name, timeout):
            self.logger.error(f"步骤 {i} 点击 {locator_name} 失败")
            return False

        # 等待指定的毫秒数
        if wait_after > 0:
            await asyncio.sleep(wait_after / 1000)
            self.logger.debug(f"等待 {wait_after}ms")

    return True

async def _click_locator_with_timeout(self, locator_name: str, timeout: int) -> bool:
    """
    使用指定的超时时间点击定位器

    Args:
        locator_name: 定位器名称
        timeout: 超时时间（毫秒）

    Returns:
        bool: 点击是否成功
    """
    # 优先使用 MetricsHybridLocator
    if self.locator:
        try:
            if await self.locator.click(locator_name, timeout=timeout):
                self.logger.info(f"使用 locator 成功点击: {locator_name}")
                return True
        except Exception as e:
            self.logger.debug(f"locator 点击 {locator_name} 失败: {e}")

    # 回退到页面直接定位
    try:
        locators_config = self.config.get('locators', {})
        selectors = locators_config.get(locator_name, [])

        if not selectors:
            self.logger.error(f"未找到定位器配置: {locator_name}")
            return False

        for selector in selectors:
            try:
                element = self.browser.page.locator(selector)
                await element.wait_for(state='visible', timeout=timeout)
                await element.click()
                self.logger.info(f"使用选择器成功点击: {selector}")
                return True
            except Exception:
                continue

    except Exception as e:
        self.logger.debug(f"直接定位点击 {locator_name} 失败: {e}")

    return False
```

#### 2.3 修改现有方法

修改 `_navigate_from_ai_create` 方法：

```python
async def _navigate_from_ai_create(self, attempted_methods: Optional[list] = None) -> bool:
    """
    从AI创作页导航到文生图页
    增强版：支持多种导航策略

    Args:
        attempted_methods: 尝试过的方法列表

    Returns:
        bool: 导航是否成功
    """
    # 先做快速探测：若当前页完全不存在"文生图"文案，优先走创建流程
    text_image_text_detected = False
    try:
        await self.browser.page.wait_for_function(
            "() => document.body && document.body.innerText && document.body.innerText.includes('文生图')",
            timeout=2000,
        )
        text_image_text_detected = True
    except Exception:
        self.logger.info("当前页未发现"文生图"文案，将优先尝试创建流程")

    navigation_attempts = [
        # 策略1：直接文生图入口（当检测到文生图文本时优先）
        ("直接文生图", lambda: self._click_text_to_image_direct()),

        # 策略2：创建按钮流程（当未检测到文生图文本时优先）
        ("创建按钮文生图", lambda: self._navigate_via_create_button()),

        # 策略3：AI工具 -> 文生图（现有兜底逻辑）
        ("AI工具->文生图", lambda: self._navigate_via_ai_tools()),

        # 策略4：直接URL导航（最后兜底）
        ("直接URL导航", lambda: self._navigate_direct()),
    ]

    # 如果没有检测到文生图文本，调整优先级
    if not text_image_text_detected:
        navigation_attempts = [
            ("创建按钮文生图", lambda: self._navigate_via_create_button()),
            ("直接文生图", lambda: self._click_text_to_image_direct()),
            ("AI工具->文生图", lambda: self._navigate_via_ai_tools()),
            ("直接URL导航", lambda: self._navigate_direct()),
        ]

    for attempt_name, attempt_func in navigation_attempts:
        try:
            if attempted_methods is not None:
                attempted_methods.append(attempt_name)
            self.logger.info(f"尝试导航方式: {attempt_name}")
            if await attempt_func():
                self.logger.info(f"导航成功，使用方式: {attempt_name}")
                return True
        except Exception as e:
            self.logger.debug(f"导航方式 {attempt_name} 失败: {str(e)}")
            continue

    return False

async def _click_text_to_image_direct(self) -> bool:
    """
    直接点击文生图入口（抽取现有逻辑）

    Returns:
        bool: 点击是否成功
    """
    # 优先使用 locator
    if self.locator:
        try:
            if await self.locator.click('nav_text_image_tab', timeout=5000):
                self.logger.info("直接定位器点击文生图成功")
                return True
        except Exception as e:
            self.logger.debug(f"直接定位器点击文生图失败: {e}")

    # 回退到原有的各种尝试方法
    return await self._try_legacy_text_image_methods()
```

#### 2.4 增强配置加载器

修改 `src/utils/config_loader.py`：

```python
def get_navigation_sequence(self, sequence_name: str) -> Dict[str, Any]:
    """
    获取导航序列配置

    Args:
        sequence_name: 序列名称

    Returns:
        Dict[str, Any]: 序列配置，如果不存在返回空字典
    """
    sequences = self.config.get('navigation_sequences', {})
    return sequences.get(sequence_name, {})

def validate_navigation_sequences(self) -> List[str]:
    """
    验证导航序列配置的有效性

    Returns:
        List[str]: 验证错误列表，空列表表示验证通过
    """
    errors = []
    sequences = self.config.get('navigation_sequences', {})

    for sequence_name, sequence_config in sequences.items():
        if not isinstance(sequence_config, dict):
            errors.append(f"导航序列 {sequence_name} 必须是字典类型")
            continue

        steps = sequence_config.get('steps')
        if not steps or not isinstance(steps, list):
            errors.append(f"导航序列 {sequence_name} 必须包含 steps 数组")
            continue

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"导航序列 {sequence_name} 步骤 {i} 必须是字典类型")
                continue

            if 'locator' not in step:
                errors.append(f"导航序列 {sequence_name} 步骤 {i} 缺少 locator 字段")

    return errors
```

### 步骤3：单元测试（预计30分钟）

#### 3.1 创建测试文件

```bash
# 创建测试文件
touch tests/test_navigate_to_text_image_enhanced.py
```

#### 3.2 编写核心测试用例

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from steps.navigate_to_text_image import NavigateToTextToImageStep

class TestNavigateToTextImageEnhanced:

    @pytest.fixture
    def mock_browser(self):
        browser = MagicMock()
        browser.page = MagicMock()
        return browser

    @pytest.fixture
    def mock_config(self):
        config = {
            'locators': {
                'create_button': ['[data-testid="create-button"]'],
                'text_image_option': ['[data-testid="text-image-option"]'],
            },
            'navigation_sequences': {
                'create_text_image_flow': {
                    'description': '测试序列',
                    'steps': [
                        {'locator': 'create_button', 'wait_after': 500},
                        {'locator': 'text_image_option', 'wait_after': 1000}
                    ]
                }
            }
        }
        return config

    @pytest.fixture
    def navigation_step(self, mock_browser, mock_config):
        step = NavigateToTextToImageStep(mock_browser, mock_config)
        return step

    @pytest.mark.asyncio
    async def test_navigate_via_create_button_success(self, navigation_step):
        """测试通过创建按钮导航成功"""
        # Mock 配置加载
        navigation_step.config.get_navigation_sequence = MagicMock(return_value={
            'steps': [
                {'locator': 'create_button', 'wait_after': 500},
                {'locator': 'text_image_option', 'wait_after': 1000}
            ]
        })

        # Mock 点击成功
        navigation_step._click_locator_with_timeout = AsyncMock(return_value=True)

        # 执行测试
        result = await navigation_step._navigate_via_create_button()

        # 验证结果
        assert result is True
        assert navigation_step._click_locator_with_timeout.call_count == 2

    @pytest.mark.asyncio
    async def test_navigation_sequence_execution(self, navigation_step):
        """测试导航序列执行"""
        sequence = {
            'steps': [
                {'locator': 'create_button', 'wait_after': 500},
                {'locator': 'text_image_option', 'wait_after': 0}
            ]
        }

        # Mock 点击成功
        navigation_step._click_locator_with_timeout = AsyncMock(return_value=True)

        # 执行测试
        result = await navigation_step._execute_navigation_sequence(sequence)

        # 验证结果
        assert result is True
        assert navigation_step._click_locator_with_timeout.call_count == 2
```

#### 3.3 运行测试

```bash
# 运行新创建的测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py -v

# 运行覆盖率测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py --cov=src.steps.navigate_to_text_image --cov-report=html
```

### 步骤4：集成测试（预计30分钟）

#### 4.1 创建集成测试脚本

```python
# scripts/test_navigation_integration.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser import BrowserManager
from utils.config_loader import ConfigLoader
from steps.navigate_to_text_image import NavigateToTextToImageStep

async def test_integration():
    """集成测试主函数"""
    print("开始集成测试...")

    # 1. 加载配置
    config = ConfigLoader('config/data_testid_config.yaml')
    print("✓ 配置加载成功")

    # 2. 验证新配置
    create_sequence = config.get_navigation_sequence('create_text_image_flow')
    assert create_sequence, "创建序列配置不存在"
    print("✓ 创建序列配置验证成功")

    # 3. 验证定位器
    locators = config.get('locators', {})
    assert 'create_button' in locators, "create_button 定位器不存在"
    assert 'text_image_option' in locators, "text_image_option 定位器不存在"
    print("✓ 定位器配置验证成功")

    # 4. 初始化组件
    browser = BrowserManager()
    step = NavigateToTextToImageStep(browser, config)
    print("✓ 组件初始化成功")

    # 5. 验证方法存在
    assert hasattr(step, '_navigate_via_create_button'), "新增方法不存在"
    assert hasattr(step, '_execute_navigation_sequence'), "序列执行方法不存在"
    print("✓ 新增方法验证成功")

    print("所有集成测试通过！")

if __name__ == "__main__":
    asyncio.run(test_integration())
```

#### 4.2 运行集成测试

```bash
# 运行集成测试
python scripts/test_navigation_integration.py

# 运行现有功能回归测试
python -m pytest tests/ -k "navigate" --tb=short
```

### 步骤5：性能验证（预计15分钟）

#### 5.1 性能测试脚本

```python
# scripts/performance_test.py
import time
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_loader import ConfigLoader

async def test_performance():
    """性能测试"""
    print("开始性能测试...")

    # 1. 配置加载性能
    start_time = time.time()
    for i in range(100):
        config = ConfigLoader('config/data_testid_config.yaml')
        config.get_navigation_sequence('create_text_image_flow')
    load_time = (time.time() - start_time) / 100
    print(f"配置加载平均时间: {load_time*1000:.2f}ms")
    assert load_time < 0.01, f"配置加载过慢: {load_time}s"

    # 2. 验证性能
    start_time = time.time()
    for i in range(100):
        config = ConfigLoader('config/data_testid_config.yaml')
        config.validate_navigation_sequences()
    validate_time = (time.time() - start_time) / 100
    print(f"配置验证平均时间: {validate_time*1000:.2f}ms")
    assert validate_time < 0.01, f"配置验证过慢: {validate_time}s"

    print("性能测试通过！")

if __name__ == "__main__":
    asyncio.run(test_performance())
```

#### 5.2 运行性能测试

```bash
python scripts/performance_test.py
```

### 步骤6：文档更新（预计15分钟）

#### 6.1 更新API文档

```markdown
# src/steps/navigate_to_text_image.md

## 新增方法

### _navigate_via_create_button()

通过创建按钮进入文生图的新导航策略。

**返回值**: bool - 导航是否成功

### _execute_navigation_sequence(sequence)

执行导航序列的核心方法。

**参数**:
- sequence (Dict): 导航序列配置

**返回值**: bool - 执行是否成功

### _click_locator_with_timeout(locator_name, timeout)

使用指定超时时间的定位器点击方法。

**参数**:
- locator_name (str): 定位器名称
- timeout (int): 超时时间（毫秒）

**返回值**: bool - 点击是否成功
```

#### 6.2 更新配置说明

```markdown
# config/data_testid_config.md

## 新增配置项

### navigation_sequences

导航序列配置，支持多步骤导航流程。

**示例**:
```yaml
navigation_sequences:
  create_text_image_flow:
    description: "创建文生图流程"
    steps:
      - locator: "create_button"
        wait_after: 500
        timeout: 5000
```

### 新增定位器

- `create_button`: 创建按钮定位器
- `text_image_option`: 文生图选项定位器
- `text_image_in_tools`: AI工具中的文生图选项定位器
```

## 验证检查点

每个步骤完成后都要进行以下检查：

### 1. 配置文件检查
```bash
# 语法检查
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))"

# 加载检查
python -c "
from utils.config_loader import ConfigLoader
config = ConfigLoader('config/data_testid_config.yaml')
print(f'定位器数量: {len(config.get(\"locators\", {}))}')
print(f'序列数量: {len(config.get(\"navigation_sequences\", {}))}')
"
```

### 2. 代码检查
```bash
# 语法检查
python -m py_compile src/steps/navigate_to_text_image.py

# 静态检查
flake8 src/steps/navigate_to_text_image.py --max-line-length=100

# 导入检查
python -c "from steps.navigate_to_text_image import NavigateToTextToImageStep; print('导入成功')"
```

### 3. 功能检查
```bash
# 运行相关测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py -v

# 回归测试
python -m pytest tests/ -k "navigate" --tb=short
```

## 常见问题处理

### 问题1：配置文件语法错误

**症状**: YAML解析错误
**解决**:
```bash
# 检查YAML语法
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))"

# 恢复备份
cp config/data_testid_config.yaml.backup config/data_testid_config.yaml
```

### 问题2：导入错误

**症状**: ImportError: cannot import name
**解决**:
```bash
# 检查Python路径
python -c "import sys; print(sys.path)"

# 检查文件存在
ls -la src/steps/navigate_to_text_image.py
```

### 问题3：测试失败

**症状**: 测试用例执行失败
**解决**:
```bash
# 详细错误信息
python -m pytest tests/test_navigate_to_text_image_enhanced.py -v -s

# 逐个测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py::TestNavigateToTextImageEnhanced::test_navigate_via_create_button_success -v -s
```

## 完成标准

项目完成需要满足以下标准：

1. **功能完整性**:
   - [ ] 所有新增方法实现
   - [ ] 配置文件更新完成
   - [ ] 导航策略生效

2. **质量保证**:
   - [ ] 所有单元测试通过
   - [ ] 集成测试通过
   - [ ] 性能测试通过

3. **文档完整**:
   - [ ] API文档更新
   - [ ] 配置说明更新
   - [ ] 实施记录完整

4. **向后兼容**:
   - [ ] 现有功能不受影响
   - [ ] 配置文件向后兼容
   - [ ] API接口保持不变

## 提交和部署

### 1. 代码提交

```bash
# 添加变更
git add config/data_testid_config.yaml src/steps/navigate_to_text_image.py src/utils/config_loader.py

# 提交变更
git commit -m "feat: 添加创建按钮文生图导航支持

- 新增创建按钮和文生图选项定位器
- 实现多策略导航机制
- 支持导航序列配置
- 增强配置加载器功能

Closes: 导航增强需求"

# 推送分支
git push origin feature/navigation-enhancement-short-term
```

### 2. 创建Pull Request

```markdown
## 变更概述

本次变更实现了通过创建按钮进入文生图的新导航策略，解决了现有导航逻辑无法适应创建流程的问题。

## 主要变更

1. **配置文件增强**: 添加创建相关定位器和导航序列
2. **代码逻辑扩展**: 新增多策略导航机制
3. **测试覆盖**: 完整的单元测试和集成测试

## 测试结果

- 单元测试: ✅ 100% 通过
- 集成测试: ✅ 全部通过
- 性能测试: ✅ 无性能回退

## 审查要点

1. 配置文件语法正确性
2. 新增方法的异常处理
3. 向后兼容性保证

## 部署注意事项

- 无需数据库迁移
- 向后兼容现有配置
- 建议在测试环境先验证
```

## 最后更新

2025-12-17