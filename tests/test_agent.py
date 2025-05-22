import os
import pytest
import requests
from unittest.mock import patch, MagicMock, mock_open, Mock
from cerebras_agent.agent import CerebrasAgent
import json
import importlib

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)

@pytest.fixture
def mock_file():
    """Return a mock file path."""
    return "test_file.py"

@pytest.fixture
def mock_code():
    """Return mock code content."""
    return "def test_function():\n    pass"

@pytest.fixture
def mock_suggested_code():
    """Return mock suggested code content."""
    return "def test_function():\n    return True"

@pytest.fixture
def mock_agent():
    """Create a mock agent instance."""
    with patch('cerebras_agent.agent.Cerebras') as mock_cerebras:
        # Mock the API response for unit tests
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "steps": [
                    {
                        "tool": "file_ops",
                        "action": "read",
                        "target": "test_file.py",
                        "description": "Read the test file"
                    }
                ],
                "expected_outcome": "Read file contents"
            })))
        ]
        mock_cerebras.return_value.chat.completions.create.return_value = mock_response
        return CerebrasAgent(api_key="test-api-key")

@pytest.fixture
def mock_file_ops():
    """Create a mock file operations instance."""
    with patch('cerebras_agent.file_ops.FileOperations') as mock:
        mock.return_value.get_repository_structure.return_value = {
            "test_file.py": "file",
            "test_dir": "directory"
        }
        mock.return_value.find_files.return_value = ["test_file.py"]
        mock.return_value.is_ignored.return_value = False
        mock.return_value.grep_files.return_value = [("test_file.py", 1, "test line")]
        yield mock

@pytest.fixture
def agent():
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        pytest.skip("CEREBRAS_API_KEY environment variable not set")
    return CerebrasAgent(api_key=api_key)

@pytest.fixture
def real_agent():
    """Create a real agent instance for integration tests."""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        pytest.skip("CEREBRAS_API_KEY environment variable not set")
    return CerebrasAgent(api_key=api_key)

def test_agent_initialization_with_direct_api_key():
    """Test agent initialization with a directly provided API key."""
    with patch('cerebras_agent.agent.Cerebras') as mock_cerebras:
        agent = CerebrasAgent(api_key="direct-key")
        assert agent.api_key == "direct-key"

def test_agent_initialization_with_env_var():
    """Test agent initialization with API key from environment."""
    with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-api-key"}):
        with patch('cerebras_agent.agent.Cerebras') as mock_cerebras:
            agent = CerebrasAgent()
            assert agent.api_key == "test-api-key"

def test_agent_initialization_with_repo_path(mock_file_ops):
    """Test agent initialization with repository path."""
    with patch('cerebras_agent.agent.Cerebras') as mock_cerebras:
        agent = CerebrasAgent(api_key="test-key", repo_path="test_repo")
        assert agent.file_ops is not None

def test_agent_initialization_without_api_key():
    """Test agent initialization without API key."""
    with patch('dotenv.load_dotenv', lambda *args, **kwargs: None):
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.getenv', return_value=None):
                with pytest.raises(ValueError):
                    CerebrasAgent()

def test_ask_question(mock_agent):
    """Test asking a question."""
    answer = mock_agent.ask_question("What is the meaning of life?")
    # Parse JSON if possible
    try:
        answer = json.loads(answer)["answer"]
    except Exception:
        pass
    assert answer == "Test answer"

def test_ask_question_with_context(mock_file_ops):
    """Test asking a question with context."""
    with patch('cerebras_agent.agent.Cerebras') as mock_cerebras:
        mock_cerebras.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content='{"answer": "Test answer"}'))
        ]
        agent = CerebrasAgent(api_key="test-key", repo_path="test_repo")
        answer = agent.ask_question("What is the meaning of life?", {"context": "test"})
        try:
            answer = json.loads(answer)["answer"]
        except Exception:
            pass
        assert answer == "Test answer"

