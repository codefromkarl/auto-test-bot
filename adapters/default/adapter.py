from __future__ import annotations

from typing import Any, Dict, List, Mapping, Type
from adapters.base import BaseAdapter
from models.action import Action
from models.context import Context
from models.semantic_action import SemanticAction

class EnsureStoryExistsSemanticAction(SemanticAction):
    def get_atomic_actions(self) -> List[Action]:
        # Default behavior is a no-op to keep the framework usable without a business adapter.
        return []

    def get_step_name(self) -> str:
        return "ensure_story_exists"


class DefaultAdapter(BaseAdapter):
    def register_selectors(self) -> Mapping[str, str]:
        return {}

    def register_semantic_actions(self) -> Mapping[str, Type[SemanticAction]]:
        return {"ensure_story_exists": EnsureStoryExistsSemanticAction}

    def get_config(self) -> Dict[str, Any]:
        return {}
