#!/usr/bin/env python3
"""Verify the fix works by running a simple test."""

import subprocess
import sys
import os



def run_test_with_timeout():
    """Run the test with a timeout."""
    try:
        # Change to the project directory
        os.chdir(r'D:\Projektit\agent_stack')

        # Run the test
        result = subprocess.run([
            sys.executable, 'test_fix.py'
        ], capture_output=True, text=True, timeout=30)

        # Write results
        with open('fix_verification.txt', 'w') as f:
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"STDOUT:\n{result.stdout}\n")
            f.write(f"STDERR:\n{result.stderr}\n")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        with open('fix_verification.txt', 'w') as f:
            f.write("Test timed out after 30 seconds - fix did not work\n")
        return False
    except Exception as e:
        with open('fix_verification.txt', 'w') as f:
            f.write(f"Error running test: {e}\n")
        return False



if __name__ == "__main__":
    print("Verifying fix...")
    success = run_test_with_timeout()
    if success:
        print("✓ Fix verified - tests should work now")
    else:
        print("✗ Fix verification failed - check fix_verification.txt")
    sys.exit(0 if success else 1)
