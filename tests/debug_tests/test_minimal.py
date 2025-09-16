#!/usr/bin/env python3
"""Minimal test to identify hanging issue."""

import sys
sys.path.insert(0, '.')

print("Starting minimal test...")

try:
    print("1. Testing basic imports...")
    from src.orchestration.state import AgentState
    print("   ✓ AgentState imported")

    from src.orchestration.graph import GRAPH
    print("   ✓ GRAPH imported")

    print("2. Testing basic functionality...")
    state = AgentState(query="test")
    print(f"   ✓ Created state: {state.query}")

    print("3. Testing graph compilation...")
    print(f"   ✓ GRAPH type: {type(GRAPH)}")
    print(f"   ✓ GRAPH has invoke: {hasattr(GRAPH, 'invoke')}")
    print(f"   ✓ GRAPH has ainvoke: {hasattr(GRAPH, 'ainvoke')}")

    print("4. Testing mock graph...")
    from tests.conftest import MockCompiledGraph
    mock_graph = MockCompiledGraph({}, [], "test")
    print("   ✓ Mock graph created")

    print("✓ All tests passed - no hanging detected")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
