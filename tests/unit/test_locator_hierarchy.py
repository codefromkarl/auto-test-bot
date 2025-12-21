import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from utils.locator_hierarchy import LocatorHierarchyCompiler


def _sample_hierarchy():
    return {
        "base": {
            "navigation": {
                "nav_home_tab": ["#home"],
            },
            "feedback": {
                "loading_indicator": [".loading"],
            },
        },
        "groups": {
            "prompt_engine": {
                "extends": "base.navigation",
                "input_area": {
                    "main_input": ["#prompt"],
                },
            },
            "image_studio": {
                "extends": "groups.prompt_engine",
                "generation": {
                    "generate_button": ["#gen"],
                },
            },
            "video_workflow": {
                "extends": "groups.prompt_engine",
                "timeline": {
                    "main_timeline": ["#timeline"],
                },
            },
        },
        "page_mapping": {
            "text_to_image": {
                "extends": "groups.image_studio",
                "context": [
                    "prompt_engine.input_area",
                    "image_studio.generation",
                ],
            },
        },
        "aliases": {
            "prompt_input": "prompt_engine.input_area.main_input",
            "generate_image_button": "image_studio.generation.generate_button",
        },
    }


def test_compile_hierarchy_with_aliases():
    compiler = LocatorHierarchyCompiler(_sample_hierarchy())
    compiled = compiler.compile()

    assert compiled["navigation.nav_home_tab"] == ["#home"]
    assert compiled["prompt_engine.input_area.main_input"] == ["#prompt"]
    assert compiled["image_studio.generation.generate_button"] == ["#gen"]
    assert compiled["prompt_input"] == ["#prompt"]
    assert compiled["generate_image_button"] == ["#gen"]


def test_compile_page_context_filters_keys():
    compiler = LocatorHierarchyCompiler(_sample_hierarchy())
    compiled = compiler.compile(page="text_to_image", strict_aliases=False)

    assert "prompt_engine.input_area.main_input" in compiled
    assert "image_studio.generation.generate_button" in compiled
    assert "video_workflow.timeline.main_timeline" not in compiled