def test_suggest_code_changes(mock_agent, mock_file, mock_code, mock_suggested_code):
    """Test suggesting code changes."""
    with patch('builtins.open', mock_open(read_data=mock_code)):
        # Patch the agent's client to return the correct mock response
        mock_agent.client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "steps": [
                    {
                        "tool": "file_ops",
                        "action": "write",
                        "target": mock_file,
                        "content": mock_suggested_code
                    }
                ]
            })))
        ]
        changes = mock_agent.suggest_code_changes(mock_file, "Add return statement")
        assert isinstance(changes, dict)
        assert "steps" in changes
        assert len(changes["steps"]) == 1
        assert changes["steps"][0]["tool"] == "file_ops"
        assert changes["steps"][0]["action"] == "write"
        assert changes["steps"][0]["target"] == mock_file
        assert changes["steps"][0]["content"] == mock_suggested_code

def test_accept_changes(mock_agent, mock_file, mock_code, mock_suggested_code):
    """Test accepting changes."""
    file_path = "test_file.py"
    mock_agent._change_history = [(file_path, mock_code, mock_suggested_code)]
    
    with patch('builtins.open', mock_open()) as m_open:
        result = mock_agent.accept_changes(file_path)
        assert result is True
        m_open().write.assert_called_once_with(mock_suggested_code)

def test_reject_changes(mock_agent, mock_file, mock_code, mock_suggested_code):
    """Test rejecting changes."""
    file_path = "test_file.py"
    mock_agent._change_history = [(file_path, mock_code, mock_suggested_code)]
    
    with patch('builtins.open', mock_open()) as m_open:
        result = mock_agent.reject_changes(file_path)
        assert result is True
        m_open().write.assert_called_once_with(mock_code)

def test_revert_to_checkpoint(mock_agent, mock_file, mock_code, mock_suggested_code):
    """Test reverting to a checkpoint."""
    mock_agent._change_history = [
        (mock_file, mock_code, mock_suggested_code),
        (mock_file, mock_suggested_code, "new code")
    ]
    
    with patch('builtins.open', mock_open()) as m_open:
        result = mock_agent.revert_to_checkpoint(0)
        assert result is True
        # Only one write per file is expected
        assert m_open().write.call_count == 1

def test_analyze_repository(mock_agent, mock_file_ops):
    """Test repository analysis."""
    agent = CerebrasAgent(api_key="test-key", repo_path="test_repo")
    analysis = agent.analyze_repository("test_repo")
    assert "structure" in analysis
    assert "file_stats" in analysis
    assert analysis["file_stats"]["total_files"] >= 0
    assert "ignored_files" in analysis["file_stats"]

def test_search_files(mock_agent, mock_file_ops):
    """Test searching for files."""
    with patch('cerebras_agent.agent.FileOperations') as MockFileOps:
        instance = MockFileOps.return_value
        instance.find_files.return_value = ["test_file.py"]
        agent = CerebrasAgent(api_key="test-key", repo_path="test_repo")
        files = agent.search_files("test")
        assert files == ["test_file.py"]

def test_grep_files(mock_agent, mock_file_ops):
    """Test grepping files."""
    with patch('cerebras_agent.agent.FileOperations') as MockFileOps:
        instance = MockFileOps.return_value
        instance.grep_files.return_value = [("test_file.py", 1, "test line")]
        agent = CerebrasAgent(api_key="test-key", repo_path="test_repo")
        results = agent.grep_files("test")
        assert results == [("test_file.py", 1, "test line")]

def test_search_files_without_repo(mock_agent):
    """Test searching files without repository path."""
    files = mock_agent.search_files("test")
    assert files == []

def test_grep_files_without_repo(mock_agent):
    """Test grepping files without repository path."""
    results = mock_agent.grep_files("test")
    assert results == []

