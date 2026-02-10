from __future__ import annotations

import re
from typing import Any, Callable, Mapping


_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")
_DOT_SELECTOR_RE = re.compile(r"^\.([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*)$")


def resolve_semantic_value(
    value: Any,
    *,
    lookup: Callable[[str], Any],
    selectors: Mapping[str, Any] | None = None,
) -> Any:
    """
    Resolve semantic variables inside `value`.

    Supported forms:
    - `.xxx` / `.a.b.c`          -> selector shorthand (from adapter selectors mapping)
    - `${path.to.value}`         -> template placeholder lookup (type-preserving when whole string)
    """
    if isinstance(value, dict):
        return {k: resolve_semantic_value(v, lookup=lookup, selectors=selectors) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_semantic_value(v, lookup=lookup, selectors=selectors) for v in value]
    if not isinstance(value, str):
        return value

    if selectors:
        m = _DOT_SELECTOR_RE.match(value.strip())
        if m:
            key = m.group(1)
            if key in selectors:
                return selectors[key]

    matches = list(_PLACEHOLDER_RE.finditer(value))
    if not matches:
        return value

    if len(matches) == 1 and matches[0].span() == (0, len(value)):
        path = matches[0].group(1).strip()
        resolved = lookup(path)
        if resolved is None:
            raise KeyError(f"Unresolved template variable: {path}")
        return resolved

    def repl(match: re.Match) -> str:
        path = match.group(1).strip()
        resolved = lookup(path)
        if resolved is None:
            raise KeyError(f"Unresolved template variable: {path}")
        return str(resolved)

    return _PLACEHOLDER_RE.sub(repl, value)
