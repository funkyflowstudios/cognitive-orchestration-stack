#!/usr/bin/env python
"""Check if required services are running."""

import socket
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings

def check_port(host, port, service_name):
    """Check if a service is running on the specified host and port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

def main():
    """Check all required services."""
    settings = get_settings()

    print("🔍 Checking required services...")
    print("=" * 50)

    # Check Ollama
    ollama_host = \
    settings.ollama_host.replace("http://", "").replace("https://", "")
    if ":" in ollama_host:
        host, port = ollama_host.split(":")
        port = int(port)
    else:
        host = ollama_host
        port = 11434

    ollama_running = check_port(host, port, "Ollama")
    print(f"🤖 Ollama ({host}:{port}): {'✅ Running' if ollama_running else '❌ Not running'}")

    # Check Neo4j
    neo4j_uri = \
    settings.neo4j_uri.replace("bolt://", "").replace("neo4j://", "")
    if ":" in neo4j_uri:
        host, port = neo4j_uri.split(":")
        port = int(port)
    else:
        host = neo4j_uri
        port = 7687

    neo4j_running = check_port(host, port, "Neo4j")
    print(f"🕸️  Neo4j ({host}:{port}): {'✅ Running' if neo4j_running else '❌ Not running'}")

    # Check ChromaDB (default port 8000)
    chromadb_running = check_port("localhost", 8000, "ChromaDB")
    print(f"🗄️  ChromaDB (localhost:8000): {'✅ Running' if chromadb_running else '❌ Not running'}")

    print("=" * 50)

    if not (ollama_running and neo4j_running and chromadb_running):
        print("⚠️  Some services are not running. Please start them before using ingestion.")
        print("\nTo start services:")
        print("1. Ollama: Download and run Ollama from https://ollama.ai")
        print("2. Neo4j: Download and run Neo4j Desktop or Community Edition")
        print("3. ChromaDB: Run 'pip install chromadb' and start the server")
        return False
    else:
        print("✅ All services are running! You can now use ingestion.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
