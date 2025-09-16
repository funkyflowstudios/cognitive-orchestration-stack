#!/usr/bin/env python3
"""Test the fix for hanging issues."""

import signal
import sys

# Add current directory to path
sys.path.insert(0, '.')


def timeout_handler(signum, frame):
    print("TIMEOUT: Test took too long - likely still hanging")
    sys.exit(1)


def test_imports():
    """Test importing the problematic modules."""
    print("Testing imports...")

    try:
        # Test basic imports
        from src.orchestration.state import AgentState
        print("✓ AgentState imported")

        from src.orchestration.graph import GRAPH
        print("✓ GRAPH imported")

        # Test creating a state
        state = AgentState(query="test")
        print(f"✓ State created: {state.query}")

        # Test graph methods exist
        print(f"✓ GRAPH has invoke: {hasattr(GRAPH, 'invoke')}")
        print(f"✓ GRAPH has ainvoke: {hasattr(GRAPH, 'ainvoke')}")

        return True

    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_execution():
    """Test simple graph execution."""
    print("\nTesting simple execution...")

    try:
        from src.orchestration.graph import GRAPH
        from src.orchestration.state import AgentState

        # Create a simple state
        state = AgentState(query="test query")

        # Test that we can call invoke without hanging
        print("Calling GRAPH.invoke...")
        result = GRAPH.invoke(state)
        print(f"✓ GRAPH.invoke completed: {type(result)}")

        return True

    except Exception as e:
        print(f"✗ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("=== Testing Fix for Hanging Issues ===\n")

    # Set up timeout (30 seconds)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)

    try:
        # Test imports
        if not test_imports():
            print("Import test failed")
            return False

        # Test simple execution
        if not test_simple_execution():
            print("Execution test failed")
            return False

        print("\n✓ All tests passed - no hanging detected")
        return True

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
