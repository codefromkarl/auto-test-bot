"""
测试数据管理器 - 提供动态数据生成、隔离机制和变异数据支持
"""

import random
import string
import uuid
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import os
import shutil
from pathlib import Path


# 创建一个简单的faker替代类
class SimpleFaker:
    def __init__(self, locale="zh_CN"):
        self.locale = locale

    def text(self, max_nb_chars=200):
        words = [
            "测试",
            "数据",
            "生成",
            "用于",
            "验证",
            "系统",
            "功能",
            "正常",
            "运行",
            "流程",
        ]
        length = min(max_nb_chars // 2, len(words))
        return "".join(random.choices(words, k=length))

    def user_name(self):
        return f"user_{random.randint(1000, 9999)}"

    def slug(self):
        return f"test-{random.randint(1000, 9999)}"


# 尝试导入faker，如果不可用则使用简单的替代方案
FAKER_AVAILABLE = False
faker_instance = SimpleFaker

try:
    import faker as faker_module

    FAKER_AVAILABLE = True
    faker_instance = faker_module.Faker
except ImportError:
    # 使用简单的faker替代
    pass


class TestDataManager:
    """测试数据管理器，支持动态数据生成、隔离和变异"""

    def __init__(self, base_dir: str = "test_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # 初始化faker生成器（如果可用）
        if FAKER_AVAILABLE:
            self.fake = faker_instance("zh_CN")
        else:
            self.fake = SimpleFaker("zh_CN")

        # 数据隔离存储
        self.isolation_stores: Dict[str, Dict[str, Any]] = {}

        # 数据变异数据库
        self.mutation_patterns = self._load_mutation_patterns()

        # 测试数据版本管理
        self.data_versions: Dict[str, str] = {}

    def _load_mutation_patterns(self) -> Dict[str, List[str]]:
        """加载数据变异模式"""
        return {
            "text_mutations": [
                "add_random_whitespace",
                "change_case",
                "add_special_chars",
                "replace_with_synonyms",
                "truncate_randomly",
            ],
            "number_mutations": [
                "add_random_offset",
                "multiply_by_factor",
                "change_sign",
                "round_to_precision",
            ],
            "date_mutations": [
                "add_random_days",
                "change_time_format",
                "add_random_hours",
                "set_to_boundary",
            ],
        }

    def generate_dynamic_data(
        self,
        data_type: str,
        constraints: Optional[Dict[str, Any]] = None,
        variation: str = "normal",
    ) -> Any:
        """
        生成动态测试数据

        Args:
            data_type: 数据类型 (text, number, date, file, email, etc.)
            constraints: 约束条件
            variation: 变异类型 (normal, boundary, edge, invalid)

        Returns:
            生成的测试数据
        """
        constraints = constraints or {}

        if data_type == "text":
            return self._generate_text_data(constraints, variation)
        elif data_type == "number":
            return self._generate_number_data(constraints, variation)
        elif data_type == "date":
            return self._generate_date_data(constraints, variation)
        elif data_type == "email":
            return self._generate_email_data(constraints, variation)
        elif data_type == "file":
            return self._generate_file_data(constraints, variation)
        elif data_type == "url":
            return self._generate_url_data(constraints, variation)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    def _generate_text_data(self, constraints: Dict[str, Any], variation: str) -> str:
        """生成文本数据"""
        min_length = constraints.get("min_length", 1)
        max_length = constraints.get("max_length", 100)

        if variation == "boundary":
            if random.choice([True, False]):
                # 最小边界
                return "A" * min_length
            else:
                # 最大边界
                return "B" * max_length
        elif variation == "edge":
            # 边界值附近
            return "C" * random.randint(min_length - 1, max_length + 1)
        elif variation == "invalid":
            # 无效数据
            return self._generate_invalid_text(constraints)
        else:
            # 正常数据
            target_length = random.randint(min_length, max_length)
            if constraints.get("include_special_chars", False):
                chars = string.ascii_letters + string.digits + string.punctuation
                return "".join(random.choices(chars, k=target_length))
            elif constraints.get("include_chinese", False):
                return "".join(
                    random.choices("这是一段测试文本用于验证系统功能", k=target_length)
                )
            else:
                return self.fake.text(max_nb_chars=target_length).strip()

    def _generate_invalid_text(self, constraints: Dict[str, Any]) -> str:
        """生成无效文本数据"""
        invalid_types = [
            "",  # 空字符串
            "   ",  # 只有空格
            "\t\n\r",  # 只有控制字符
            "<script>alert('xss')</script>",  # XSS攻击
            "'; DROP TABLE users; --",  # SQL注入
            "\x00\x01\x02",  # 二进制字符
            "a" * 10000,  # 超长字符串
        ]
        return random.choice(invalid_types)

    def _generate_number_data(
        self, constraints: Dict[str, Any], variation: str
    ) -> Union[int, float]:
        """生成数字数据"""
        min_val = constraints.get("min_value", 0)
        max_val = constraints.get("max_value", 1000)
        is_float = constraints.get("is_float", False)

        if variation == "boundary":
            if random.choice([True, False]):
                return min_val
            else:
                return max_val
        elif variation == "edge":
            # 边界值附近
            if is_float:
                return random.uniform(min_val - 0.1, max_val + 0.1)
            else:
                return random.randint(min_val - 1, max_val + 1)
        elif variation == "invalid":
            # 无效数字
            invalid_types = [
                float("inf"),
                float("-inf"),
                float("nan"),
                None,
                "not_a_number",
                "1e1000",  # 溢出
            ]
            return random.choice(invalid_types)
        else:
            # 正常数据
            if is_float:
                return round(
                    random.uniform(min_val, max_val), constraints.get("precision", 2)
                )
            else:
                return random.randint(min_val, max_val)

    def _generate_date_data(self, constraints: Dict[str, Any], variation: str) -> str:
        """生成日期数据"""
        start_date = constraints.get("start_date", datetime.now() - timedelta(days=365))
        end_date = constraints.get("end_date", datetime.now())
        format_str = constraints.get("format", "%Y-%m-%d")

        if variation == "boundary":
            if random.choice([True, False]):
                return start_date.strftime(format_str)
            else:
                return end_date.strftime(format_str)
        elif variation == "edge":
            # 边界日期附近
            edge_date = start_date - timedelta(days=random.randint(1, 10))
            return edge_date.strftime(format_str)
        elif variation == "invalid":
            # 无效日期
            invalid_dates = [
                "invalid-date",
                "2023-13-32",  # 不存在的日期
                "2023/02/30",  # 不存在的日期
                "",
                None,
            ]
            return random.choice(invalid_dates)
        else:
            # 正常日期
            time_between = end_date - start_date
            days_between = time_between.days
            random_number_of_days = random.randrange(days_between)
            random_date = start_date + timedelta(days=random_number_of_days)
            return random_date.strftime(format_str)

    def _generate_email_data(self, constraints: Dict[str, Any], variation: str) -> str:
        """生成邮箱数据"""
        if variation == "invalid":
            invalid_emails = [
                "",
                "not-an-email",
                "@domain.com",
                "user@",
                "user..name@domain.com",
                "user@.com",
                "user@domain.",
                "user name@domain.com",  # 包含空格
                "user@domain..com",
            ]
            return random.choice(invalid_emails)
        else:
            domain = constraints.get("domain", "example.com")
            username = self.fake.user_name() if variation == "normal" else "test"
            return f"{username}@{domain}"

    def _generate_file_data(
        self, constraints: Dict[str, Any], variation: str
    ) -> Dict[str, Any]:
        """生成文件数据"""
        file_type = constraints.get("type", "text")
        file_size = constraints.get("size", random.randint(1, 1024))

        file_data = {
            "name": f"test_file_{uuid.uuid4().hex[:8]}.{file_type}",
            "type": file_type,
            "size": file_size,
        }

        if variation == "invalid":
            file_data.update(
                {
                    "name": "invalid.exe",  # 危险文件类型
                    "size": file_size * 10,  # 超大文件
                }
            )

        return file_data

    def _generate_url_data(self, constraints: Dict[str, Any], variation: str) -> str:
        """生成URL数据"""
        if variation == "invalid":
            invalid_urls = [
                "",
                "not-a-url",
                "ftp://invalid-protocol.com",
                "http://",
                "https://",
                "http://[invalid-ipv6]",
            ]
            return random.choice(invalid_urls)
        else:
            domain = constraints.get("domain", "example.com")
            path = f"/{self.fake.slug()}" if variation == "normal" else "/test"
            return f"https://{domain}{path}"

    def create_isolation_context(self, context_name: str) -> str:
        """
        创建数据隔离上下文

        Args:
            context_name: 上下文名称

        Returns:
            上下文ID
        """
        context_id = f"{context_name}_{uuid.uuid4().hex[:8]}"

        # 创建隔离目录
        context_dir = self.base_dir / context_id
        context_dir.mkdir(exist_ok=True)

        # 初始化隔离存储
        self.isolation_stores[context_id] = {
            "data": {},
            "files": str(context_dir),
            "created_at": datetime.now().isoformat(),
            "metadata": {},
        }

        return context_id

    def store_isolated_data(self, context_id: str, key: str, data: Any) -> None:
        """
        存储隔离数据

        Args:
            context_id: 隔离上下文ID
            key: 数据键
            data: 数据值
        """
        if context_id not in self.isolation_stores:
            raise ValueError(f"Isolation context {context_id} not found")

        self.isolation_stores[context_id]["data"][key] = {
            "value": data,
            "stored_at": datetime.now().isoformat(),
            "checksum": self._calculate_checksum(data),
        }

    def retrieve_isolated_data(self, context_id: str, key: str) -> Any:
        """
        检索隔离数据

        Args:
            context_id: 隔离上下文ID
            key: 数据键

        Returns:
            数据值
        """
        if context_id not in self.isolation_stores:
            raise ValueError(f"Isolation context {context_id} not found")

        if key not in self.isolation_stores[context_id]["data"]:
            raise ValueError(f"Data key {key} not found in context {context_id}")

        stored_data = self.isolation_stores[context_id]["data"][key]
        return stored_data["value"]

    def mutate_data(
        self,
        original_data: Any,
        mutation_type: str = "random",
        mutation_intensity: float = 0.1,
    ) -> Any:
        """
        数据变异

        Args:
            original_data: 原始数据
            mutation_type: 变异类型
            mutation_intensity: 变异强度 (0.0-1.0)

        Returns:
            变异后的数据
        """
        if isinstance(original_data, str):
            return self._mutate_text(original_data, mutation_type, mutation_intensity)
        elif isinstance(original_data, (int, float)):
            return self._mutate_number(original_data, mutation_type, mutation_intensity)
        elif isinstance(original_data, dict):
            return self._mutate_dict(original_data, mutation_type, mutation_intensity)
        elif isinstance(original_data, list):
            return self._mutate_list(original_data, mutation_type, mutation_intensity)
        else:
            return original_data

    def _mutate_text(self, text: str, mutation_type: str, intensity: float) -> str:
        """文本变异"""
        if not text:
            return text

        mutation_count = max(1, int(len(text) * intensity))

        for _ in range(mutation_count):
            if mutation_type == "random":
                mutation = random.choice(self.mutation_patterns["text_mutations"])
            else:
                mutation = mutation_type

            if mutation == "add_random_whitespace":
                pos = random.randint(0, len(text))
                text = text[:pos] + " " + text[pos:]
            elif mutation == "change_case":
                if text:
                    pos = random.randint(0, len(text) - 1)
                    char = text[pos]
                    text = (
                        text[:pos]
                        + (char.upper() if char.islower() else char.lower())
                        + text[pos + 1 :]
                    )
            elif mutation == "add_special_chars":
                pos = random.randint(0, len(text))
                special_char = random.choice("!@#$%^&*()")
                text = text[:pos] + special_char + text[pos:]
            elif mutation == "truncate_randomly":
                if len(text) > 1:
                    pos = random.randint(1, len(text) - 1)
                    text = text[:pos]

        return text

    def _mutate_number(
        self, number: Union[int, float], mutation_type: str, intensity: float
    ) -> Union[int, float]:
        """数字变异"""
        if mutation_type == "random":
            mutation = random.choice(self.mutation_patterns["number_mutations"])
        else:
            mutation = mutation_type

        if mutation == "add_random_offset":
            offset = number * intensity * random.uniform(-1, 1)
            return number + offset
        elif mutation == "multiply_by_factor":
            factor = 1 + intensity * random.uniform(-0.5, 0.5)
            return number * factor
        elif mutation == "change_sign":
            return -number
        elif mutation == "round_to_precision":
            return round(number, random.randint(0, 5))

        return number

    def _mutate_dict(
        self, data: Dict[str, Any], mutation_type: str, intensity: float
    ) -> Dict[str, Any]:
        """字典变异"""
        mutated = data.copy()
        keys_to_mutate = list(mutated.keys())
        mutation_count = max(1, int(len(keys_to_mutate) * intensity))

        for _ in range(mutation_count):
            if keys_to_mutate:
                key = random.choice(keys_to_mutate)
                keys_to_mutate.remove(key)
                mutated[key] = self.mutate_data(mutated[key], mutation_type, intensity)

        return mutated

    def _mutate_list(
        self, data: List[Any], mutation_type: str, intensity: float
    ) -> List[Any]:
        """列表变异"""
        mutated = data.copy()
        mutation_count = max(1, int(len(mutated) * intensity))

        for _ in range(mutation_count):
            if mutated:
                index = random.randint(0, len(mutated) - 1)
                mutated[index] = self.mutate_data(
                    mutated[index], mutation_type, intensity
                )

        return mutated

    def _calculate_checksum(self, data: Any) -> str:
        """计算数据校验和"""
        if isinstance(data, str):
            content = data.encode("utf-8")
        else:
            content = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.md5(content).hexdigest()

    def cleanup_isolation_context(self, context_id: str) -> None:
        """清理隔离上下文"""
        if context_id in self.isolation_stores:
            context_dir = Path(self.isolation_stores[context_id]["files"])
            if context_dir.exists():
                shutil.rmtree(context_dir)
            del self.isolation_stores[context_id]

    def generate_test_data_suite(
        self, data_specifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成测试数据套件

        Args:
            data_specifications: 数据规范列表

        Returns:
            测试数据套件
        """
        test_suite = {
            "suite_id": f"test_suite_{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.now().isoformat(),
            "data_sets": {},
        }

        for spec in data_specifications:
            data_name = spec.get("name", f"data_{len(test_suite['data_sets'])}")
            data_type = spec.get("type", "text")
            constraints = spec.get("constraints", {})
            variations = spec.get("variations", ["normal"])

            test_suite["data_sets"][data_name] = {}

            for variation in variations:
                data = self.generate_dynamic_data(data_type, constraints, variation)
                test_suite["data_sets"][data_name][variation] = data

        return test_suite

    def export_test_data(self, context_id: str, export_path: str) -> None:
        """导出测试数据"""
        if context_id not in self.isolation_stores:
            raise ValueError(f"Isolation context {context_id} not found")

        context_data = self.isolation_stores[context_id]
        export_file = Path(export_path)

        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False, default=str)

    def import_test_data(self, import_path: str) -> str:
        """导入测试数据"""
        import_file = Path(import_path)

        with open(import_file, "r", encoding="utf-8") as f:
            imported_data = json.load(f)

        context_id = self.create_isolation_context(f"imported_{import_file.stem}")
        self.isolation_stores[context_id] = imported_data

        return context_id


# 全局测试数据管理器实例
test_data_manager = TestDataManager()
