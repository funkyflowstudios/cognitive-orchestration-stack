# Test Suite Documentation

This directory contains the comprehensive test suite for the Cognitive Orchestration Stack, following the testing pyramid model with Unit, Integration, and End-to-End tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_utils.py       # Utilities testing
│   ├── test_orchestration_nodes.py  # Orchestration nodes testing
│   ├── test_orchestration_graph.py  # Orchestration graph testing
│   └── test_api_layer.py   # API layer testing
├── e2e/                    # End-to-End tests (slow, full system)
│   ├── test_full_system.py # Complete system E2E tests
│   ├── conftest.py         # E2E test configuration
│   ├── docker-compose.e2e.yml  # Docker services for E2E
│   ├── performance_test.js # k6 performance tests
│   └── security_test.py    # Security testing with Bandit
├── test_integration.py     # Integration tests (medium speed, component interaction)
├── test_api_health.py     # API health endpoint tests
├── test_api_metrics.py    # API metrics endpoint tests
├── test_config.py         # Configuration management tests
├── test_config_vault.py   # Vault integration tests
├── test_logging_config.py # Logging configuration tests
├── test_main.py           # Main application tests
├── test_orchestration.py  # Orchestration workflow tests
├── test_orchestration_graph.py  # Graph orchestration tests
├── test_orchestration_nodes.py  # Node processing tests
├── test_state.py          # State management tests
├── test_structured_logging.py  # Structured logging tests
├── test_tools_chromadb.py # ChromaDB tool tests
├── test_tools_neo4j.py    # Neo4j tool tests
├── test_utils_metrics.py  # Metrics utility tests
├── test_utils_retry.py    # Retry utility tests
├── test_utils_schema_validator.py  # Schema validation tests
└── conftest.py            # Global test configuration
```

## Running Tests

### All Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Unit Tests Only
```bash
python -m pytest tests/unit/ -v
```

### Integration Tests Only
```bash
python -m pytest tests/test_integration.py -v
```

### End-to-End Tests Only
```bash
# With Docker services
python scripts/run_e2e_tests.py

# Without Docker (assumes services are running)
python -m pytest tests/e2e/ -v
```

### Performance Tests
```bash
# Install k6 first: https://k6.io/docs/getting-started/installation/
k6 run tests/e2e/performance_test.js
```

### Security Tests
```bash
python tests/e2e/security_test.py
```

### Comprehensive Test Suite
```bash
# Run all test types
python scripts/run_all_tests.py

# Run specific test types
python scripts/run_all_tests.py --unit --integration
```

## Test Configuration

### Environment Variables
- `NEO4J_URI`: Neo4j connection URI (default: bolt://localhost:7687)
- `NEO4J_USER`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password (required)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model name (default: llama3)
- `OLLAMA_EMBEDDING_MODEL`: Ollama embedding model (required)

### Docker Services for E2E
The E2E tests use Docker Compose to spin up required services:
- Neo4j (port 7474, 7687)
- Ollama (port 11434)

ChromaDB uses local persistent storage and doesn't require a Docker service.

## Test Types

### Unit Tests
- **Purpose**: Test individual functions and classes in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Mocked external services
- **Coverage**: 100% of core business logic

### Integration Tests
- **Purpose**: Test interaction between components
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: Some real services, some mocked
- **Coverage**: Critical integration paths

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Speed**: Slow (5-30 seconds per test)
- **Dependencies**: Real external services
- **Coverage**: Critical user journeys

### Performance Tests
- **Purpose**: Validate system performance under load
- **Tool**: k6
- **Metrics**: Response time, throughput, error rate
- **Thresholds**: 95% of requests < 1s, error rate < 10%

### Security Tests
- **Purpose**: Identify security vulnerabilities
- **Tools**: Bandit (static analysis), Safety (dependency vulnerabilities)
- **Coverage**: All source code and dependencies

## Test Data Management

### Fixtures
- `reset_metrics_fixture`: Resets metrics between tests
- `reset_logger_singleton`: Ensures logger isolation
- `e2e_client`: FastAPI test client for E2E tests
- `wait_for_services`: Waits for external services to be ready

### Test Data
- Sample queries for testing orchestration workflows
- Sample documents for testing document ingestion
- Mock responses for external service calls

## Continuous Integration

### GitHub Actions
The CI pipeline runs on every push and pull request:
1. **Unit Tests**: Fast feedback on code changes
2. **Integration Tests**: Verify component interactions
3. **E2E Tests**: Full system validation with Docker services
4. **Performance Tests**: Load testing with k6
5. **Security Tests**: Vulnerability scanning
6. **Linting**: Code quality checks with Ruff
7. **Type Checking**: Static type analysis with mypy

### Test Reports
- Coverage reports generated in HTML format
- Performance test results in JSON format
- Security scan results in JSON format
- Test results published to Codecov

## Best Practices

### Writing Tests
1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive Names**: Test names should explain what they test
3. **Single Responsibility**: One test per behavior
4. **Independent Tests**: Tests should not depend on each other
5. **Fast Feedback**: Unit tests should be fast, E2E tests can be slower

### Test Data
1. **Isolated Data**: Each test should use its own data
2. **Cleanup**: Always clean up test data after tests
3. **Realistic Data**: Use realistic test data that matches production

### Mocking
1. **Mock External Dependencies**: Don't test external services in unit tests
2. **Verify Interactions**: Assert that mocked methods are called correctly
3. **Minimal Mocking**: Only mock what's necessary

## Troubleshooting

### Common Issues

#### Permission Errors
- **Issue**: File permission errors on Windows
- **Solution**: Ensure no other processes are using log files

#### Service Connection Errors
- **Issue**: E2E tests failing to connect to services
- **Solution**: Ensure Docker services are running and accessible

#### Import Errors
- **Issue**: Module import errors in tests
- **Solution**: Check Python path and virtual environment activation

#### Mock Failures
- **Issue**: Mocks not working as expected
- **Solution**: Verify mock setup and patch targets

### Debug Mode
```bash
# Run tests with debug output
python -m pytest tests/ -v -s --tb=long

# Run specific test with debug
python -m pytest tests/unit/test_utils.py::test_retry_decorator -v -s
```

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Add appropriate fixtures for test data
3. Ensure tests are independent and can run in any order
4. Update this documentation if adding new test types
5. Run the full test suite before submitting changes

## Test Metrics

- **Unit Test Coverage**: 100% of core business logic
- **Integration Test Coverage**: All critical integration paths
- **E2E Test Coverage**: All critical user journeys
- **Performance Thresholds**: 95% of requests < 1s
- **Security**: Zero high-severity vulnerabilities
