"""Test configuration and fixtures for the Cognitive Orchestration Stack.

This file provides comprehensive test fixtures, mocks, and configuration
for testing all components of the agent stack without requiring external
dependencies like Neo4j, ChromaDB, or Ollama.
"""

from __future__ import annotations

import asyncio
import os
import sys
from types import ModuleType
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.metrics import initialize_metrics

# ---------------------------------------------------------------------------
# Environment Setup
# ---------------------------------------------------------------------------

# Set test environment variables before any imports
os.environ.update({
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "test_password",
    "OLLAMA_HOST": "http://localhost:11434",
    "OLLAMA_MODEL": "llama3",
    "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text",
    "LOG_LEVEL": "DEBUG",
    "TESTING": "true"  # Flag to disable file logging during tests
})

# Initialize metrics system for testing
initialize_metrics()


# ---------------------------------------------------------------------------
# Mock External Dependencies
# ---------------------------------------------------------------------------

def _create_mock_module(name: str, **attrs) -> ModuleType:
    """Create a mock module with the given attributes."""
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


# Mock ChromaDB
if "chromadb" not in sys.modules:
    chromadb_module = _create_mock_module("chromadb")

    class MockCollection:
        """Mock ChromaDB Collection."""
        def __init__(self, name: str):
            self.name = name
            self._documents: List[str] = []
            self._embeddings: List[List[float]] = []
            self._metadatas: List[Dict[str, Any]] = []
            self._ids: List[str] = []

        def add(self, documents: List[str], embeddings: List[List[float]],
                metadatas: List[Dict[str, Any]], ids: List[str]) -> None:
            """Add documents to the collection."""
            self._documents.extend(documents)
            self._embeddings.extend(embeddings)
            self._metadatas.extend(metadatas)
            self._ids.extend(ids)

        def query(self, query_embeddings: List[List[float]], n_results: int = 5) -> Dict[str, Any]:
            """Query the collection."""
            return {
                "documents": [self._documents[:n_results]],
                "metadatas": [self._metadatas[:n_results]],
                "ids": [self._ids[:n_results]]
            }

        def count(self) -> int:
            """Get document count."""
            return len(self._documents)

    class MockChromaDBClient:
        """Mock ChromaDB Client."""
        def __init__(self, path: str | None = None):
            self._collections: Dict[str, MockCollection] = {}

        def create_collection(self, name: str) -> MockCollection:
            """Create a new collection."""
            collection = MockCollection(name)
            self._collections[name] = collection
            return collection

        def get_collection(self, name: str) -> MockCollection:
            """Get an existing collection."""
            if name not in self._collections:
                return self.create_collection(name)
            return self._collections[name]

        def list_collections(self) -> List[MockCollection]:
            """List all collections."""
            return list(self._collections.values())

        def delete_collection(self, name: str) -> None:
            """Delete a collection."""
            if name in self._collections:
                del self._collections[name]

    class MockPersistentClient(MockChromaDBClient):
        """Mock PersistentClient for ChromaDB."""
        def __init__(self, path: str | None = None):
            super().__init__(path)
            # Reset collections on each new instance
            self._collections.clear()

    # Set both Client and PersistentClient
    setattr(chromadb_module, "Client", MockChromaDBClient)
    setattr(chromadb_module, "PersistentClient", MockPersistentClient)


