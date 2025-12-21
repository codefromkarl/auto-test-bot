"""
Locator hierarchy compiler.

Flattens hierarchical locator definitions into a flat mapping while preserving
group namespaces and providing alias compatibility for legacy keys.
"""

from typing import Any, Dict, Iterable, List, Optional


class LocatorHierarchyCompiler:
    """Compile hierarchical locators into flat locators."""

    META_KEYS = {"extends"}
    HIERARCHY_HINTS = {
        "base",
        "groups",
        "page_mapping",
        "loading_strategy",
        "performance",
        "semantic_isolation",
    }

    def __init__(self, raw_locators: Optional[Dict[str, Any]]):
        self.raw_locators = raw_locators or {}
        self.hierarchy = self._extract_hierarchy(self.raw_locators)
        self.aliases = self._extract_aliases(self.raw_locators)

        self.base_group_names: List[str] = []
        self.group_group_names: List[str] = []
        self.group_defs: Dict[str, Dict[str, Any]] = {}
        self.group_extends: Dict[str, List[str]] = {}

        if self.hierarchy is not None:
            self._load_group_defs()

    @classmethod
    def is_hierarchical(cls, raw_locators: Any) -> bool:
        if not isinstance(raw_locators, dict):
            return False
        if "hierarchy" in raw_locators:
            return True
        return any(key in raw_locators for key in cls.HIERARCHY_HINTS)

    def compile(
        self,
        page: Optional[str] = None,
        context: Optional[List[str]] = None,
        strict_aliases: bool = True,
    ) -> Dict[str, List[str]]:
        """Compile hierarchical locators into a flat map."""
        if self.hierarchy is None:
            return self._normalize_flat_locators(self.raw_locators)

        group_names = self._resolve_page_groups(page)
        if not group_names:
            group_names = list(self.group_defs.keys())

        ordered_groups = self._expand_groups(group_names)
        flat: Dict[str, List[str]] = {}
        for group_name in ordered_groups:
            group_flat = self._flatten_group(group_name)
            flat = self._merge_flat(flat, group_flat)

        if context is None and page:
            page_def = (self.hierarchy.get("page_mapping") or {}).get(page, {})
            context = page_def.get("context")

        if context:
            flat = self._filter_by_context(flat, context)

        if self.aliases:
            flat = self._apply_aliases(flat, strict=strict_aliases)

        return flat

    def _resolve_page_groups(self, page: Optional[str]) -> List[str]:
        if not page:
            return []
        page_def = (self.hierarchy.get("page_mapping") or {}).get(page, {})
        return self._normalize_extends(page_def.get("extends"))

    def _extract_hierarchy(self, raw_locators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.is_hierarchical(raw_locators):
            return None
        if "hierarchy" in raw_locators:
            return raw_locators.get("hierarchy") or {}
        return raw_locators

    def _extract_aliases(self, raw_locators: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_locators, dict):
            return {}
        return (
            raw_locators.get("aliases")
            or raw_locators.get("locator_aliases")
            or {}
        )

    def _load_group_defs(self) -> None:
        base_defs = self.hierarchy.get("base") or {}
        group_defs = self.hierarchy.get("groups") or {}

        self.base_group_names = list(base_defs.keys())
        self.group_group_names = list(group_defs.keys())

        self.group_defs = {}
        self.group_defs.update(base_defs)
        self.group_defs.update(group_defs)

        self.group_extends = {}
        for name, definition in self.group_defs.items():
            if not isinstance(definition, dict):
                raise ValueError(f"定位器分组必须是字典: {name}")
            self.group_extends[name] = self._normalize_extends(definition.get("extends"))

    def _normalize_extends(self, raw_extends: Any) -> List[str]:
        if not raw_extends:
            return []
        if isinstance(raw_extends, str):
            raw_list = [raw_extends]
        elif isinstance(raw_extends, list):
            raw_list = raw_extends
        else:
            raise ValueError("extends 必须是字符串或字符串数组")

        result: List[str] = []
        for ref in raw_list:
            result.extend(self._resolve_group_ref(ref))
        return result

    def _resolve_group_ref(self, ref: Any) -> List[str]:
        if not isinstance(ref, str):
            raise ValueError("extends 引用必须是字符串")
        ref = ref.strip()
        if not ref:
            return []
        if ref == "base":
            return list(self.base_group_names)
        if ref == "groups":
            return list(self.group_group_names)
        if ref.startswith("base."):
            return [ref.split(".", 1)[1]]
        if ref.startswith("groups."):
            return [ref.split(".", 1)[1]]
        return [ref]

    def _expand_groups(self, group_names: Iterable[str]) -> List[str]:
        visited: set[str] = set()
        visiting: set[str] = set()
        order: List[str] = []

        def dfs(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"定位器分组存在循环继承: {name}")
            if name not in self.group_defs:
                raise ValueError(f"未知定位器分组: {name}")
            visiting.add(name)
            for parent in self.group_extends.get(name, []):
                dfs(parent)
            visiting.remove(name)
            visited.add(name)
            order.append(name)

        for name in group_names:
            dfs(name)

        return order

    def _flatten_group(self, group_name: str) -> Dict[str, List[str]]:
        definition = self.group_defs.get(group_name) or {}
        return self._flatten_locators(definition, prefix=group_name)

    def _flatten_locators(self, data: Any, prefix: str) -> Dict[str, List[str]]:
        flat: Dict[str, List[str]] = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if key in self.META_KEYS:
                    continue
                child_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    flat.update(self._flatten_locators(value, child_prefix))
                elif isinstance(value, list):
                    selectors = self._normalize_selector_list(value)
                    if selectors:
                        flat[child_prefix] = selectors
                elif isinstance(value, str):
                    flat[child_prefix] = [value]
        return flat

    def _normalize_selector_list(self, value: List[Any]) -> List[str]:
        return [item for item in value if isinstance(item, str) and item.strip()]

    def _normalize_flat_locators(self, raw: Dict[str, Any]) -> Dict[str, List[str]]:
        flat: Dict[str, List[str]] = {}
        for key, value in raw.items():
            if isinstance(value, list):
                selectors = self._normalize_selector_list(value)
                if selectors:
                    flat[key] = selectors
            elif isinstance(value, str):
                flat[key] = [value]
        return flat

    def _merge_flat(
        self,
        base: Dict[str, List[str]],
        extra: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        merged = dict(base)
        for key, selectors in extra.items():
            if key not in merged:
                merged[key] = selectors
            else:
                merged[key] = self._dedupe_list(merged[key] + selectors)
        return merged

    def _filter_by_context(self, flat: Dict[str, List[str]], context: List[str]) -> Dict[str, List[str]]:
        prefixes = [item for item in context if isinstance(item, str) and item.strip()]
        if not prefixes:
            return flat

        filtered: Dict[str, List[str]] = {}
        for key, selectors in flat.items():
            if any(key == prefix or key.startswith(f"{prefix}.") for prefix in prefixes):
                filtered[key] = selectors
        return filtered

    def _apply_aliases(
        self,
        flat: Dict[str, List[str]],
        strict: bool = True,
    ) -> Dict[str, List[str]]:
        merged = dict(flat)
        for alias, target in self.aliases.items():
            targets = target if isinstance(target, list) else [target]
            selectors: List[str] = []
            for path in targets:
                if not isinstance(path, str):
                    continue
                if path not in flat:
                    if strict:
                        raise ValueError(f"别名目标未找到: {alias} -> {path}")
                    continue
                selectors.extend(flat[path])
            if selectors:
                merged[alias] = self._dedupe_list(selectors)
        return merged

    def _dedupe_list(self, items: List[str]) -> List[str]:
        seen = set()
        result = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result
