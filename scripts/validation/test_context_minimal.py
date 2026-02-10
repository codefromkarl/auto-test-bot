#!/usr/bin/env python3
"""Minimal test for Context class without locks"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Test without locks first
try:
    from src.models import Context

    print("Testing Context import...")

    # Simple test without any operations that might cause locks
    context = Context()
    print("Context created successfully")

    # Test basic properties
    print(f"current_phase: {context.current_phase}")
    print(f"current_step: {context.current_step}")
    print(f"current_url: {context.current_url}")
    print(f"is_error_state: {context.is_error_state()}")

    # Test simple state operations
    context._state["test"] = "value"
    print(f"State test: {context._state.get('test')}")

    print("✅ Basic Context test completed successfully")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
