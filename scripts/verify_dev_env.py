#!/usr/bin/env python3
"""
Development Environment Verification Script

This script verifies that the dev.env file exists and is properly configured.
Run this before any major operations to ensure your environment is set up.
"""

import os
from pathlib import Path

def verify_dev_environment():
    """Verify that the development environment is properly set up."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / "dev.env"
    
    print("🔍 Verifying development environment...")
    print("=" * 50)
    
    # Check if dev.env exists
    if not env_file.exists():
        print("❌ CRITICAL: config/dev.env file is missing!")
        print("   This file contains your API keys and passwords.")
        print("   Run: python scripts/setup_dev_env.py")
        return False
    
    print("✅ config/dev.env file exists")
    
    # Check if it's properly gitignored
    try:
        import subprocess
        result = subprocess.run(
            ["git", "check-ignore", str(env_file)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            print("✅ dev.env is properly gitignored")
        else:
            print("⚠️  WARNING: dev.env is not gitignored!")
            print("   This is a security risk - the file will be committed to git!")
            return False
    except Exception as e:
        print(f"⚠️  Could not verify gitignore status: {e}")
    
    # Check if it has actual values (not template values)
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            
        if "your_neo4j_password_here" in content:
            print("⚠️  WARNING: dev.env still contains template values!")
            print("   Please edit config/dev.env with your actual API keys")
            return False
        else:
            print("✅ dev.env appears to have real configuration values")
            
    except Exception as e:
        print(f"❌ Error reading dev.env: {e}")
        return False
    
    print("=" * 50)
    print("🎉 Development environment is properly configured!")
    return True

if __name__ == "__main__":
    success = verify_dev_environment()
    exit(0 if success else 1)
