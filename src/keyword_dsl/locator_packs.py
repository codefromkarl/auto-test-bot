from typing import Dict


class LocatorPackRegistry:
    def __init__(self, packs: Dict[str, Dict[str, str]]):
        self._packs = packs

    def resolve(self, pack: str, key: str) -> str:
        if pack not in self._packs:
            raise ValueError(f"Unknown locator pack: {pack}")
        mapping = self._packs[pack]
        if key not in mapping:
            raise ValueError(f"Unknown locator key: {key}")
        return mapping[key]
