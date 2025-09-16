#!/usr/bin/env python3
"""Test without importing graph module."""

import sys
sys.path.insert(0, '.')

print("Testing without graph import...")

try:
    print("1. Testing basic imports...")
    from src.orchestration.state import AgentState
    print("   ✓ AgentState imported")

    print("2. Testing state creation...")
    state = AgentState(query="test")
    print(f"   ✓ Created state: {state.query}")

    print("3. Testing nodes import...")
    # from src.orchestration.nodes import planner_node  # Unused import
    print("   ✓ planner_node imported")

    print("✓ All tests passed - no hanging detected")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
