#!/usr/bin/env python3
"""Run minimal test and write output to file."""

import subprocess
import sys
import os

# Change to the project directory
os.chdir(r'D:\Projektit\agent_stack')

try:
    # Run the minimal test and capture output
    result = subprocess.run([
        sys.executable, 'test_minimal.py'
    ], capture_output=True, text=True, timeout=30)

    # Write results to file
    with open('test_results.txt', 'w') as f:
        f.write(f"Return code: {result.returncode}\n")
        f.write(f"STDOUT:\n{result.stdout}\n")
        f.write(f"STDERR:\n{result.stderr}\n")

    print("Test completed, results written to test_results.txt")

except subprocess.TimeoutExpired:
    with open('test_results.txt', 'w') as f:
        f.write("Test timed out after 30 seconds\n")
    print("Test timed out")

except Exception as e:
    with open('test_results.txt', 'w') as f:
        f.write(f"Error running test: {e}\n")
    print(f"Error: {e}")
