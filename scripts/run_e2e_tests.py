#!/usr/bin/env python3
"""Script to run End-to-End tests with Docker services."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result

def check_docker():
    """Check if Docker is available."""
    try:
        run_command(["docker", "--version"])
        run_command(["docker-compose", "--version"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Docker or docker-compose not found. Please install Docker.")
        return False

def start_services():
    """Start E2E test services."""
    print("Starting E2E test services...")
    docker_compose_file = \
    Path(__file__).parent.parent / "tests" / "e2e" / "docker-compose.e2e.yml"

    run_command([
        "docker-compose",
        "-f", str(docker_compose_file),
        "up", "-d"
    ])

    print("Waiting for services to be ready...")
    time.sleep(30)  # Give services time to start

def stop_services():
    """Stop E2E test services."""
    print("Stopping E2E test services...")
    docker_compose_file = \
    Path(__file__).parent.parent / "tests" / "e2e" / "docker-compose.e2e.yml"

    run_command([
        "docker-compose",
        "-f", str(docker_compose_file),
        "down"
    ], check=False)

def run_e2e_tests(verbose=False, specific_test=None):
    """Run the E2E tests."""
    print("Running E2E tests...")

    cmd = ["python", "-m", "pytest", "tests/e2e/"]

    if verbose:
        cmd.append("-v")

    if specific_test:
        cmd.append(specific_test)

    cmd.extend(["-s", "--tb=short"])

    result = run_command(cmd, check=False)
    return result.returncode == 0

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run End-to-End tests")
    parser.add_argument("-v", "--verbose", action="store_true",
    help="Verbose output")
    parser.add_argument("-t", "--test", help="Run specific test")
    parser.add_argument("--no-docker", action="store_true",
    help="Skip Docker setup (assume services are running)")
    parser.add_argument("--keep-services", action="store_true",
    help="Keep services running after tests")

    args = parser.parse_args()

    if not args.no_docker:
        if not check_docker():
            sys.exit(1)

        try:
            start_services()
            success = run_e2e_tests(args.verbose, args.test)
        finally:
            if not args.keep_services:
                stop_services()
    else:
        print("Skipping Docker setup - assuming services are already running")
        success = run_e2e_tests(args.verbose, args.test)

    if success:
        print("E2E tests passed!")
        sys.exit(0)
    else:
        print("E2E tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
