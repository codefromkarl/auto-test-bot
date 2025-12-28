import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from keyword_dsl.ast import DslCase, DslStatement, SourceRef
from keyword_dsl.registry import KeywordRegistry, KeywordSpec
from keyword_dsl.locator_packs import LocatorPackRegistry
from keyword_dsl.compiler import compile_case


def test_compile_core_steps():
    case = DslCase(
        name="DEMO",
        source=SourceRef("demo.dsl", 1),
        locator_pack="demo",
        statements=[
            DslStatement("step", "open", {"url": "https://example.com"}, SourceRef("demo.dsl", 2)),
            DslStatement("step", "click", {"target": "nav.ai_create"}, SourceRef("demo.dsl", 3)),
        ],
    )
    registry = KeywordRegistry()
    registry.register(KeywordSpec(name="open", action="open_page", required_params=["url"]))
    registry.register(KeywordSpec(name="click", action="click", required_params=["target"]))
    packs = LocatorPackRegistry({"demo": {"nav.ai_create": "#nav-ai"}})

    workflow = compile_case(case, registry, packs)
    steps = workflow.phases[0].steps
    assert steps[0].get_step_name() == "open_page"
    assert steps[1].params["selector"] == "#nav-ai"
