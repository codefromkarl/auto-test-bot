# Data-TestId 元素定位策略

## 策略概述

基于 Playwright 的测试机器人应该采用分层定位策略，优先使用语义化的 `data-testid`，辅以其他稳定的定位方式。

## 1. 定位优先级

### 第一优先级：业务语义化的 data-testid
```yaml
# 语义化的业务标识
prompt_input: "data-testid=prompt-input"
generate_image_button: "data-testid=generate-image-button"
image_result: "data-testid=image-result"
loading_indicator: "data-testid=loading-indicator"
```

### 第二优先级：ARIA 属性
```yaml
# 可访问性属性
submit_button: "role=button[name='生成图片']"
prompt_textarea: "role=textbox[name*='提示词']"
```

### 第三优先级：稳定的 CSS 选择器
```yaml
# 结合组件类名的选择器
prompt_area: ".arco-textarea[data-testid*=prompt]"
result_container: ".result-section[data-testid*=result]"
```

### 第四优先级：文本定位（谨慎使用）
```yaml
# 仅在文本相对稳定的场景使用
nav_ai_create: "text=AI创作"
nav_text_image: "text=文生图"
```

## 2. Data-TestId 命名规范

### 2.1 命名约定

```
{feature}_{component}_{action/state}

示例：
- text_image_generate_button
- image_result_container
- loading_spinner
- prompt_textarea
```

### 2.2 分类标准

#### 输入类组件
```
{page}_prompt_input
{page}_text_field
{page}_textarea
```

#### 按钮类组件
```
{page}_{action}_button
{page}_{action}_btn
{page}_submit_button
```

#### 结果展示类
```
{page}_{type}_result
{page}_{type}_container
{page}_{type}_display
```

#### 状态指示器
```
{page}_loading_spinner
{page}_loading_indicator
{page}_error_message
{page}_success_message
```

#### 导航和布局
```
nav_{page}_tab
{page}_section
{page}_header
{page}_sidebar
```

## 3. 测试机器人适配策略

### 3.1 创建定位器管理器

```python
class DataTestIdLocator:
    """基于 data-testid 的元素定位器"""

    def __init__(self, page):
        self.page = page

    def get_element(self, testid: str, timeout: int = 10000):
        """通过 data-testid 获取元素"""
        return self.page.locator(f"[data-testid='{testid}']", timeout=timeout)

    def get_element_contains(self, testid_part: str, timeout: int = 10000):
        """通过包含的 data-testid 部分获取元素"""
        return self.page.locator(f"[data-testid*='{testid_part}']", timeout=timeout)

    def wait_for_element(self, testid: str, state="visible", timeout=10000):
        """等待元素达到指定状态"""
        return self.page.wait_for_selector(
            f"[data-testid='{testid}']",
            state=state,
            timeout=timeout
        )
```

### 3.2 混合定位策略

```python
class HybridLocator:
    """混合定位策略 - 结合 data-testid 和其他方式"""

    def __init__(self, page):
        self.page = page
        self.data_testid_locator = DataTestIdLocator(page)

    async def locate_prompt_input(self):
        """定位提示词输入框的多种方式"""
        strategies = [
            lambda: self.data_testid_locator.get_element("prompt-textarea"),
            lambda: self.page.locator("textarea[placeholder*='提示']"),
            lambda: self.page.locator(".arco-textarea"),
            lambda: self.page.locator("textarea").first,
        ]

        for strategy in strategies:
            try:
                element = strategy()
                if await element.count() > 0:
                    return element
            except:
                continue

        raise Exception("无法定位提示词输入框")
```

## 4. 配置文件设计

### 4.1 Data-TestId 映射配置

```yaml
# config/data_testid_mappings.yaml
mappings:
  # 导航相关
  navigation:
    home_tab: "nav-home-tab"
    ai_create_tab: "nav-ai-create-tab"
    text_image_tab: "nav-text-image-tab"

  # AI创作页面
  ai_create_page:
    prompt_textarea: "ai-create-prompt-textarea"
    generate_image_btn: "ai-create-generate-image-btn"
    generate_video_btn: "ai-create-generate-video-btn"

  # 文生图页面
  text_image_page:
    prompt_input: "text-image-prompt-input"
    style_selector: "text-image-style-selector"
    generate_button: "text-image-generate-button"

  # 结果展示
  results:
    image_container: "result-image-container"
    video_container: "result-video-container"
    loading_spinner: "result-loading-spinner"
    error_message: "result-error-message"

# 回退策略配置
fallback_strategies:
  prompt_input:
    - "[data-testid='prompt-input']"
    - "textarea[placeholder*='提示']"
    - "textarea.arco-textarea"
    - "textarea:first-of-type"

  generate_button:
    - "[data-testid='generate-button']"
    - "button:has-text('生成')"
    - "button[type='submit']"
    - ".arco-btn-primary"
```

## 5. 实施建议

### 5.1 前端开发指南

1. **关键交互元素必须添加 data-testid**
2. **使用语义化的命名**
3. **保持命名一致性**
4. **避免动态生成的 ID**

### 5.2 测试开发指南

1. **优先使用 data-testid**
2. **使用回退策略提高稳定性**
3. **封装定位器避免重复代码**
4. **定期更新定位器配置**

## 6. 维护策略

### 6.1 自动化检测
- 定期扫描页面，检测 data-testid 覆盖率
- 识别缺失 data-testid 的关键交互元素
- 生成添加建议

### 6.2 版本管理
- data-testid 变更需要纳入代码审查
- 重大变更需要更新测试配置
- 保持向后兼容性