# Mock Neo4j
if "neo4j" not in sys.modules:
    _create_mock_module("neo4j")

    class MockNeo4jDriver:
        def __init__(self, uri: str, auth: tuple):
            self.uri = uri
            self.auth = auth
            self._closed = False

        def close(self) -> None:
            self._closed = True

        def verify_connectivity(self) -> None:
            """Mock verify_connectivity method."""
            pass

        def session(self, **kwargs):
            return MockNeo4jSession()

    class MockNeo4jSession:
        def __init__(self):
            self._closed = False

        def close(self) -> None:
            self._closed = True

        def run(self, query: str, parameters: Dict[str, Any] | None = None):
            return [MockNeo4jResult()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    class MockNeo4jResult:
        def __init__(self):
            self._records = [{"test": 1}]

        def __iter__(self):
            return iter(self._records)

        def data(self):
            return self._records[0] if self._records else {}

    class MockGraphDatabase:
        @staticmethod
        def driver(uri: str, auth: tuple[Any, ...] | None = None, **kwargs):
            return MockNeo4jDriver(uri, auth or ())

    setattr(sys.modules["neo4j"], "GraphDatabase", MockGraphDatabase)


# Mock Ollama
if "ollama" not in sys.modules:
    _create_mock_module("ollama")

    class MockOllamaClient:
        def __init__(self, host: str = "http://localhost:11434"):
            self.host = host

        def generate(self, model: str, prompt: str, **kwargs):
            return {
                "response": f"Mock response for: {prompt[:50]}...",
                "model": model,
                "done": True
            }

    setattr(sys.modules["ollama"], "Client", MockOllamaClient)


# Mock LlamaIndex
if "llama_index" not in sys.modules:
    llama_index_module = _create_mock_module("llama_index")

    class MockDocument:
        def __init__(self, text: str, metadata: Dict[str, Any] | None = None):
            self.text = text
            self.metadata = metadata or {}

    class MockOllamaEmbedding:
        def __init__(self, model_name: str, base_url: str):
            self.model_name = model_name
            self.base_url = base_url

        def get_text_embedding(self, text: str) -> List[float]:
            # Return a mock embedding vector
            return [0.1] * 384  # Common embedding dimension

    # Create submodules
    llama_index_core_module = _create_mock_module("llama_index.core")
    llama_index_embeddings_module = _create_mock_module("llama_index.embeddings")
    llama_index_embeddings_ollama_module = _create_mock_module("llama_index.embeddings.ollama")

    setattr(llama_index_core_module, "Document", MockDocument)
    setattr(llama_index_embeddings_ollama_module, "OllamaEmbedding", MockOllamaEmbedding)
    setattr(llama_index_embeddings_module, "ollama", llama_index_embeddings_ollama_module)
    setattr(llama_index_module, "core", llama_index_core_module)
    setattr(llama_index_module, "embeddings", llama_index_embeddings_module)


# Mock Unstructured
if "unstructured" not in sys.modules:
    _create_mock_module("unstructured")

    class MockElement:
        def __init__(self, text: str):
            self.text = text

    class MockPartition:
        @staticmethod
        def auto(file_path: str):
            return [MockElement(f"Mock content from {file_path}")]

    setattr(sys.modules["unstructured"], "partition", MockPartition)


# Mock spaCy
if "spacy" not in sys.modules:
    _create_mock_module("spacy")

    class MockDoc:
        def __init__(self, text: str):
            self.text = text
            self.ents = [MockEntity("Mock Entity", "PERSON")]

    class MockEntity:
        def __init__(self, text: str, label: str):
            self.text = text
            self.label_ = label

    class MockLanguage:
        def __call__(self, text: str):
            return MockDoc(text)

    def mock_load(model_name: str):
        return MockLanguage()

    setattr(sys.modules["spacy"], "load", mock_load)


# Mock httpx
if "httpx" not in sys.modules:
    httpx_module = _create_mock_module("httpx")

    class MockResponse:
        def __init__(self, status_code: int = 200, json_data: Dict[str, Any] | None = None):
            self.status_code = status_code
            self._json_data = json_data or {}

        def json(self):
            return self._json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    class MockClient:
        def __init__(self, **kwargs):
            pass

        def get(self, url: str, **kwargs):
            return MockResponse()

        def post(self, url: str, **kwargs):
            return MockResponse()

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def get(self, url: str, **kwargs):
            return MockResponse()

        async def post(self, url: str, **kwargs):
            return MockResponse()

    class MockBaseTransport:
        pass

    # Create httpx submodules
    httpx_client_module = _create_mock_module("httpx._client")
    httpx_types_module = _create_mock_module("httpx._types")

    class MockUseClientDefault:
        pass

    setattr(httpx_client_module, "USE_CLIENT_DEFAULT", MockUseClientDefault())
    setattr(httpx_types_module, "AuthTypes", str)

    setattr(httpx_module, "Response", MockResponse)
    setattr(httpx_module, "Client", MockClient)
    setattr(httpx_module, "AsyncClient", MockAsyncClient)
    setattr(httpx_module, "BaseTransport", MockBaseTransport)
    setattr(httpx_module, "_client", httpx_client_module)
    setattr(httpx_module, "_types", httpx_types_module)

# Mock tenacity
if "tenacity" not in sys.modules:
    tenacity_module = _create_mock_module("tenacity")

    def mock_retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def mock_stop_after_attempt(attempts):
        return attempts

    def mock_wait_exponential(multiplier, min=0.5, max=4, **kwargs):
        return None

    def mock_retry_if_exception_type(*args, **kwargs):
        return None

    def mock_retry_if_exception(*args, **kwargs):
        return None

    def mock_retry_if_not_exception_type(*args, **kwargs):
        return None

    def mock_retry_if_result(*args, **kwargs):
        return None

    def mock_retry_if_not_result(*args, **kwargs):
        return None

    def mock_retry_always(*args, **kwargs):
        return None

    def mock_retry_never(*args, **kwargs):
        return None

    def mock_retry_any(*args, **kwargs):
        return None

    def mock_retry_all(*args, **kwargs):
        return None

    def mock_retry_unless_exception_type(*args, **kwargs):
        return None

    def mock_retry_if_exception_message(*args, **kwargs):
        return None

    def mock_retry_if_not_exception_message(*args, **kwargs):
        return None

    def mock_retry_if_exception_cause_type(*args, **kwargs):
        return None

    def mock_stop_after_delay(*args, **kwargs):
        return None

    def mock_stop_never(*args, **kwargs):
        return None

    def mock_stop_all(*args, **kwargs):
        return None

    def mock_stop_any(*args, **kwargs):
        return None

    def mock_stop_before_delay(*args, **kwargs):
        return None

    def mock_stop_when_event_set(*args, **kwargs):
        return None

    def mock_wait_fixed(*args, **kwargs):
        return None

    def mock_wait_random(*args, **kwargs):
        return None

    def mock_wait_combine(*args, **kwargs):
        return None

    def mock_wait_chain(*args, **kwargs):
        return None

    def mock_wait_incrementing(*args, **kwargs):
        return None

    def mock_wait_exponential_jitter(*args, **kwargs):
        return None

    def mock_wait_full_jitter(*args, **kwargs):
        return None

    def mock_wait_random_exponential(*args, **kwargs):
        return None

    def mock_wait_none(*args, **kwargs):
        return None

    def mock_sleep(*args, **kwargs):
        return None

    def mock_sleep_using_event(*args, **kwargs):
        return None

    def mock_before_log(*args, **kwargs):
        return None

    def mock_after_log(*args, **kwargs):
        return None

    def mock_before_sleep_log(*args, **kwargs):
        return None

    def mock_before_nothing(*args, **kwargs):
        return None

    def mock_after_nothing(*args, **kwargs):
        return None

    def mock_before_sleep_nothing(*args, **kwargs):
        return None

    class MockRetrying:
        def __init__(self, *args, **kwargs):
            pass

    class MockAsyncRetrying:
        def __init__(self, *args, **kwargs):
            pass

    class MockBaseRetrying:
        def __init__(self, *args, **kwargs):
            pass

    class MockAttemptManager:
        def __init__(self, *args, **kwargs):
            pass

    class MockBaseAction:
        def __init__(self, *args, **kwargs):
            pass

    class MockDoAttempt:
        def __init__(self, *args, **kwargs):
            pass

    class MockDoSleep:
        def __init__(self, *args, **kwargs):
            pass

    class MockRetryAction:
        def __init__(self, *args, **kwargs):
            pass

    class MockRetryCallState:
        def __init__(self, *args, **kwargs):
            pass

    class MockRetryError(Exception):
        pass

    class MockTryAgain(Exception):
        pass

    class MockWrappedFn:
        def __init__(self, *args, **kwargs):
            pass

    class MockFuture:
        def __init__(self, *args, **kwargs):
            pass

    # Set all the mock functions and classes
    setattr(tenacity_module, "retry", mock_retry)
    setattr(tenacity_module, "stop_after_attempt", mock_stop_after_attempt)
    setattr(tenacity_module, "wait_exponential", mock_wait_exponential)
    setattr(tenacity_module, "Retrying", MockRetrying)
    setattr(tenacity_module, "AsyncRetrying", MockAsyncRetrying)
    setattr(tenacity_module, "BaseRetrying", MockBaseRetrying)
    setattr(tenacity_module, "AttemptManager", MockAttemptManager)
    setattr(tenacity_module, "BaseAction", MockBaseAction)
    setattr(tenacity_module, "DoAttempt", MockDoAttempt)
    setattr(tenacity_module, "DoSleep", MockDoSleep)
    setattr(tenacity_module, "RetryAction", MockRetryAction)
    setattr(tenacity_module, "RetryCallState", MockRetryCallState)
    setattr(tenacity_module, "RetryError", MockRetryError)
    setattr(tenacity_module, "TryAgain", MockTryAgain)
    setattr(tenacity_module, "WrappedFn", MockWrappedFn)
    setattr(tenacity_module, "Future", MockFuture)
    setattr(tenacity_module, "NO_RESULT", None)

    # Retry conditions
    setattr(tenacity_module, "retry_if_exception_type", mock_retry_if_exception_type)
    setattr(tenacity_module, "retry_if_exception", mock_retry_if_exception)
    setattr(tenacity_module, "retry_if_not_exception_type", mock_retry_if_not_exception_type)
    setattr(tenacity_module, "retry_if_result", mock_retry_if_result)
    setattr(tenacity_module, "retry_if_not_result", mock_retry_if_not_result)
    setattr(tenacity_module, "retry_always", mock_retry_always)
    setattr(tenacity_module, "retry_never", mock_retry_never)
    setattr(tenacity_module, "retry_any", mock_retry_any)
    setattr(tenacity_module, "retry_all", mock_retry_all)
    setattr(tenacity_module, "retry_unless_exception_type", mock_retry_unless_exception_type)
    setattr(tenacity_module, "retry_if_exception_message", mock_retry_if_exception_message)
    setattr(tenacity_module, "retry_if_not_exception_message", mock_retry_if_not_exception_message)
    setattr(tenacity_module, "retry_if_exception_cause_type", mock_retry_if_exception_cause_type)

    # Stop conditions
    setattr(tenacity_module, "stop_after_delay", mock_stop_after_delay)
    setattr(tenacity_module, "stop_never", mock_stop_never)
    setattr(tenacity_module, "stop_all", mock_stop_all)
    setattr(tenacity_module, "stop_any", mock_stop_any)
    setattr(tenacity_module, "stop_before_delay", mock_stop_before_delay)
    setattr(tenacity_module, "stop_when_event_set", mock_stop_when_event_set)

    # Wait strategies
    setattr(tenacity_module, "wait_fixed", mock_wait_fixed)
    setattr(tenacity_module, "wait_random", mock_wait_random)
    setattr(tenacity_module, "wait_combine", mock_wait_combine)
    setattr(tenacity_module, "wait_chain", mock_wait_chain)
    setattr(tenacity_module, "wait_incrementing", mock_wait_incrementing)
    setattr(tenacity_module, "wait_exponential_jitter", mock_wait_exponential_jitter)
    setattr(tenacity_module, "wait_full_jitter", mock_wait_full_jitter)
    setattr(tenacity_module, "wait_random_exponential", mock_wait_random_exponential)
    setattr(tenacity_module, "wait_none", mock_wait_none)

    # Sleep functions
    setattr(tenacity_module, "sleep", mock_sleep)
    setattr(tenacity_module, "sleep_using_event", mock_sleep_using_event)

    # Logging functions
    setattr(tenacity_module, "before_log", mock_before_log)
    setattr(tenacity_module, "after_log", mock_after_log)
    setattr(tenacity_module, "before_sleep_log", mock_before_sleep_log)
    setattr(tenacity_module, "before_nothing", mock_before_nothing)
    setattr(tenacity_module, "after_nothing", mock_after_nothing)
    setattr(tenacity_module, "before_sleep_nothing", mock_before_sleep_nothing)

# Mock prompt_toolkit
if "prompt_toolkit" not in sys.modules:
    prompt_toolkit_module = _create_mock_module("prompt_toolkit")

    class MockPromptSession:
        def __init__(self, **kwargs):
            pass

        def prompt(self, message: str) -> str:
            return "mock input"

    class MockStyle:
        @staticmethod
        def from_dict(style_dict):
            return MockStyle()

    # Create prompt_toolkit submodules
    prompt_toolkit_styles_module = _create_mock_module("prompt_toolkit.styles")
    setattr(prompt_toolkit_styles_module, "Style", MockStyle)

    setattr(prompt_toolkit_module, "PromptSession", MockPromptSession)
    setattr(prompt_toolkit_module, "Style", MockStyle)
    setattr(prompt_toolkit_module, "styles", prompt_toolkit_styles_module)

# Mock rich
if "rich" not in sys.modules:
    rich_module = _create_mock_module("rich")

    # Create all required rich submodules
    submodules = [
        "rich.console", "rich.markdown", "rich.text", "rich.panel",
        "rich.table", "rich.progress", "rich.status", "rich.live",
        "rich.layout", "rich.align", "rich.columns", "rich.group"
    ]

    for submodule_name in submodules:
        submodule = _create_mock_module(submodule_name)
        setattr(rich_module, submodule_name.split(".")[-1], submodule)

    # Mock specific classes that are commonly used
    class MockConsole:
        def __init__(self, **kwargs):
            pass

        def print(self, *args, **kwargs):
            print(*args)

    class MockMarkdown:
        def __init__(self, text: str):
            self.text = text

    setattr(rich_module, "Console", MockConsole)
    setattr(rich_module, "Markdown", MockMarkdown)

# Mock textual
if "textual" not in sys.modules:
    textual_module = _create_mock_module("textual")

    class MockApp:
        def __init__(self):
            pass

        def run(self):
            pass

    class MockScreen:
        def __init__(self):
            pass

    class MockWidget:
        def __init__(self):
            pass

    class MockContainer:
        def __init__(self):
            pass

    # Create all required textual submodules
    textual_submodules = [
        "textual.app", "textual.screen", "textual.widgets", "textual.containers",
        "textual.worker", "textual.events", "textual.message", "textual.reactive",
        "textual.binding", "textual.keys", "textual.color", "textual.geometry"
    ]

    for submodule_name in textual_submodules:
        submodule = _create_mock_module(submodule_name)
        setattr(textual_module, submodule_name.split(".")[-1], submodule)

    setattr(textual_module, "App", MockApp)
    setattr(textual_module, "Screen", MockScreen)
    setattr(textual_module, "Widget", MockWidget)
    setattr(textual_module, "Container", MockContainer)

# Mock psutil
if "psutil" not in sys.modules:
    psutil_module = _create_mock_module("psutil")

    class MockVirtualMemory:
        def __init__(self):
            self.percent = 50.0
            self.available = 1000000000
            self.total = 2000000000

    def mock_cpu_percent():
        return 25.0

    def mock_virtual_memory():
        return MockVirtualMemory()

    setattr(psutil_module, "cpu_percent", mock_cpu_percent)
    setattr(psutil_module, "virtual_memory", mock_virtual_memory)

# Mock yaml
if "yaml" not in sys.modules:
    yaml_module = _create_mock_module("yaml")

    def mock_safe_load(text: str):
        return {}

    def mock_safe_dump(data: Dict[str, Any]):
        return "mock yaml"

    setattr(yaml_module, "safe_load", mock_safe_load)
    setattr(yaml_module, "safe_dump", mock_safe_dump)

# Mock pathlib
if "pathlib" not in sys.modules:
    pathlib_module = _create_mock_module("pathlib")

    class MockPath:
        def __init__(self, path: str):
            self._path = path

        def exists(self):
            return True

        def is_file(self):
            return True

        def is_dir(self):
            return True

        def rglob(self, pattern: str):
            return [MockPath("mock_file.txt")]

        def stat(self):
            class MockStat:
                st_size = 1000
            return MockStat()

    setattr(pathlib_module, "Path", MockPath)


# ---------------------------------------------------------------------------
# Mock Classes for Testing
# ---------------------------------------------------------------------------

class MockCompiledGraph:
    """Mock compiled graph for testing."""
    def __init__(self, nodes, edges, name):
        self.nodes = nodes
        self.edges = edges
        self.name = name

    def invoke(self, input_data):
        """Mock invoke method."""
        return {"result": "mocked_result"}

    def ainvoke(self, input_data):
        """Mock async invoke method."""
        import asyncio
        return asyncio.create_task(self._async_invoke(input_data))

    async def _async_invoke(self, input_data):
        """Mock async invoke implementation."""
        return {"result": "mocked_async_result"}

# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_chromadb():
    """Provide a mock ChromaDB client for testing."""
    with patch("src.tools.chromadb_agent.ChromaDBAgent") as mock:
        mock_instance = MagicMock()
        mock_instance.similarity_search.return_value = [
            "Mock document 1",
            "Mock document 2",
            "Mock document 3"
        ]
        mock_instance.get_collections.return_value = ["default"]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_neo4j():
    """Provide a mock Neo4j client for testing."""
    with patch("src.tools.neo4j_agent.Neo4jAgent") as mock:
        mock_instance = MagicMock()
        mock_instance.query.return_value = [{"name": "Test Entity", "label": "PERSON"}]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ollama():
    """Provide a mock Ollama client for testing."""
    with patch("src.orchestration.nodes._get_ollama_client") as mock:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = {
            "response": '{"plan": ["vector_search"]}',
            "model": "llama3",
            "done": True
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llamaindex():
    """Provide mock LlamaIndex components for testing."""
    with patch("src.tools.chromadb_agent.OllamaEmbedding") as mock_embedding:
        mock_instance = MagicMock()
        mock_instance.get_text_embedding.return_value = [0.1] * 384
        mock_embedding.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_documents():
    """Provide sample documents for testing."""
    return [
        {
            "text": "This is a sample document about machine learning.",
            "metadata": {"source": "test", "filename": "ml_doc.txt"}
        },
        {
            "text": "Another document about artificial intelligence.",
            "metadata": {"source": "test", "filename": "ai_doc.txt"}
        }
    ]


@pytest.fixture
def sample_query():
    """Provide a sample query for testing."""
    return "What is machine learning?"


@pytest.fixture
def sample_agent_state(sample_query):
    """Provide a sample AgentState for testing."""
    from src.orchestration.state import AgentState
    return AgentState(query=sample_query)


@pytest.fixture
def mock_ui_callback():
    """Provide a mock UI callback function for testing."""
    def callback(message: str) -> None:
        print(f"UI Callback: {message}")
    return callback


@pytest.fixture
def mock_settings():
    """Provide mock settings for testing."""
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.ollama_host = "http://localhost:11434"
    settings.ollama_embedding_model = "nomic-embed-text"
    settings.neo4j_uri = "bolt://localhost:7687"
    settings.neo4j_user = "neo4j"
    settings.neo4j_password = "test_password"
    settings.chroma_host = "localhost"
    settings.chroma_port = 8000
    return settings


@pytest.fixture
def mock_chromadb_agent():
    """Provide a mock ChromaDB agent for testing."""
    from unittest.mock import MagicMock, AsyncMock

    agent = MagicMock()
    agent.similarity_search.return_value = ["Mock document 1", "Mock document 2"]

    # Create async mock for async methods using AsyncMock
    agent.similarity_search_async = AsyncMock(return_value=["Mock async document 1", "Mock async document 2"])
    agent.get_collections.return_value = ["default"]
    return agent


@pytest.fixture
def mock_neo4j_agent():
    """Provide a mock Neo4j agent for testing."""
    from unittest.mock import MagicMock, AsyncMock

    agent = MagicMock()
    agent.query.return_value = [{"name": "Test Node", "label": "PERSON"}]
    agent.execute_query.return_value = [{"result": "test"}]
    agent.verify_connectivity.return_value = True

    # Create async mock for async methods using AsyncMock
    agent.query_async = AsyncMock(return_value=[{"name": "Test Async Node", "label": "PERSON"}])
    agent.execute_query_async = AsyncMock(return_value=[{"result": "async_test"}])
    return agent


@pytest.fixture
def mock_health_check():
    """Provide a mock health check response."""
    return {
        "status": "alive",
        "service": "agent-stack",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_metrics():
    """Provide mock metrics for testing."""
    return {
        "vector_search_calls": 10,
        "graph_search_calls": 5,
        "planner_calls": 15,
        "synthesizer_calls": 15
    }


# ---------------------------------------------------------------------------
# Async Test Support
# ---------------------------------------------------------------------------

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def async_mock_chromadb():
    """Provide an async mock ChromaDB client for testing."""
    with patch("src.tools.chromadb_agent.ChromaDBAgent") as mock:
        mock_instance = AsyncMock()
        mock_instance.similarity_search_async.return_value = [
            "Mock async document 1",
            "Mock async document 2"
        ]
        mock_instance.get_collections.return_value = ["default"]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
async def async_mock_neo4j():
    """Provide an async mock Neo4j client for testing."""
    with patch("src.tools.neo4j_agent.Neo4jAgent") as mock:
        mock_instance = AsyncMock()
        mock_instance.query_async.return_value = [{"name": "Async Entity", "label": "PERSON"}]
        mock.return_value = mock_instance
        yield mock_instance


# ---------------------------------------------------------------------------
# Integration Test Support
# ---------------------------------------------------------------------------

@pytest.fixture
def integration_test_config():
    """Provide configuration for integration tests."""
    return {
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "test_password",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama3",
        "ollama_embedding_model": "nomic-embed-text",
        "log_level": "DEBUG"
    }


@pytest.fixture
def mock_file_system():
    """Provide a mock file system for testing."""
    with patch("pathlib.Path") as mock_path:
        mock_instance = MagicMock()
        mock_instance.exists.return_value = True
        mock_instance.is_file.return_value = True
        mock_instance.is_dir.return_value = True
        mock_instance.rglob.return_value = [
            MagicMock(name="test1.txt"),
            MagicMock(name="test2.txt")
        ]
        mock_path.return_value = mock_instance
        yield mock_instance


# ---------------------------------------------------------------------------
# Performance Test Support
# ---------------------------------------------------------------------------

@pytest.fixture
def performance_timer():
    """Provide a timer for performance testing."""
    import time
    start_time = time.time()
    yield lambda: time.time() - start_time


@pytest.fixture
def memory_profiler():
    """Provide a simple memory profiler for testing."""
    import psutil
    process = psutil.Process()
    start_memory = process.memory_info().rss
    yield lambda: process.memory_info().rss - start_memory


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Configure pytest with test-specific settings."""
    # Set test mode
    os.environ["TESTING"] = "true"

    # Disable file logging during tests
    import logging
    logging.getLogger().handlers.clear()


@pytest.fixture
def mock_ollama_client():
    """Provide a mock Ollama client for testing."""
    from unittest.mock import MagicMock
    client = MagicMock()
    client.generate.return_value = {"response": '{"plan": ["vector_search", "graph_search"]}'}
    return client


@pytest.fixture
def sample_agent_state_with_plan():
    """Provide a sample agent state with a plan for testing."""
    from src.orchestration.state import AgentState

    def mock_ui_callback(msg: str) -> None:
        pass

    return AgentState(
        query="What is artificial intelligence?",
        plan=["vector_search", "graph_search"],
        ui=mock_ui_callback
    )


@pytest.fixture
def sample_agent_state_with_outputs():
    """Provide a sample agent state with tool outputs for testing."""
    from src.orchestration.state import AgentState

    def mock_ui_callback(msg: str) -> None:
        pass

    return AgentState(
        query="What is artificial intelligence?",
        plan=["vector_search", "graph_search"],
        tool_output=["AI is a field of computer science...", "Machine learning is a subset of AI..."],
        ui=mock_ui_callback
    )


def pytest_unconfigure(config):
    """Clean up after tests."""
    # Restore environment
    if "TESTING" in os.environ:
        del os.environ["TESTING"]