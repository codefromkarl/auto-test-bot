from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping, TYPE_CHECKING, Type

from framework.core.protocol.adapter import AdapterProtocol

if TYPE_CHECKING:
    from models.semantic_action import SemanticAction


class BaseAdapter(AdapterProtocol, ABC):
    """
    业务适配器基类（业务模块层）。

    业务模块只需要实现：
    - selectors（供 workflow 使用 `.xxx` 简写）
    - semantic actions（供 workflow 使用 `rf_` action）
    - adapter config（业务侧默认/覆盖）
    """

    @abstractmethod
    def register_selectors(self) -> Mapping[str, str]:
        """返回 selector 映射（允许使用 `navigation.ai_creation` 这类 dot-path key）"""

    @abstractmethod
    def register_semantic_actions(self) -> Mapping[str, Type["SemanticAction"]]:
        """返回语义 Action 映射（key 为 semantic type，例如 `ensure_story_exists`）"""

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """返回业务配置（会被合并进执行器的 template context）"""
