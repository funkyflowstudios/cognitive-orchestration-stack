#!/usr/bin/env python3
"""Comprehensive test runner for all test types."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture_output, text=True)
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        if capture_output:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result

def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    print("=" * 50)
    print("Running Unit Tests")
    print("=" * 50)

    cmd = ["python", "-m", "pytest", "tests/unit/"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])

    result = run_command(cmd, check=False)
    return result.returncode == 0

def run_integration_tests(verbose=False):
    """Run integration tests."""
    print("=" * 50)
    print("Running Integration Tests")
    print("=" * 50)

    cmd = ["python", "-m", "pytest", "tests/integration/"]

    if verbose:
        cmd.append("-v")

    result = run_command(cmd, check=False)
    return result.returncode == 0

def run_e2e_tests(verbose=False, with_docker=True):
    """Run E2E tests."""
    print("=" * 50)
    print("Running End-to-End Tests")
    print("=" * 50)

    if with_docker:
        # Use the E2E test script
        cmd = ["python", "scripts/run_e2e_tests.py"]
        if verbose:
            cmd.append("-v")
    else:
        # Run E2E tests directly
        cmd = ["python", "-m", "pytest", "tests/e2e/"]
        if verbose:
            cmd.append("-v")

    result = run_command(cmd, check=False)
    return result.returncode == 0

def run_performance_tests(base_url="http://localhost:8000"):
    """Run performance tests using k6."""
    print("=" * 50)
    print("Running Performance Tests")
    print("=" * 50)

    cmd = [
        "k6", "run",
        "--env", f"BASE_URL={base_url}",
        "tests/e2e/performance_test.js"
    ]

    try:
        result = run_command(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("k6 not found. Please install it from https://k6.io/docs/getting-started/installation/")
        return False

def run_security_tests():
    """Run security tests."""
    print("=" * 50)
    print("Running Security Tests")
    print("=" * 50)

    cmd = ["python", "tests/e2e/security_test.py"]
    result = run_command(cmd, check=False)
    return result.returncode == 0

def run_linting():
    """Run code linting."""
    print("=" * 50)
    print("Running Code Linting")
    print("=" * 50)

    # Run Ruff
    cmd = ["ruff", "check", "src/", "tests/"]
    result1 = run_command(cmd, check=False)

    # Run Ruff formatting check
    cmd = ["ruff", "format", "--check", "src/", "tests/"]
    result2 = run_command(cmd, check=False)

    return result1.returncode == 0 and result2.returncode == 0

def run_type_checking():
    """Run type checking with mypy."""
    print("=" * 50)
    print("Running Type Checking")
    print("=" * 50)

    cmd = ["mypy", "src/"]
    result = run_command(cmd, check=False)
    return result.returncode == 0

def main():
    """Main function."""
    parser = \
    argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument("-v", "--verbose", action="store_true",
    help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true",
    help="Generate coverage report")
    parser.add_argument("--unit", action="store_true",
    help="Run only unit tests")
    parser.add_argument("--integration", action="store_true",
    help="Run only integration tests")
    parser.add_argument("--e2e", action="store_true",
    help="Run only E2E tests")
    parser.add_argument("--performance", action="store_true",
    help="Run only performance tests")
    parser.add_argument("--security", action="store_true",
    help="Run only security tests")
    parser.add_argument("--lint", action="store_true", help="Run only linting")
    parser.add_argument("--type-check", action="store_true",
    help="Run only type checking")
    parser.add_argument("--no-docker", action="store_true",
    help="Skip Docker for E2E tests")
    parser.add_argument("--base-url", default="http://localhost:8000",
    help="Base URL for performance tests")

    args = parser.parse_args()

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)

    results = {}

    # Run tests based on arguments
    if args.unit or \
    not any([args.integration, args.e2e, args.performance, args.security,
    args.lint,
    args.type_check]):
        results['unit'] = run_unit_tests(args.verbose, args.coverage)

    if args.integration or \
    not any([args.unit, args.e2e, args.performance, args.security, args.lint,
    args.type_check]):
        results['integration'] = run_integration_tests(args.verbose)

    if args.e2e or \
    not any([args.unit, args.integration, args.performance, args.security,
    args.lint,
    args.type_check]):
        results['e2e'] = run_e2e_tests(args.verbose, not args.no_docker)

    if args.performance or \
    not any([args.unit, args.integration, args.e2e, args.security, args.lint,
    args.type_check]):
        results['performance'] = run_performance_tests(args.base_url)

    if args.security or \
    not any([args.unit, args.integration, args.e2e, args.performance,
    args.lint,
    args.type_check]):
        results['security'] = run_security_tests()

    if args.lint or \
    not any([args.unit, args.integration, args.e2e, args.performance,
    args.security,
    args.type_check]):
        results['lint'] = run_linting()

    if args.type_check or \
    not any([args.unit, args.integration, args.e2e, args.performance,
    args.security,
    args.lint]):
        results['type_check'] = run_type_checking()

    # Print summary
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)

    all_passed = True
    for test_type, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{test_type.upper()}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll tests passed! 🎉")
        sys.exit(0)
    else:
        print("\nSome tests failed! ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()
