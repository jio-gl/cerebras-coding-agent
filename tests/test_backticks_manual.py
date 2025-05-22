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

def test_backtick_removal_in_filenames(agent, temp_project_dir):
    """Test that backticks are properly removed from filenames when executing a plan."""
    # Test markdown with backticks in filenames
    markdown = '''
    # Test Project with Backticks
    
    Let's create some example files:
    
    ### `app.js`
    ```javascript
    console.log('Hello from app.js');
    ```
    
    ### `index.html`
    ```html
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Page</h1>
        <script src='app.js'></script>
    </body>
    </html>
    ```
    '''
    
    # Execute the plan
    created_files = agent.execute_plan(markdown)
    print(f'Created files: {created_files}')
    
    # Verify files were created properly
    for filename in created_files:
        # Check that no backticks in filenames
        assert '`' not in filename, f"Backticks found in filename: {filename}"
        
        # Check that file exists on disk
        file_path = os.path.join(temp_project_dir, filename)
        assert os.path.exists(file_path), f"File doesn't exist on disk: {file_path}"
    
    # Check specific expected files
    assert 'app.js' in created_files, "app.js not found in created files"
    assert 'index.html' in created_files, "index.html not found in created files"
    
    # Verify file contents
    app_js_path = os.path.join(temp_project_dir, 'app.js')
    with open(app_js_path, 'r') as f:
        content = f.read()
        assert "Hello from app.js" in content
    
    html_path = os.path.join(temp_project_dir, 'index.html')
    with open(html_path, 'r') as f:
        content = f.read()
        assert "<title>Test Page</title>" in content 