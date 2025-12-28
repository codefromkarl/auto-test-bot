import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from keyword_dsl.registry import KeywordRegistry, KeywordSpec


def test_registry_validates_required_params():
    registry = KeywordRegistry()
    registry.register(KeywordSpec(name="open", action="open_page", required_params=["url"]))
    spec = registry.get("open")
    with pytest.raises(ValueError):
        spec.validate({})
