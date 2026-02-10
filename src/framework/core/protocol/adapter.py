from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from models.semantic_action import SemanticAction


class AdapterProtocol(ABC):
    """
    Business adapter contract.

    Adapters expose:
    - selector registry (for `.xxx` shorthand in workflows)
    - semantic action registry (for `rf_` actions)
    - business configuration (adapter-specific defaults/overrides)
    """

    @abstractmethod
    def register_selectors(self) -> Mapping[str, str]:
        """Return selector mapping (supports dot-path keys like `navigation.ai_creation`)."""

    @abstractmethod
    def register_semantic_actions(self) -> Mapping[str, Type["SemanticAction"]]:
        """Return semantic action mapping, keyed by semantic type (e.g. `ensure_story_exists`)."""

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Return adapter-specific configuration (merged into executor template context)."""

