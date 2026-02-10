from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Optional, Type

from .protocol.adapter import AdapterProtocol


@dataclass(frozen=True)
class AdapterLoadSpec:
    module: str
    cls_name: Optional[str] = None


def _parse_adapter_spec(spec: Optional[str]) -> AdapterLoadSpec:
    raw = (spec or "").strip()
    if not raw:
        return AdapterLoadSpec(module="adapters.default.adapter", cls_name="DefaultAdapter")

    # `module:ClassName`
    if ":" in raw:
        mod, cls_name = raw.split(":", 1)
        return AdapterLoadSpec(module=mod.strip(), cls_name=cls_name.strip() or None)

    # `package.module.ClassName`
    if "." in raw and raw.split(".")[-1][:1].isupper():
        parts = raw.split(".")
        return AdapterLoadSpec(module=".".join(parts[:-1]), cls_name=parts[-1])

    # `naohai` -> `adapters.naohai.adapter`
    return AdapterLoadSpec(module=f"adapters.{raw}.adapter", cls_name=None)


def load_adapter(spec: Optional[str]) -> AdapterProtocol:
    """
    Dynamically load an adapter.

    Supported spec formats:
    - `naohai`  -> imports `adapters.naohai.adapter` and finds an AdapterProtocol implementation
    - `adapters.naohai.adapter:NaohaiAdapter`
    - `adapters.naohai.adapter.NaohaiAdapter`
    """
    load_spec = _parse_adapter_spec(spec)
    module = importlib.import_module(load_spec.module)

    if load_spec.cls_name:
        adapter_cls: Type[Any] = getattr(module, load_spec.cls_name)
        instance = adapter_cls()
        if not isinstance(instance, AdapterProtocol):
            raise TypeError(f"{load_spec.module}:{load_spec.cls_name} is not an AdapterProtocol")
        return instance

    for _, obj in vars(module).items():
        if not inspect.isclass(obj):
            continue
        if issubclass(obj, AdapterProtocol) and obj is not AdapterProtocol and not inspect.isabstract(obj):
            return obj()

    raise ImportError(f"No AdapterProtocol implementation found in {load_spec.module}")
