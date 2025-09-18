#!/usr/bin/env python3
"""
Development Environment Setup Script

This script helps you set up your development environment securely.
It copies the template file and guides you through the setup process.
"""

import os
import shutil
from pathlib import Path

def setup_dev_environment():
    """Set up development environment configuration."""
    project_root = Path(__file__).parent.parent
    template_file = project_root / "config" / "dev.env.template"
    env_file = project_root / "config" / "dev.env"
    
    print("🔧 Setting up development environment...")
    
    # Check if dev.env already exists
    if env_file.exists():
        print(f"⚠️  {env_file} already exists!")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Setup cancelled.")
            return False
    
    # Copy template to dev.env
    try:
        shutil.copy2(template_file, env_file)
        print(f"✅ Created {env_file}")
        print()
        print("🔐 SECURITY SETUP REQUIRED:")
        print("=" * 50)
        print("1. Edit config/dev.env with your actual API keys and passwords")
        print("2. The dev.env file is gitignored and will NOT be committed")
        print("3. Never share your dev.env file with anyone")
        print()
        print("📝 Required API Keys:")
        print("- NEO4J_PASSWORD: Your Neo4j database password")
        print("- SERPAPI_KEY: Get from https://serpapi.com/")
        print("- BRAVE_API_KEY: Get from https://brave.com/search/api/")
        print()
        print("🚀 After setup, run: poetry run cos")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up environment: {e}")
        return False

if __name__ == "__main__":
    setup_dev_environment()
