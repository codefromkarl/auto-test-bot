# 闹海AIGC平台自动化测试架构重构方案

## 一、背景与目标

### 1.1 业务特性
闹海是AIGC（AI生成内容）平台，具有以下核心特征：
- **重生成**：视频生成耗时10秒到10分钟不等
- **长耗时**：异步任务需要智能轮询
- **重资产**：资源包下载、文件校验等复杂操作

### 1.2 核心痛点
1. **异步长任务**：纯RF难以处理视频生成的等待
2. **文件处理**：资源包校验超出RF能力范围
3. **数据准备**：前置依赖复杂，纯UI测试效率低
4. **UI变动**：定位器维护成本高

### 1.3 重构目标
- 保留现有Python Bot工程化资产（度量、门禁、诊断）
- 引入RF提升业务可读性
- 解决AIGC场景的特殊测试难题
- 支持API+UI混合编排

## 二、架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────┐
│     Layer 1: 业务编排层 (RF)          │
│  - Robot Framework (.robot文件)        │
│  - 业务DSL，描述验收流程              │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Layer 2: 适配与调度层 (Python)       │
│  - NaohaiAdapter.py (胶水层)         │
│  - Sync-to-Async桥接                 │
│  - AIGC增强能力                     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Layer 3: 核心执行引擎 (现有Bot)       │
│  - Playwright封装                    │
│  - MetricsHybridLocator (三级定位)     │
│  - MCP诊断系统                       │
│  - 契约门禁                         │
└─────────────────────────────────────────┘
```

### 2.2 核心设计原则

1. **分层解耦**：每层职责明确，接口清晰
2. **资产复用**：最大化保留现有Python工程能力
3. **智能降级**：三级定位策略确保稳定性
4. **混合编排**：API快速准备数据，UI验证核心流程

## 三、分层详细设计

### 3.1 Layer 1: 业务编排层

**技术栈**：Robot Framework
**职责**：
- 将功能清单转化为可执行的测试流程
- 提供业务级的DSL抽象
- 支持非技术人员参与

**示例测试用例**：
```robot
*** Test Cases ***
视频创作完整流程
    [Documentation]    验收Step 6核心闭环

    # 1. 快速准备数据（API能力）
    ${test_data}=    准备视频生成测试数据
    Set Suite Variable    ${test_data}

    # 2. UI执行核心流程
    进入剧本详情    ${test_data.script_id}
    进入视频创作页    ${test_data.episode_id}
    配置视频参数    model=v2.0    resolution=1080P
    提交视频生成

    # 3. 智能等待（AIGC能力）
    ${result}=    等待视频生成完成    timeout=600s

    # 4. 导出和校验
    导出资源包
    校验资源包完整性    expected_videos=${test_data.expected_videos}
```

### 3.2 Layer 2: 适配与调度层

**核心组件**：NaohaiAdapter.py
**关键机制**：

#### 3.2.1 Sync-to-Async桥接
```python
class NaohaiAdapter:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.bot = None

    @keyword
    def some_keyword(self):
        return self.loop.run_until_complete(
            self.bot.async_method()
        )
```

#### 3.2.2 AIGC专属能力
- **智能轮询**：处理长耗时异步任务
- **文件处理**：资源包解压、验证、校验
- **API混合编排**：快速准备测试数据

#### 3.2.3 生命周期管理
- Suite级别单例：避免浏览器重复启动
- 自动清理：测试结束后释放资源

### 3.3 Layer 3: 核心执行引擎

**保留的现有资产**：
- **Playwright封装**：浏览器操作能力
- **MCP诊断系统**：失败时深度分析
- **登录态管理**：SessionStorage注入
- **度量系统**：data-testid覆盖率统计

#### 3.3.1 三级定位策略（新增核心）
```python
class ThreeTierLocator:
    async def locate(self, config):
        # L1: Gold Standard (data-testid)
        if result := await self._try_gold(config):
            return self._record_tier(result, 'gold')

        # L2: Silver Standard (稳定属性)
        if result := await self._try_silver(config):
            return self._record_tier(result, 'silver', warning=True)

        # L3: Bronze Standard (文本兜底)
        if result := await self._try_bronze(config):
            return self._record_tier(result, 'bronze', risk=True)

        return self._handle_failure(config)
```

## 四、关键业务场景解决方案

### 4.1 异步长任务处理
**场景**：Step 6.2 视频生成（1-10分钟）
**解决方案**：
```python
async def wait_for_video_completion(self, task_id, timeout=600):
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = await self.api.get_task_status(task_id)

        if status == 'completed':
            return await self.api.get_result(task_id)
        elif status == 'failed':
            raise TaskFailedException(f"任务失败: {task_id}")

        await asyncio.sleep(5)  # 智能等待

    raise TimeoutException(f"任务超时: {task_id}")
```

### 4.2 文件处理与校验
**场景**：Step 6.4 导出资源包（几百MB）
**解决方案**：
```python
def validate_resource_package(self, expected_videos=5):
    zip_path = self.get_latest_download()

    with zipfile.ZipFile(zip_path) as zf:
        file_list = zf.namelist()

        # 验证视频数量
        video_files = [f for f in file_list if f.endswith('.mp4')]
        if len(video_files) < expected_videos:
            raise ValidationException(f"视频数量不足")

        # 验证每个视频完整性
        for video in video_files:
            with zf.open(video) as vf:
                probe = ffmpeg.probe(vf)
                if probe['streams'][0]['height'] < 720:
                    raise ValidationException(f"分辨率不足")

    return True
