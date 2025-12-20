# 代码实现示例

## 概述

本文档提供了实现短期导航增强方案的核心代码示例，包括新增方法和现有方法的修改。

## 主要修改文件

- `src/steps/navigate_to_text_image.py` - 主要导航逻辑
- `src/utils/config_loader.py` - 配置加载增强
- `tests/test_navigate_to_text_image_enhanced.py` - 测试用例

## 核心代码实现

### 1. 新增导航方法

#### `navigate_to_text_image.py` 新增方法

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

    for step in steps:
        locator_name = step.get('locator')
        wait_after = step.get('wait_after', 0)
        timeout = step.get('timeout', 5000)

        if not locator_name:
            self.logger.error("导航步骤中缺少 locator 配置")
            return False

        # 执行点击操作
        if not await self._click_locator_with_timeout(locator_name, timeout):
            self.logger.error(f"点击 {locator_name} 失败")
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
        locators_config = self.config.get_enhanced_locators()
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

async def _try_legacy_text_image_methods(self) -> bool:
    """
    尝试传统的文生图点击方法

    Returns:
        bool: 点击是否成功
    """
    navigation_attempts = [
        ("卡片文生图", lambda: self._click_text_to_image_card()),
        ("文生图按钮", lambda: self._click_by_role("button", "文生图")),
        ("文生图链接", lambda: self._click_by_text("文生图")),
        ("开始创作", lambda: self._click_by_text("开始创作文生图")),
    ]

    for attempt_name, attempt_func in navigation_attempts:
        try:
            self.logger.info(f"尝试传统导航方式: {attempt_name}")
            if await attempt_func():
                self.logger.info(f"传统导航成功: {attempt_name}")
                return True
        except Exception as e:
            self.logger.debug(f"传统导航方式 {attempt_name} 失败: {str(e)}")
            continue

    return False
```

### 2. 修改现有方法

#### 修改 `_navigate_from_ai_create` 方法

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
```

### 3. 配置加载器增强

#### `config_loader.py` 新增方法

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

def get_enhanced_locators(self) -> Dict[str, List[str]]:
    """
    获取增强版定位器配置

    Returns:
        Dict[str, List[str]]: 定位器配置字典
    """
    # 基础定位器配置
    locators = self.config.get('locators', {}).copy()

    # 合并增强配置（如果存在）
    enhanced_locators = self.config.get('enhanced_locators', {})
    for name, selectors in enhanced_locators.items():
        if name in locators:
            # 合并选择器，增强配置在前
            locators[name] = selectors + locators[name]
        else:
            locators[name] = selectors

    return locators

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

            if 'wait_after' in step and not isinstance(step['wait_after'], int):
                errors.append(f"导航序列 {sequence_name} 步骤 {i} wait_after 必须是整数")

            if 'timeout' in step and not isinstance(step['timeout'], int):
                errors.append(f"导航序列 {sequence_name} 步骤 {i} timeout 必须是整数")

    return errors
```

## 测试用例示例

### `test_navigate_to_text_image_enhanced.py`

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

    def test_config_loader_navigation_sequence(self):
        """测试配置加载器导航序列读取"""
        from utils.config_loader import ConfigLoader

        config = ConfigLoader({
            'navigation_sequences': {
                'test_sequence': {
                    'description': '测试序列',
                    'steps': [
                        {'locator': 'test_button'}
                    ]
                }
            }
        })

        sequence = config.get_navigation_sequence('test_sequence')
        assert sequence['description'] == '测试序列'
        assert len(sequence['steps']) == 1
        assert sequence['steps'][0]['locator'] == 'test_button'

    def test_config_loader_validation(self):
        """测试配置验证"""
        from utils.config_loader import ConfigLoader

        # 有效配置
        config = ConfigLoader({
            'navigation_sequences': {
                'valid_sequence': {
                    'steps': [
                        {'locator': 'button', 'wait_after': 500, 'timeout': 5000}
                    ]
                }
            }
        })

        errors = config.validate_navigation_sequences()
        assert len(errors) == 0

        # 无效配置
        config = ConfigLoader({
            'navigation_sequences': {
                'invalid_sequence': 'not_a_dict'
            }
        })

        errors = config.validate_navigation_sequences()
        assert len(errors) > 0
```

## 最佳实践

### 1. 错误处理

```python
async def _execute_navigation_sequence(self, sequence: Dict[str, Any]) -> bool:
    """执行导航序列 - 完整错误处理版本"""
    try:
        steps = sequence.get('steps', [])
        if not steps:
            self.logger.error("导航序列中没有配置步骤")
            return False

        for i, step in enumerate(steps):
            locator_name = step.get('locator')
            if not locator_name:
                self.logger.error(f"步骤 {i} 缺少 locator 配置")
                return False

            # 执行步骤
            if not await self._click_locator_with_timeout(locator_name, 5000):
                self.logger.error(f"步骤 {i} 点击 {locator_name} 失败")
                return False

            # 等待
            wait_after = step.get('wait_after', 0)
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)

        return True

    except Exception as e:
        self.logger.error(f"执行导航序列异常: {str(e)}")
        return False
```

### 2. 性能优化

```python
# 使用缓存优化配置读取
class NavigateToTextToImageStep:
    def __init__(self, browser, config, locator=None):
        self.browser = browser
        self.config = config
        self.locator = locator
        self._sequence_cache = {}  # 缓存导航序列

    def _get_cached_sequence(self, sequence_name: str) -> Dict:
        """获取缓存的导航序列"""
        if sequence_name not in self._sequence_cache:
            self._sequence_cache[sequence_name] = self.config.get_navigation_sequence(sequence_name)
        return self._sequence_cache[sequence_name]
```

### 3. 调试支持

```python
# 添加详细的调试日志
async def _click_locator_with_timeout(self, locator_name: str, timeout: int) -> bool:
    """点击定位器 - 带调试版本"""
    self.logger.debug(f"尝试点击定位器: {locator_name}, 超时: {timeout}ms")

    if self.locator:
        try:
            start_time = asyncio.get_event_loop().time()
            if await self.locator.click(locator_name, timeout=timeout):
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                self.logger.debug(f"locator 点击成功: {locator_name}, 耗时: {elapsed:.2f}ms")
                return True
        except Exception as e:
            self.logger.debug(f"locator 点击失败: {locator_name}, 错误: {e}")

    return False
```

## 最后更新

2025-12-17