import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from keyword_dsl.parser import parse_dsl


def test_parse_minimal_case():
    dsl = """
CASE "DEMO"
  STEP open url="https://example.com"
  STEP click target="nav.ai_create"
END
"""
    ast = parse_dsl(dsl, source_path="demo.dsl")
    assert ast.cases[0].name == "DEMO"
    assert ast.cases[0].statements[0].keyword == "open"
    assert ast.cases[0].statements[1].params["target"] == "nav.ai_create"
