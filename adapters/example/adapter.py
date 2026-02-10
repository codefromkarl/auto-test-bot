from __future__ import annotations

from typing import Any, Dict, Mapping, Type

from src.adapters.base import BaseAdapter
from src.models.semantic_action import SemanticAction


class ExampleAdapter(BaseAdapter):
    def register_selectors(self) -> Mapping[str, str]:
        return {
            "buttons.ok": "#ok",
            "buttons.cancel": "#cancel",
        }

    def register_semantic_actions(self) -> Mapping[str, Type[SemanticAction]]:
        return {}

    def get_config(self) -> Dict[str, Any]:
        return {}

