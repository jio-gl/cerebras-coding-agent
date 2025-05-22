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
    temp_path = tempfile.mkdtemp(prefix="test-project-")
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def agent(api_key, temp_project_dir):
    """Create an agent with the real API key and temp directory."""
    agent = CerebrasAgent(api_key=api_key, repo_path=temp_project_dir)
    agent.file_ops = FileOperations(temp_project_dir)
    return agent

def test_prevent_nested_project_folders(agent, temp_project_dir):
    """Test that the agent prevents creating nested project folders."""
    # Get the project folder name
    project_name = os.path.basename(temp_project_dir)
    
    # Create a markdown response with paths that include the project name
    markdown_response = f"""
    # {project_name} Implementation
    
    Let's create the core components for our project:
    
    ### `{project_name}/components/App.js`
    ```javascript
    import React from 'react';
    
    function App() {{
      return (
        <div>
          <h1>Welcome to {project_name}</h1>
        </div>
      );
    }}
    
    export default App;
    ```
    
    ### `{project_name}/index.js`
    ```javascript
    import React from 'react';
    import ReactDOM from 'react-dom';
    import App from './components/App';
    
    ReactDOM.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
      document.getElementById('root')
    );
    ```
    
    ### `src/{project_name}/utils/helpers.js`
    ```javascript
    export function formatDate(date) {{
      return new Date(date).toLocaleDateString();
    }}
    
    export function generateId() {{
      return Math.random().toString(36).substring(2, 9);
    }}
    ```
    """
    
    # Execute the plan
    created_files = agent.execute_plan(markdown_response)
    print(f"Created files: {created_files}")
    
    # Verify no nested project folders were created
    for filepath in created_files:
        # The path should not start with project_name/
        assert not filepath.startswith(f"{project_name}/"), f"Path should not start with {project_name}/: {filepath}"
        
        # The path should not contain project_name twice
        assert filepath.count(project_name) <= 1, f"Path should not contain project name multiple times: {filepath}"
        
        # Check src/ paths don't have nested project folders
        if filepath.startswith("src/"):
            parts = filepath.split("/")
            if len(parts) >= 2:
                assert parts[1] != project_name, f"Path should not have nested project folder in src: {filepath}"
    
    # Verify the files exist with correct paths
    expected_files = ["components/App.js", "index.js", "src/utils/helpers.js"]
    for expected_file in expected_files:
        file_path = os.path.join(temp_project_dir, expected_file)
        assert os.path.exists(file_path), f"Expected file doesn't exist: {file_path}"
    
    # Verify the problematic nested folder doesn't exist
    nested_project_dir = os.path.join(temp_project_dir, project_name)
    assert not os.path.exists(nested_project_dir), f"Nested project folder should not exist: {nested_project_dir}" 