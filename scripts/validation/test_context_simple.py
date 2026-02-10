#!/usr/bin/env python3
"""Simple test for Context class"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.models import Context


def test_context():
    """Test Context class methods"""
    print("Testing Context class...")

    # Create context
    context = Context()

    # Test initial state
    assert context.current_phase is None
    assert context.current_step is None
    assert context.current_url is None
    assert context.is_error_state() is False
    print("✓ Initial state test passed")

    # Test state updates
    context.update_phase("navigation")
    assert context.current_phase == "navigation"
    print("✓ Phase update test passed")

    context.update_step("open_page")
    assert context.current_step == "open_page"
    print("✓ Step update test passed")

    context.update_url("http://example.com")
    assert context.current_url == "http://example.com"
    print("✓ URL update test passed")

    # Test data storage
    context.set_data("last_click", {"selector": "#button", "time": 1234567890})
    assert context.get_data("last_click")["selector"] == "#button"
    print("✓ Data storage test passed")

    # Test error state
    context.set_error(
        {"type": "TIMEOUT", "message": "Element not found"}, "step_timeout"
    )
    assert context.is_error_state() is True
    assert context.last_error["type"] == "TIMEOUT"
    print("✓ Error state test passed")

    # Test error recovery
    context.clear_error()
    assert context.is_error_state() is False
    assert context.last_error is None
    print("✓ Error recovery test passed")

    # Test snapshot
    snapshot = context.create_snapshot()
    assert "state" in snapshot
    assert "data" in snapshot
    assert "timestamp" in snapshot
    print("✓ Snapshot creation test passed")

    # Test restore from snapshot
    new_context = Context()
    new_context.restore_from_snapshot(snapshot)
    assert new_context.current_phase == "navigation"
    assert new_context.current_step == "open_page"
    print("✓ Snapshot restore test passed")

    print("\n✅ All Context tests passed!")


if __name__ == "__main__":
    test_context()
