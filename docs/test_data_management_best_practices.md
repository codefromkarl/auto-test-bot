# 测试数据管理最佳实践

## 📋 概述

测试数据管理是自动化测试成功的关键因素。本指南详细介绍了闹海测试系统中测试数据的生成、管理、隔离和维护的最佳实践。

## 🎯 核心原则

### 1. 数据隔离原则
- **独立环境**：每个测试用例使用独立的数据环境
- **无状态影响**：测试间不应相互影响
- **及时清理**：测试完成后及时清理数据

### 2. 数据真实性原则
- **接近生产**：测试数据应接近真实生产环境数据
- **多样性**：覆盖各种数据类型和格式
- **动态性**：避免使用固定的硬编码数据

### 3. 数据安全原则
- **敏感信息保护**：避免使用真实的敏感数据
- **脱敏处理**：对生产数据进行适当的脱敏
- **访问控制**：控制测试数据的访问权限

## 🛠️ 数据生成策略

### 1. 动态数据生成

```python
from src.utils.test_data_manager import test_data_manager

# 基础数据生成
text_data = test_data_manager.generate_dynamic_data(
    data_type="text",
    constraints={
        "min_length": 10,
        "max_length": 100,
        "include_chinese": True
    },
    variation="normal"
)

# 边界值数据生成
boundary_text = test_data_manager.generate_dynamic_data(
    data_type="text",
    constraints={"min_length": 1, "max_length": 1000},
    variation="boundary"
)

# 无效数据生成
invalid_text = test_data_manager.generate_dynamic_data(
    data_type="text",
    constraints={},
    variation="invalid"
)
```

### 2. 数据变异数据生成

```python
# 基础数据
base_data = {
    "username": "test_user",
    "age": 25,
    "email": "test@example.com"
}

# 轻度变异
light_mutated = test_data_manager.mutate_data(
    original_data=base_data,
    mutation_type="random",
    mutation_intensity=0.05
)

# 重度变异
heavy_mutated = test_data_manager.mutate_data(
    original_data=base_data,
    mutation_type="random",
    mutation_intensity=0.3
)
```

### 3. 测试数据套件生成

```python
# 定义数据规范
data_specifications = [
    {
        "name": "user_profile_name",
        "type": "text",
        "constraints": {
            "min_length": 2,
            "max_length": 50,
            "include_chinese": True
        },
        "variations": ["normal", "boundary", "edge", "invalid"]
    },
    {
        "name": "user_profile_age",
        "type": "number",
        "constraints": {
            "min_value": 18,
            "max_value": 100
        },
        "variations": ["normal", "boundary", "invalid"]
    },
    {
        "name": "user_profile_email",
        "type": "email",
        "constraints": {
            "domain": "example.com"
        },
        "variations": ["normal", "invalid"]
    }
]

# 生成测试数据套件
test_suite = test_data_manager.generate_test_data_suite(data_specifications)

# 使用数据套件
for data_set_name, data_variations in test_suite["data_sets"].items():
    for variation, data_value in data_variations.items():
        print(f"{data_set_name} - {variation}: {data_value}")
```

## 🏗️ 数据隔离管理

### 1. 上下文隔离

```python
# 创建测试上下文
context_id = test_data_manager.create_isolation_context("user_registration_test")

# 在上下文中存储数据
test_data_manager.store_isolated_data(context_id, "username", "test_user_001")
test_data_manager.store_isolated_data(context_id, "email", "test_user_001@example.com")
test_data_manager.store_isolated_data(context_id, "age", 25)

# 从上下文中检索数据
username = test_data_manager.retrieve_isolated_data(context_id, "username")
email = test_data_manager.retrieve_isolated_data(context_id, "email")
age = test_data_manager.retrieve_isolated_data(context_id, "age")

print(f"User: {username}, Email: {email}, Age: {age}")

# 清理上下文
test_data_manager.cleanup_isolation_context(context_id)
```

### 2. 测试套件隔离

```yaml
# 工作流中的数据隔离配置
workflow:
  name: "isolated_user_registration_test"
  
  suite_setup:
    - action: "create_isolation_context"
      context_name: "user_registration"
      
  phases:
    - name: "test_normal_registration"
      steps:
        - action: "generate_user_data"
          context: "user_registration"
          variation: "normal"
          
        - action: "perform_registration"
          use_context: "user_registration"
          
    - name: "test_boundary_registration"
      steps:
        - action: "generate_user_data"
          context: "user_registration"
          variation: "boundary"
          
        - action: "perform_registration"
          use_context: "user_registration"
          
  suite_teardown:
    - action: "cleanup_isolation_context"
      context: "user_registration"
```

