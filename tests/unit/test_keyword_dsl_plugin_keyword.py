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


def test_compile_plugin_keyword():
    case = DslCase(
        name="DEMO",
        source=SourceRef("demo.dsl", 1),
        statements=[
            DslStatement("step", "aigc.generate", {"mode": "storyboard"}, SourceRef("demo.dsl", 2)),
        ],
    )
    registry = KeywordRegistry()
    registry.register(
        KeywordSpec(
            name="aigc.generate",
            action="plugin_action",
            required_params=["mode"],
            is_plugin=True,
            plugin_name="aigc",
        )
    )
    packs = LocatorPackRegistry({})

    workflow = compile_case(case, registry, packs)
    assert workflow.phases[0].steps[0].get_step_name() == "plugin_action"
    assert workflow.phases[0].steps[0].params["plugin"] == "aigc"
