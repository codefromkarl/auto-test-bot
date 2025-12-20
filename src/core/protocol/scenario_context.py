from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import Any, Dict, Optional


class ScenarioContextValidationError(ValueError):
    pass


def _require_str(data: Dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioContextValidationError(f"字段 {key} 必须是非空字符串")
    return value


def _require_dict(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ScenarioContextValidationError(f"字段 {key} 必须是对象(dict)")
    return value


@dataclass
class ScenarioContext:
    """跨层数据传输的标准协议（v2）"""

    test_id: str
    business_flow: str
    test_name: str

    test_data: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    execution_options: Dict[str, Any] = field(default_factory=dict)
    expected_results: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # 协议版本（语义版本号）
    version: str = "2.0"
    # Schema 版本（用于演进与兼容）
    schema_version: str = "2.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "schema_version": self.schema_version,
            "test_id": self.test_id,
            "business_flow": self.business_flow,
            "test_name": self.test_name,
            "test_data": self.test_data,
            "environment": self.environment,
            "execution_options": self.execution_options,
            "expected_results": self.expected_results,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    @classmethod
    def from_json(cls, json_str: str) -> ScenarioContext:
        try:
            payload = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ScenarioContextValidationError("ScenarioContext JSON 解析失败") from exc
        if not isinstance(payload, dict):
            raise ScenarioContextValidationError("ScenarioContext JSON 顶层必须是对象(dict)")
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> ScenarioContext:
        version = str(payload.get("version") or "1.0")
        normalized = payload
        if version.startswith("1."):
            normalized = cls._upgrade_v1_to_v2(payload)

        test_id = _require_str(normalized, "test_id")
        business_flow = _require_str(normalized, "business_flow")
        test_name = _require_str(normalized, "test_name")

        test_data = _require_dict(normalized, "test_data")
        environment = _require_dict(normalized, "environment")
        execution_options = _require_dict(normalized, "execution_options")
        expected_results = _require_dict(normalized, "expected_results")

        created_at = cls._parse_dt(normalized.get("created_at")) or datetime.now()
        updated_at = cls._parse_dt(normalized.get("updated_at"))

        ctx = cls(
            test_id=test_id,
            business_flow=business_flow,
            test_name=test_name,
            test_data=test_data,
            environment=environment,
            execution_options=execution_options,
            expected_results=expected_results,
            created_at=created_at,
            updated_at=updated_at,
            version=str(normalized.get("version") or "2.0"),
            schema_version=str(normalized.get("schema_version") or "2.0"),
        )
        return ctx

    @staticmethod
    def _parse_dt(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value)
            except ValueError as exc:
                raise ScenarioContextValidationError("时间字段必须是 ISO8601 格式") from exc
        raise ScenarioContextValidationError("时间字段必须是字符串或 datetime")

    @staticmethod
    def _upgrade_v1_to_v2(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        v1.x → v2.0 升级：尽量兼容历史字段命名。
        """
        def pick(*keys: str) -> Any:
            for k in keys:
                if k in payload:
                    return payload.get(k)
            return None

        return {
            "version": "2.0",
            "schema_version": "2.0",
            "test_id": pick("test_id", "testId", "id"),
            "business_flow": pick("business_flow", "businessFlow", "flow"),
            "test_name": pick("test_name", "testName", "name"),
            "test_data": pick("test_data", "data") or {},
            "environment": pick("environment", "env") or {},
            "execution_options": pick("execution_options", "options") or {},
            "expected_results": pick("expected_results", "expected") or {},
            "created_at": pick("created_at", "createdAt"),
            "updated_at": pick("updated_at", "updatedAt"),
        }