def test_suggest_code_changes_with_ignored_file(mock_agent, mock_file, mock_code, mock_suggested_code, mock_file_ops):
    """Test suggesting changes for an ignored file."""
    mock_file_ops.return_value.is_ignored.return_value = True
    
    with patch('builtins.open', mock_open(read_data=mock_code)):
        with patch('cerebras_agent.agent.Cerebras') as mock_cerebras:
            mock_cerebras.return_value.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps({
                    "steps": [
                        {
                            "tool": "file_ops",
                            "action": "write",
                            "target": mock_file,
                            "content": mock_suggested_code
                        }
                    ]
                })))
            ]
            agent = CerebrasAgent(api_key="test-key", repo_path="test_repo")
            changes = agent.suggest_code_changes(mock_file, "Add return statement")
            assert isinstance(changes, dict)
            assert "steps" in changes
            assert len(changes["steps"]) == 1
            assert changes["steps"][0]["tool"] == "file_ops"
            assert changes["steps"][0]["action"] == "write"
            assert changes["steps"][0]["target"] == mock_file
            assert changes["steps"][0]["content"] == mock_suggested_code

def test_create_plan(agent):
    """Test that plan creation returns a valid plan structure."""
    task = "Create a simple counter contract"
    context = {
        "structure": {},
        "file_count": 0,
        "python_files": 0,
        "ignored_files": 0
    }
    
    plan = agent._create_plan(task, context)
    assert isinstance(plan, dict)
    assert "steps" in plan
    assert isinstance(plan["steps"], list)

def test_execute_plan_step(agent):
    """Test that plan steps can be executed."""
    step = {
        "tool": "chat",
        "action": "generate",
        "target": "Create a simple counter contract in Solidity"
    }
    
    result = agent._execute_plan_step(step)
    assert isinstance(result, str)
    assert len(result) > 0

def test_prompt_complex_change(agent):
    """Test that complex changes can be suggested."""
    prompt = "Create a simple counter contract"
    result = agent.prompt_complex_change(prompt)
    assert isinstance(result, dict)
    assert "steps" in result
    assert isinstance(result["steps"], list)

@patch('cerebras_agent.agent.Cerebras')
def test_plan_creation_with_mock(mock_cerebras):
    """Test plan creation with mocked API response."""
    # Mock the API response
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='''{
            "steps": [
                {
                    "tool": "file_ops",
                    "action": "write",
                    "target": "contracts/Counter.sol",
                    "content": "// Counter contract"
                }
            ]
        }'''))
    ]
    mock_cerebras.return_value.chat.completions.create.return_value = mock_response
    
    agent = CerebrasAgent(api_key="test_key")
    plan = agent._create_plan("test task", {})
    
    assert isinstance(plan, dict)
    assert "steps" in plan
    assert len(plan["steps"]) > 0
    assert plan["steps"][0]["tool"] == "file_ops"

def test_ask_question_integration(real_agent):
    """Test asking a question using the real API."""
    answer = real_agent.ask_question("What is the purpose of this test file?")
    assert answer is not None
    assert isinstance(answer, str)
    assert len(answer) > 0

def test_ask_question_with_context_integration(real_agent):
    """Test asking a question with context using the real API."""
    context = {
        "file_content": "def hello(): print('Hello, World!')",
        "file_type": "python"
    }
    answer = real_agent.ask_question("How can I improve this function?", context)
    assert answer is not None
    assert isinstance(answer, str)
    assert len(answer) > 0

def test_suggest_code_changes_integration(real_agent, mock_file, mock_code):
    """Test suggesting code changes using the real API."""
    with patch('builtins.open', mock_open(read_data=mock_code)):
        changes = real_agent.suggest_code_changes(mock_file, "Add a docstring to the function")
        assert isinstance(changes, dict)
        assert "steps" in changes
        assert len(changes["steps"]) > 0
        assert any(step["tool"] == "file_ops" for step in changes["steps"])

def test_create_plan_integration(real_agent):
    """Test plan creation using the real API."""
    task = "Create a simple counter contract"
    context = {
        "structure": {},
        "file_count": 0,
        "python_files": 0,
        "ignored_files": 0
    }
    
    plan = real_agent._create_plan(task, context)
    assert isinstance(plan, dict)
    assert "steps" in plan
    assert isinstance(plan["steps"], list)
    assert len(plan["steps"]) > 0 