import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from keyword_dsl.locator_packs import LocatorPackRegistry


def test_resolve_locator_key():
    packs = LocatorPackRegistry({"demo": {"nav.ai_create": "#nav-ai"}})
    assert packs.resolve("demo", "nav.ai_create") == "#nav-ai"
