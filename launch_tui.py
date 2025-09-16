#!/usr/bin/env python3
"""
Production launcher for the Cognitive Orchestration Stack TUI.

This script provides a robust way to launch the TUI with proper error handling,
logging, and system checks.
"""

import sys
import os
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import textual
        print("✓ Textual is installed")
    except ImportError:
        print("❌ Textual is not installed. Run: poetry install")
        return False

    return True


def check_environment():
    """Check if the environment is properly set up."""
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Not in project root directory")
        return False

    # Check if src directory exists
    if not Path("src/tui").exists():
        print("❌ TUI source directory not found")
        return False

    print("✓ Environment check passed")
    return True


def launch_tui():
    """Launch the TUI application."""
    try:
        # Add src to Python path
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        # Import and run the TUI
        from src.tui.app import main
        main()

    except KeyboardInterrupt:
        print("\n👋 TUI closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to launch TUI: {e}")
        sys.exit(1)


def main():
    """Main launcher function."""
    print("🚀 Launching Cognitive Orchestration Stack TUI...")
    print()

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    print("✓ All checks passed")
    print("🎯 Starting TUI...")
    print()

    # Launch the TUI
    launch_tui()


if __name__ == "__main__":
    main()
