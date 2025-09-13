# Testing Strategy

The project will employ **layered testing**:

1. **Unit Tests** – Target individual functions/modules.  Use `pytest` and follow Arrange-Act-Assert.  External services mocked with `unittest.mock`.
2. **Integration Tests** – Validate interactions between layers (e.g., LangGraph ↔ Neo4j, Reasoning ↔ Ollama stub).
3. **Contract Tests** – Ensure that each layer’s API (e.g., LangGraph node signature) meets agreed-upon schemas.
4. **End-to-End Smoke Tests** – Lightweight scenario validating full data flow.

Coverage threshold: **≥80 %** of business logic.
