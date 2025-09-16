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
#   - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (set strong password!)
#   - OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_EMBEDDING_MODEL
#   - LOG_LEVEL (optional)

# 6. Verify installation (optional)
python -c "import langgraph, neo4j, chromadb, fastapi, dotenv, spacy; print('Environment OK')"
```

Refer to `DEVOPS_PLAN.md` for deeper environment details.

## Usage

### Data Ingestion

Place source documents into the `data/` folder then run:

```bash
python -m scripts.ingest_data --source_dir data
```

### Ask the Agent via CLI

```bash
# Interactive mode
python -m src.main

# Single question mode
python -m src.main --question "What is the capital of France?"
```

### Health Monitoring & API

Start the comprehensive API server:

```bash
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

#### Health Endpoints

- **Liveness**: `GET /health/live` - Basic process health
- **Readiness**: `GET /health/ready` - Checks all dependencies (Neo4j, ChromaDB, Ollama)

#### Metrics & Monitoring

- **Metrics**: `GET /metrics/` - Performance metrics and counters
- **Dashboard**: `GET /metrics/dashboard` - Interactive HTML dashboard
- **Health Score**: `GET /metrics/health` - System health score and status
- **Reset**: `POST /metrics/reset` - Reset metrics (testing)

#### Documentation

- **API Docs**: `GET /docs` - Interactive Swagger UI
- **ReDoc**: `GET /redoc` - Alternative documentation
- **OpenAPI**: `GET /openapi.json` - OpenAPI schema
- **Troubleshooting**: `GET /docs/troubleshooting` - Common issues guide

#### Examples

```bash
# Health checks
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live

# Metrics
curl http://localhost:8000/metrics/
curl http://localhost:8000/metrics/health

# Open dashboard in browser
open http://localhost:8000/metrics/dashboard
```

### Performance Features

The system now includes advanced performance optimizations:

- **🚀 Async/Await Support**: Non-blocking operations for better throughput
- **💾 Intelligent Caching**: Reduces redundant computations with smart caching
- **🔧 Query Optimization**: Automatic query performance improvements
- **🧠 Memory Management**: Automatic cleanup and garbage collection
- **📊 Comprehensive Monitoring**: Real-time metrics and health scoring
- **🔌 Connection Pooling**: Optimized database connections
- **⚡ Concurrent Execution**: Parallel tool execution for faster responses