```

### 4.3 API+UI混合编排
**场景**：Step 1-4 前置数据准备
**解决方案**：
```python
async def setup_test_data(self):
    # API快速创建剧本
    script = await self.api.create_script({
        'name': '自动化测试剧本',
        'style': 'anime',
        'ratio': '16:9'
    })

    # API创建分集
    episode = await self.api.create_episode(script['id'])

    # API创建角色
    role = await self.api.create_role({
        'episode_id': episode['id'],
        'name': '测试角色'
    })

    return {
        'script_id': script['id'],
        'episode_id': episode['id'],
        'role_id': role['id']
    }
```

## 五、工程目录结构

```
naohai_autotest/
├── config/
│   ├── prod.yaml                    # 环境配置
│   └── required_testids.yaml        # 契约文件
├── core/                          # Layer 3: 核心引擎
│   ├── bot.py                     # Playwright封装
│   ├── locator/
│   │   ├── three_tier_locator.py    # 三级定位器
│   │   └── metrics_collector.py     # 度量收集
│   ├── mcp/                      # MCP诊断
│   └── gates/                    # 契约门禁
├── libraries/                     # Layer 2: 适配层
│   ├── naohai_adapter.py          # RF适配器
│   ├── api_client.py              # API客户端
│   └── file_validator.py          # 文件处理工具
├── tests/                         # Layer 1: RF测试用例
│   ├── keywords/                  # 业务关键字
│   │   ├── video_creation.resource
│   │   └── common_keywords.resource
│   ├── scenarios/                 # 测试场景
│   │   ├── e2e_script_flow.robot
│   │   └── smoke_video_gen.robot
│   └── data/                     # 测试数据
└── results/                       # 测试报告
```

## 六、实施计划

### Phase 1: 基础改造（2周）
- [ ] 实现NaohaiAdapter基础框架
- [ ] 搭建三层定位器核心
- [ ] 实现Sync-to-Async桥接
- [ ] 单元测试覆盖

### Phase 2: AIGC能力建设（2周）
- [ ] 实现智能轮询机制
- [ ] 开发文件处理模块
- [ ] 创建API混合编排能力
- [ ] 集成测试验证

### Phase 3: 试点验证（1周）
- [ ] 选取核心场景进行POC
- [ ] 对比新旧方案效果
- [ ] 收集性能数据
- [ ] 优化关键瓶颈

### Phase 4: 全面迁移（2周）
- [ ] 迁移全部测试用例
- [ ] 更新CI/CD流程
- [ ] 培训团队使用
- [ ] 建立监控告警

## 七、关键设计决策

### 7.1 为什么必须用RF？
1. **业务可读性**：产品人员可以理解和维护
2. **降低门槛**：非技术人员也能参与
3. **标准化**：统一的测试DSL格式

### 7.2 为什么保留Python Bot？
1. **保护投资**：现有工程化资产继续复用
2. **解决痛点**：AIGC场景需要复杂逻辑
3. **灵活性**：Python处理复杂任务更强大

### 7.3 为什么选择混合架构？
1. **最优分工**：RF做编排，Python做执行
2. **渐进迁移**：风险可控，可逐步推进
3. **未来兼容**：为后续扩展留有空间

## 八、风险评估与缓解

### 8.1 技术风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 定位器回退误点 | 高 | L3必须满足唯一性+语义校验 |
| 异步轮询超时 | 中 | 智能超时计算+重试机制 |
| API依赖变更 | 中 | 版本化API+兼容性检查 |

### 8.2 运维风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 环境配置复杂 | 中 | 配置模板化+文档完善 |
| 调试难度增加 | 中 | 保留MCP诊断+增强日志 |

## 九、成功指标

### 9.1 技术指标
- 测试执行时间：减少50%（API混合编排）
- 定位成功率：保持95%+（三级定位）
- CI通过率：提升至90%+（软门禁）
- 维护成本：降低60%（业务DSL）

### 9.2 业务指标
- 发布周期：缩短30%（减少阻塞）
- 缺陷发现：提前20%（自动化覆盖）
- 团队效率：提升40%（降低门槛）

## 十、附录

### 10.1 核心接口定义

```python
# NaohaiAdapter接口
class NaohaiAdapter:
    def init_env(self, config_path): ...
    def smart_click(self, element_key, fallback=None): ...
    def wait_for_video(self, task_id, timeout=600): ...
    def validate_package(self, expected_count): ...
    def cleanup(self): ...
```

### 10.2 配置示例

```yaml
# config/prod.yaml
app:
  base_url: "https://naohai.example.com"

test:
  timeout: 30000
  retry_times: 3

locator:
  tiers:
    gold:
      selector_template: "[data-testid='{test_id}']"
      timeout: 5000
    silver:
      selectors:
        - "[name='{name}']"
        - "[aria-label='{label}']"
      timeout: 3000
    bronze:
      selector_template: "text='{text}'"
      timeout: 2000
      verify_unique: true
```

---

**文档版本**：v1.0
**最后更新**：2025-12-17
**维护者**：闹海测试团队