### 3. 数据库隔离

```python
class DatabaseIsolationManager:
    def __init__(self):
        self.active_connections = {}
    
    def create_isolated_database(self, test_name):
        """创建独立的测试数据库"""
        db_name = f"test_{test_name}_{uuid.uuid4().hex[:8]}"
        
        # 创建数据库连接
        connection = self._create_database_connection(db_name)
        
        # 初始化数据库结构
        self._initialize_database_schema(connection)
        
        self.active_connections[test_name] = {
            "db_name": db_name,
            "connection": connection,
            "created_at": datetime.now()
        }
        
        return db_name
    
    def cleanup_isolated_database(self, test_name):
        """清理测试数据库"""
        if test_name in self.active_connections:
            db_info = self.active_connections[test_name]
            
            # 关闭连接
            db_info["connection"].close()
            
            # 删除数据库
            self._drop_database(db_info["db_name"])
            
            del self.active_connections[test_name]
```

## 📊 数据类型管理

### 1. 文本数据

```python
# 中文文本生成
chinese_text = test_data_manager.generate_dynamic_data(
    data_type="text",
    constraints={
        "min_length": 5,
        "max_length": 100,
        "include_chinese": True
    },
    variation="normal"
)

# 特殊字符文本
special_chars_text = test_data_manager.generate_dynamic_data(
    data_type="text",
    constraints={
        "min_length": 10,
        "max_length": 50,
        "include_special_chars": True
    },
    variation="normal"
)

# HTML脚本文本（安全测试）
html_script_text = test_data_manager.generate_dynamic_data(
    data_type="text",
    constraints={},
    variation="invalid"
)
```

### 2. 数值数据

```python
# 整数数据
integer_data = test_data_manager.generate_dynamic_data(
    data_type="number",
    constraints={
        "min_value": 0,
        "max_value": 100,
        "is_float": False
    },
    variation="boundary"
)

# 浮点数数据
float_data = test_data_manager.generate_dynamic_data(
    data_type="number",
    constraints={
        "min_value": 0.0,
        "max_value": 100.0,
        "is_float": True,
        "precision": 2
    },
    variation="normal"
)

# 边界值数据
boundary_number = test_data_manager.generate_dynamic_data(
    data_type="number",
    constraints={
        "min_value": 18,
        "max_value": 65
    },
    variation="boundary"
)
```

### 3. 日期数据

```python
# 标准日期数据
standard_date = test_data_manager.generate_dynamic_data(
    data_type="date",
    constraints={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "format": "%Y-%m-%d"
    },
    variation="normal"
)

# 边界日期数据
boundary_date = test_data_manager.generate_dynamic_data(
    data_type="date",
    constraints={
        "start_date": "1920-01-01",
        "end_date": "2004-12-31"
    },
    variation="boundary"
)

# 时间戳数据
timestamp_data = test_data_manager.generate_dynamic_data(
    data_type="date",
    constraints={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "format": "%Y-%m-%d %H:%M:%S"
    },
    variation="normal"
)
```

### 4. 文件数据

```python
# 图片文件数据
image_file = test_data_manager.generate_dynamic_data(
    data_type="file",
    constraints={
        "type": "jpg",
        "size": 1024  # 1KB
    },
    variation="normal"
)

# 大文件数据
large_file = test_data_manager.generate_dynamic_data(
    data_type="file",
    constraints={
        "type": "mp4",
        "size": 1024 * 1024 * 10  # 10MB
    },
    variation="normal"
)

# 无效文件数据
invalid_file = test_data_manager.generate_dynamic_data(
    data_type="file",
    constraints={
        "type": "exe",
        "size": 1024 * 100  # 100KB
    },
    variation="invalid"
)
```

## 🔄 数据生命周期管理

### 1. 数据创建

