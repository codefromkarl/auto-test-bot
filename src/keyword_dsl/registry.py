from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeywordSpec:
    name: str
    action: str
    required_params: List[str] = field(default_factory=list)
    is_plugin: bool = False
    plugin_name: Optional[str] = None

    def validate(self, params: Dict[str, str]) -> None:
        missing = [p for p in self.required_params if p not in params]
        if missing:
            raise ValueError(f"Missing params for {self.name}: {missing}")


class KeywordRegistry:
    def __init__(self):
        self._specs: Dict[str, KeywordSpec] = {}

    def register(self, spec: KeywordSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Duplicate keyword: {spec.name}")
        self._specs[spec.name] = spec

    def get(self, name: str) -> KeywordSpec:
        if name not in self._specs:
            raise ValueError(f"Unknown keyword: {name}")
        return self._specs[name]

    def has(self, name: str) -> bool:
        return name in self._specs
