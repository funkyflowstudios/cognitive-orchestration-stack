#!/usr/bin/env python3
"""Debug import issues."""

import sys
import traceback

# Add current directory to path
sys.path.insert(0, '.')


def test_import(module_name, description):
    """Test importing a module and report success/failure."""
    try:
        print(f"Testing {description}...")
        exec(f"import {module_name}")
        print(f"✓ {description} imported successfully")
        return True
    except Exception as e:
        print(f"✗ {description} failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Test all imports step by step."""
    print("=== Debugging Import Issues ===\n")

    # Test basic imports first
    basic_imports = [
        ("src.orchestration.state", "AgentState module"),
        ("src.orchestration.nodes", "Nodes module"),
        ("src.utils.logger", "Logger module"),
        ("src.config", "Config module"),
    ]

    for module, desc in basic_imports:
        if not test_import(module, desc):
            print(f"Stopping at {desc} - this is likely the problem")
            return

    print("\n--- Testing LangGraph import ---")
    try:
        # import langgraph  # Unused import removed
        print("✓ langgraph imported")

        from langgraph.graph import StateGraph
        print("✓ StateGraph imported")

        # Test creating a simple graph
        from src.orchestration.state import AgentState
        StateGraph(AgentState)
        print("✓ StateGraph builder created")

    except Exception as e:
        print(f"✗ LangGraph issue: {e}")
        traceback.print_exc()
        return

    print("\n--- Testing graph module import ---")
    try:
        from src.orchestration.graph import GRAPH
        print("✓ GRAPH imported successfully")
        print(f"GRAPH type: {type(GRAPH)}")
    except Exception as e:
        print(f"✗ Graph import failed: {e}")
        traceback.print_exc()
        return

    print("\n✓ All imports successful - no hanging detected")


if __name__ == "__main__":
    main()
