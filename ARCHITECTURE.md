# Cognitive Orchestration Stack – High-Level Architecture

The stack is organized into **four tightly-coupled layers**, each responsible for a distinct concern in the system.  Data flows top-down (ingestion → knowledge → reasoning → orchestration) while control signals can propagate bidirectionally.

```text
┌─────────────────┐     ┌─────────────────────┐
│  Orchestration  │◀──▶│      Reasoning       │
└─────────────────┘     └─────────────────────┘
         ▲                        ▲
         │                        │
┌─────────────────┐     ┌─────────────────────┐
│    Knowledge    │◀──▶│      Ingestion       │
└─────────────────┘     └─────────────────────┘
```

## 1. Orchestration Layer

* **Technology:** LangGraph (Python)
* **Role:** Manages agent workflows as DAGs/state machines. Coordinates calls to the Reasoning layer and external tools, persists state, and handles retries & error strategies.

## 2. Reasoning Layer

* **Technology:** Ollama-served LLMs (e.g., Llama-3-8B-Instruct-Q4_K).
* **Role:** Provides core language reasoning. Encapsulated behind a small inference service consumed by LangGraph.

## 3. Knowledge Layer

* **Technologies:**
  * **Neo4j Community Edition** – structured knowledge graph for entities & relations.
  * **ChromaDB** – vector store for unstructured embeddings.
* **Role:** Supplies retrieval-augmented generation (RAG) context to the Reasoning layer via graph + dense retrieval.

## 4. Ingestion Layer

* **Technology:** LlamaIndex ingestion pipelines.
* **Role:** Extracts, cleans, and indexes external documents into Neo4j & ChromaDB. Handles scheduled re-ingestion.

## Data Flow Summary

1. Documents enter via Ingestion → nodes in Neo4j + embeddings in ChromaDB.
2. Orchestration receives a user request, identifies task graph.
3. Reasoning queries Knowledge layer for contextual data using LangGraph callbacks.
4. Response is synthesized and returned upstream.

**Non-negotiable libraries** are defined in `.cursor/rules/01-core-tech-stack.mdc` (see governance rules).
