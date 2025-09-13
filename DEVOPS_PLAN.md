# DevOps & Environment Plan

## Python Environment

* Target Version: **Python 3.11+**
* Isolation: **`python -m venv venv`** created in project root.
* Activation (Windows PowerShell): `venv\Scripts\Activate.ps1`
* A `requirements.txt` will be maintained; pin exact versions via `pip freeze > requirements.txt`.

## Dependency Management

| Category | Package |
|----------|---------|
| Orchestration | langgraph |
| LLM Serving | ollama-python |
| Knowledge Graph | neo4j |
| Vector Store | chromadb |
| Ingestion | llama-index |
| API Layer | fastapi, uvicorn |
| Testing | pytest, coverage, pytest-asyncio |

## Configuration

All runtime settings live in `config.py`, which will load from environment variables. A template `.env.example` will be provided.

## Continuous Integration (Future Phase)

A GitHub Actions workflow will run linting (`ruff`), tests, and coverage gates on each push.
