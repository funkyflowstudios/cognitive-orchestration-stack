#!/usr/bin/env python3
"""Security testing script using Bandit for the Cognitive Orchestration Stack."""

import subprocess
import sys
from pathlib import Path

def run_bandit():
    """Run Bandit security analysis."""
    print("Running Bandit security analysis...")

    # Run Bandit on the source code
    cmd = [
        "bandit",
        "-r", "src/",
        "-f", "json",
        "-o", "security-results.json"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Bandit security analysis completed successfully")
            print("No security issues found")
            return True
        else:
            print("Bandit security analysis found issues:")
            print(result.stdout)
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("Bandit not found. Please install it with: pip install bandit")
        return False

def run_safety():
    """Run Safety to check for known security vulnerabilities in dependencies."""
    print("Running Safety dependency vulnerability check...")

    cmd = ["safety", "check", "--json", "--output", "safety-results.json"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Safety check completed successfully")
            print("No known vulnerabilities found in dependencies")
            return True
        else:
            print("Safety check found vulnerabilities:")
            print(result.stdout)
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("Safety not found. Please install it with: pip install safety")
        return False

def main():
    """Main function."""
    print("Starting security testing...")

    # Change to project root directory
    project_root = Path(__file__).parent.parent.parent
    import os
    os.chdir(project_root)

    # Run security tests
    bandit_success = run_bandit()
    safety_success = run_safety()

    if bandit_success and safety_success:
        print("All security tests passed!")
        sys.exit(0)
    else:
        print("Security tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
