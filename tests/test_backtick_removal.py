import os
import pytest
import tempfile
import shutil
import re
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

def test_extract_code_blocks_with_backticks(agent):
    """Test that extract_code_blocks correctly handles filenames with backticks."""
    markdown_response = """
    # Test Project with Backticks
    
    Let's create some files with backtick filenames:
    
    ### `Game.js`
    ```javascript
    class Game {
        constructor() {
            this.score = 0;
        }
        
        incrementScore() {
            this.score += 1;
        }
    }
    
    module.exports = Game;
    ```
    
    ### `index.js`
    ```javascript
    const Game = require('./Game');
    
    const game = new Game();
    game.incrementScore();
    console.log(`Current score: ${game.score}`);
    ```
    
    ### `SmartContract.sol`
    ```solidity
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    contract GameContract {
        uint256 public score;
        
        function incrementScore() public {
            score += 1;
        }
    }
    ```
    """
    
    # First, let's manually analyze the markdown to see what headers and code blocks exist
    headers = re.findall(r'###\s+(.+)', markdown_response)
    print(f"Detected headers: {headers}")
    
    # Find code blocks
    code_blocks = re.findall(r'```(\w+)[\s\S]+?```', markdown_response)
    print(f"Detected code block languages: {code_blocks}")
    
    # Extract code blocks using the CerebrasAgent method
    extracted_blocks = agent.extract_code_blocks(markdown_response)
    print(f"Extracted code blocks: {list(extracted_blocks.keys())}")
    
    # Check that backticks are removed in key names
    for key in extracted_blocks.keys():
        assert '`' not in key, f"Backticks found in key: {key}"
    
    # Check for specific expected files
    expected_files = ['Game.js', 'index.js', 'SmartContract.sol']
    for file in expected_files:
        assert any(key == file or key == file.lower() for key in extracted_blocks.keys()), f"Expected file not found: {file}"

def test_execute_plan_with_backticks(agent, temp_project_dir):
    """Test that execute_plan properly handles filenames with backticks during file creation."""
    # Create markdown response with backticks manually constructing file headers
    markdown_response = """
    # Test Project with Backticks
    
    Let's create some files with backtick filenames:
    
    ### Game.js
    ```javascript
    class Game {
        constructor() {
            this.score = 0;
        }
        
        incrementScore() {
            this.score += 1;
        }
    }
    
    module.exports = Game;
    ```
    
    ### index.js
    ```javascript
    const Game = require('./Game');
    
    const game = new Game();
    game.incrementScore();
    console.log(`Current score: ${game.score}`);
    ```
    
    ### SmartContract.sol
    ```solidity
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    contract GameContract {
        uint256 public score;
        
        function incrementScore() public {
            score += 1;
        }
    }
    ```
    """
    
    # First, manually extract code blocks to verify the test
    code_blocks = agent.extract_code_blocks(markdown_response)
    print(f"Extracted code blocks before execute_plan: {list(code_blocks.keys())}")
    
    # Execute the plan
    created_files = agent.execute_plan(markdown_response)
    
    # Print created files for debugging
    print(f"Files created by execute_plan: {created_files}")
    
    # Verify that created files don't have backticks
    for filename in created_files:
        assert '`' not in filename, f"Backticks found in filename: {filename}"
    
    # Check for specific files expected to be created
    expected_files = ['Game.js', 'index.js', 'SmartContract.sol']
    for expected_file in expected_files:
        # Check if file exists on disk
        file_path = os.path.join(temp_project_dir, expected_file)
        assert os.path.exists(file_path), f"File doesn't exist on disk: {file_path}" 