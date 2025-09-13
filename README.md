# Cognitive Orchestration Stack

A modular, multi-layer stack for large-language-model cognitive workflows, built on LangGraph, Ollama, Neo4j, ChromaDB, and FastAPI.

## Getting Started

Follow these steps on your local machine:

```bash
# 1. Clone repository (if you haven't already)
git clone <repo-url>
cd agent_stack

# 2. Create Python 3.11 virtual environment
python -m venv venv

# 3. Activate the environment
# Windows PowerShell
venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure environment variables
cp env.example .env  # copy template
# Open .env and fill in:
#   - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
#   - OLLAMA_HOST, OLLAMA_MODEL (optional)
#   - LOG_LEVEL (optional)

# 6. Verify installation (optional)
python -c "import langgraph, neo4j, chromadb, fastapi, dotenv, spacy; print('Environment OK')"
```

Refer to `DEVOPS_PLAN.md` for deeper environment details.

## Usage
