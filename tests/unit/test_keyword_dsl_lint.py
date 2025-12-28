import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from keyword_dsl.lint import lint_dsl_text


def test_rejects_selector_usage():
    dsl = """
CASE "DEMO"
  STEP click selector="#bad"
END
"""
    errors = lint_dsl_text(dsl)
    assert "selector" in errors[0]
