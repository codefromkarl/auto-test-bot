import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import main_keyword_dsl

from keyword_dsl.ast import DslCase, DslStatement, SourceRef
from keyword_dsl.registry import KeywordRegistry, KeywordSpec
from keyword_dsl.locator_packs import LocatorPackRegistry
from keyword_dsl.compiler import compile_case


def test_entrypoint_compiles_case():
    case = DslCase(
        name="DEMO",
        source=SourceRef("demo.dsl", 1),
        statements=[DslStatement("step", "open", {"url": "https://example.com"}, SourceRef("demo.dsl", 2))],
    )
    registry = KeywordRegistry()
    registry.register(KeywordSpec(name="open", action="open_page", required_params=["url"]))
    packs = LocatorPackRegistry({})
    workflow = compile_case(case, registry, packs)
    assert workflow.name == "DEMO"