```python
class TestDataLifecycle:
    def __init__(self):
        self.data_registry = {}
        self.lifecycle_events = []
    
    def create_test_data(self, data_spec):
        """创建测试数据"""
        data_id = str(uuid.uuid4())
        
        # 生成数据
        data = test_data_manager.generate_dynamic_data(
            data_type=data_spec["type"],
            constraints=data_spec.get("constraints", {}),
            variation=data_spec.get("variation", "normal")
        )
        
        # 注册数据
        self.data_registry[data_id] = {
            "data": data,
            "spec": data_spec,
            "created_at": datetime.now(),
            "status": "active"
        }
        
        # 记录生命周期事件
        self.lifecycle_events.append({
            "event": "created",
            "data_id": data_id,
            "timestamp": datetime.now()
        })
        
        return data_id, data
    
    def update_test_data(self, data_id, new_data):
        """更新测试数据"""
        if data_id in self.data_registry:
            old_data = self.data_registry[data_id]["data"]
            self.data_registry[data_id]["data"] = new_data
            self.data_registry[data_id]["updated_at"] = datetime.now()
            
            self.lifecycle_events.append({
                "event": "updated",
                "data_id": data_id,
                "old_data": old_data,
                "new_data": new_data,
                "timestamp": datetime.now()
            })
```

### 2. 数据清理

```python
def cleanup_test_data(self, data_id=None, test_name=None):
    """清理测试数据"""
    if data_id:
        # 清理特定数据
        if data_id in self.data_registry:
            del self.data_registry[data_id]
            self.lifecycle_events.append({
                "event": "cleaned",
                "data_id": data_id,
                "timestamp": datetime.now()
            })
    
    elif test_name:
        # 清理特定测试的所有数据
        to_remove = []
        for data_id, data_info in self.data_registry.items():
            if data_info["spec"].get("test_name") == test_name:
                to_remove.append(data_id)
        
        for data_id in to_remove:
            del self.data_registry[data_id]
            self.lifecycle_events.append({
                "event": "cleaned",
                "data_id": data_id,
                "test_name": test_name,
                "timestamp": datetime.now()
            })
```

### 3. 数据归档

```python
def archive_test_data(self, test_name, archive_path):
    """归档测试数据"""
    archived_data = {}
    
    for data_id, data_info in self.data_registry.items():
        if data_info["spec"].get("test_name") == test_name:
            archived_data[data_id] = data_info
    
    # 保存到文件
    with open(archive_path, 'w', encoding='utf-8') as f:
        json.dump(archived_data, f, indent=2, default=str)
    
    # 从活跃数据中移除
    self.cleanup_test_data(test_name=test_name)
    
    self.lifecycle_events.append({
        "event": "archived",
        "test_name": test_name,
        "archive_path": archive_path,
        "data_count": len(archived_data),
        "timestamp": datetime.now()
    })
```

## 🛡️ 数据安全管理

### 1. 敏感数据脱敏

```python
class DataMasking:
    def __init__(self):
        self.masking_patterns = {
            "email": r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "phone": r"(\d{3})\d{4}(\d{4})",
            "id_card": r"(\d{6})\d{8}(\d{4})",
            "credit_card": r"(\d{4})\d{8}(\d{4})"
        }
    
    def mask_data(self, data, data_type="text"):
        """脱敏处理"""
        if isinstance(data, dict):
            return {k: self.mask_data(v, k) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.mask_data(item) for item in data]
        elif isinstance(data, str):
            return self._mask_string(data)
        else:
            return data
    
    def _mask_string(self, text):
        """字符串脱敏"""
        masked = text
        
        # 邮箱脱敏
        masked = re.sub(self.masking_patterns["email"], r"\1***@\2", masked)
        
        # 手机号脱敏
        masked = re.sub(self.masking_patterns["phone"], r"\1****\2", masked)
        
        # 身份证脱敏
        masked = re.sub(self.masking_patterns["id_card"], r"\1********\2", masked)
        
        # 信用卡脱敏
        masked = re.sub(self.masking_patterns["credit_card"], r"\1********\2", masked)
        
        return masked
```

### 2. 数据访问控制

```python
class DataAccessControl:
    def __init__(self):
        self.access_policies = {}
        self.access_logs = []
    
    def set_access_policy(self, role, permissions):
        """设置访问策略"""
        self.access_policies[role] = permissions
    
    def check_access(self, user_role, data_type, operation):
        """检查访问权限"""
        has_permission = False
        
        if user_role in self.access_policies:
            policy = self.access_policies[user_role]
            if data_type in policy and operation in policy[data_type]:
                has_permission = True
        
        # 记录访问日志
        self.access_logs.append({
            "user_role": user_role,
            "data_type": data_type,
            "operation": operation,
            "has_permission": has_permission,
            "timestamp": datetime.now()
        })
        
        return has_permission
    
    def mask_based_on_role(self, data, user_role):
        """基于角色进行数据脱敏"""
        if user_role in ["admin", "tester"]:
            return data  # 管理员和测试员可以看到完整数据
        else:
            return self._mask_sensitive_data(data)
```

