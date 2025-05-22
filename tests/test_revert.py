import os
import pytest
import tempfile
import shutil
from pathlib import Path

from cerebras_agent.agent import CerebrasAgent
from cerebras_agent.file_ops import FileOperations

@pytest.fixture
def api_key():
    """Get the real Cerebras API key from environment variables."""
    key = os.environ.get("CEREBRAS_API_KEY")
    if not key:
        pytest.skip("CEREBRAS_API_KEY environment variable not set")
    return key

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def agent(api_key, temp_project_dir):
    """Create an agent with the real API key and temp directory."""
    agent = CerebrasAgent(api_key=api_key, repo_path=temp_project_dir)
    agent.file_ops = FileOperations(temp_project_dir)
    return agent

def test_revert_functionality(agent, temp_project_dir):
    """Test the revert functionality of the agent."""
    # This is a placeholder test that should be expanded with actual revert functionality tests
    assert True, "Placeholder for revert functionality tests" 