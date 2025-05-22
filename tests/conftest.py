import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from cerebras_agent.agent import CerebrasAgent

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for unit tests."""
    with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test_api_key"}):
        yield

@pytest.fixture
def mock_file():
    """Return a mock file path."""
    return "test.py"

@pytest.fixture
def mock_code():
    """Return mock code content."""
    return "print('Hello, World!')"

@pytest.fixture
def mock_suggested_code():
    """Return mock suggested code content."""
    return "print('Hello, Cerebras!')"

@pytest.fixture
def mock_agent(mock_env_vars):
    """Create a mock agent instance."""
    return CerebrasAgent()

@pytest.fixture
def real_agent():
    """Create a real agent instance for integration tests."""
    if not os.getenv("CEREBRAS_API_KEY"):
        pytest.skip("CEREBRAS_API_KEY environment variable not set")
    return CerebrasAgent()

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.py"
    file_path.write_text("print('Hello, World!')")
    return file_path 