## 📈 性能优化

### 1. 数据生成优化

```python
class OptimizedDataGenerator:
    def __init__(self):
        self.data_cache = {}
        self.generation_templates = {}
    
    def generate_cached_data(self, data_spec, cache_key=None):
        """缓存数据生成"""
        if cache_key and cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        data = test_data_manager.generate_dynamic_data(
            data_type=data_spec["type"],
            constraints=data_spec.get("constraints", {}),
            variation=data_spec.get("variation", "normal")
        )
        
        if cache_key:
            self.data_cache[cache_key] = data
        
        return data
    
    def batch_generate_data(self, data_specs, batch_size=100):
        """批量生成数据"""
        results = []
        
        for i in range(0, len(data_specs), batch_size):
            batch = data_specs[i:i+batch_size]
            batch_results = []
            
            for spec in batch:
                data = self.generate_cached_data(
                    spec, 
                    cache_key=f"{spec['type']}_{spec.get('variation', 'normal')}"
                )
                batch_results.append(data)
            
            results.extend(batch_results)
        
        return results
```

### 2. 内存管理

```python
class MemoryEfficientDataManager:
    def __init__(self, max_memory_usage=1024*1024*1024):  # 1GB
        self.max_memory_usage = max_memory_usage
        self.current_memory_usage = 0
        self.data_pools = {}
    
    def store_data_with_limit(self, key, data):
        """限制内存使用的数据存储"""
        data_size = sys.getsizeof(data)
        
        # 检查内存限制
        if self.current_memory_usage + data_size > self.max_memory_usage:
            self._cleanup_old_data()
        
        # 存储数据
        self.data_pools[key] = {
            "data": data,
            "size": data_size,
            "accessed_at": datetime.now()
        }
        
        self.current_memory_usage += data_size
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        # 按访问时间排序
        sorted_items = sorted(
            self.data_pools.items(),
            key=lambda x: x[1]["accessed_at"]
        )
        
        # 清理最老的数据直到内存使用在限制内
        for key, item in sorted_items:
            if self.current_memory_usage <= self.max_memory_usage * 0.8:
                break
            
            self.current_memory_usage -= item["size"]
            del self.data_pools[key]
```

## 📋 最佳实践检查清单

### 数据生成
- [ ] 使用动态数据生成避免硬编码
- [ ] 覆盖正常、边界、异常数据
- [ ] 数据类型与生产环境匹配
- [ ] 定期更新数据生成规则

### 数据隔离
- [ ] 每个测试使用独立数据环境
- [ ] 测试完成后及时清理数据
- [ ] 避免测试间数据共享
- [ ] 使用上下文隔离机制

### 数据安全
- [ ] 敏感数据脱敏处理
- [ ] 实施访问控制策略
- [ ] 定期审计数据使用
- [ ] 安全存储测试数据

### 性能优化
- [ ] 使用缓存减少重复生成
- [ ] 监控内存使用情况
- [ ] 批量生成提高效率
- [ ] 及时清理无用数据

### 生命周期管理
- [ ] 明确数据创建规则
- [ ] 实施数据更新策略
- [ ] 定期归档历史数据
- [ ] 完整记录数据变更

## 🚀 故障排查

### 常见问题

1. **数据隔离失败**
   - 检查上下文创建和清理逻辑
   - 验证数据存储和检索机制
   - 确认测试间没有数据共享

2. **性能问题**
   - 分析数据生成热点
   - 优化缓存策略
   - 减少内存占用

3. **数据不一致**
   - 检查数据生成规则
   - 验证数据更新逻辑
   - 确认数据同步机制

4. **安全问题**
   - 审查数据脱敏规则
   - 检查访问控制策略
   - 验证数据传输安全

## 📚 参考资源

- [复杂场景测试指南](complex_scenario_guide.md)
- [边界条件测试指南](boundary_condition_guide.md)
- [高级功能使用指南](advanced_features_guide.md)
- [架构设计文档](architecture-design/README.md)