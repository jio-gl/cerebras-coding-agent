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

def test_plan_with_backtick_files(agent, temp_project_dir):
    """Test a realistic markdown plan with backticks in filenames."""
    # Create a more realistic markdown response from an LLM
    markdown_response = """
    # ZK-Poker Implementation

    Based on your requirements, I'll implement a Zero-Knowledge Poker game using JavaScript for the frontend and smart contracts for the backend. Here's the implementation plan:

    ## Frontend Components

    First, let's create the main components for our poker game:

    ### `Game.js`
    ```javascript
    // The main Game component for ZK-Poker
    import React, { useState, useEffect } from 'react';
    import { ethers } from 'ethers';
    import { generateProof, verifyProof } from './zk-utils';
    import PokerContract from './SmartContract';

    const Game = () => {
      const [gameState, setGameState] = useState({
        players: [],
        cards: [],
        pot: 0,
        currentPlayer: null,
        winner: null
      });
      
      const [wallet, setWallet] = useState(null);
      
      useEffect(() => {
        // Connect to wallet and contract on component mount
        const connectWallet = async () => {
          if (window.ethereum) {
            try {
              await window.ethereum.request({ method: 'eth_requestAccounts' });
              const provider = new ethers.providers.Web3Provider(window.ethereum);
              const signer = provider.getSigner();
              setWallet(signer);
            } catch (error) {
              console.error("Failed to connect wallet:", error);
            }
          }
        };
        
        connectWallet();
      }, []);
      
      const dealCards = () => {
        // Deal encrypted cards to players
        // In a real implementation, this would use ZK proofs
        console.log("Dealing cards...");
      };
      
      const placeBet = (amount) => {
        // Place a bet with ZK proof that player has enough funds
        console.log(`Placing bet: ${amount}`);
      };
      
      const foldHand = () => {
        // Fold current hand
        console.log("Folding hand...");
      };
      
      return (
        <div className="game-container">
          <h1>ZK-Poker</h1>
          <div className="game-table">
            <div className="players">
              {gameState.players.map(player => (
                <div key={player.id} className="player">
                  <div className="player-info">
                    <span>{player.name}</span>
                    <span>{player.chips} chips</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="controls">
              <button onClick={dealCards}>Deal</button>
              <button onClick={() => placeBet(10)}>Bet 10</button>
              <button onClick={() => placeBet(20)}>Bet 20</button>
              <button onClick={foldHand}>Fold</button>
            </div>
          </div>
        </div>
      );
    };

    export default Game;
    ```

    ### `index.js`
    ```javascript
    import React from 'react';
    import ReactDOM from 'react-dom';
    import Game from './Game';
    import './styles.css';

    ReactDOM.render(
      <React.StrictMode>
        <Game />
      </React.StrictMode>,
      document.getElementById('root')
    );
    ```

    ## Smart Contract Implementation
    
    Now let's create the Solidity smart contract for our game:

    ### `SmartContract.sol`
    ```solidity
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;

    contract ZKPoker {
        struct Player {
            address addr;
            uint256 chips;
            bool active;
        }
        
        struct Game {
            uint256 id;
            Player[] players;
            uint256 pot;
            uint256 startTime;
            bool active;
            address winner;
        }
        
        mapping(uint256 => Game) public games;
        uint256 public gameCount;
        
        event GameCreated(uint256 gameId, address creator);
        event PlayerJoined(uint256 gameId, address player);
        event BetPlaced(uint256 gameId, address player, uint256 amount);
        event GameEnded(uint256 gameId, address winner, uint256 amount);
        
        // Create a new game
        function createGame() public returns (uint256) {
            uint256 gameId = gameCount++;
            games[gameId].id = gameId;
            games[gameId].active = true;
            games[gameId].startTime = block.timestamp;
            
            Player memory creator = Player({
                addr: msg.sender,
                chips: 1000,
                active: true
            });
            
            games[gameId].players.push(creator);
            
            emit GameCreated(gameId, msg.sender);
            
            return gameId;
        }
        
        // Join an existing game
        function joinGame(uint256 gameId) public {
            require(games[gameId].active, "Game is not active");
            
            Player memory newPlayer = Player({
                addr: msg.sender,
                chips: 1000,
                active: true
            });
            
            games[gameId].players.push(newPlayer);
            
            emit PlayerJoined(gameId, msg.sender);
        }
        
        // Place a bet with a zero-knowledge proof
        function placeBet(uint256 gameId, uint256 amount, bytes memory proof) public {
            require(games[gameId].active, "Game is not active");
            
            // In a real implementation, we would verify the ZK proof here
            // verifyProof(proof);
            
            // For this simplified version, we just update the pot
            games[gameId].pot += amount;
            
            emit BetPlaced(gameId, msg.sender, amount);
        }
        
        // End the game and determine the winner
        function endGame(uint256 gameId, address winner, bytes memory proof) public {
            require(games[gameId].active, "Game is not active");
            
            // In a real implementation, we would verify the winner with a ZK proof
            // verifyWinnerProof(proof);
            
            games[gameId].active = false;
            games[gameId].winner = winner;
            
            emit GameEnded(gameId, winner, games[gameId].pot);
        }
    }
    ```

    This implementation provides a basic structure for a Zero-Knowledge Poker game. The smart contract handles game creation, player management, and betting, while the frontend components render the game interface. In a production environment, you would need to implement the actual zero-knowledge proof generation and verification.
    """
    
    # Execute the plan to create files
    created_files = agent.execute_plan(markdown_response)
    print(f"Created files: {created_files}")
    
    # Check for expected files (without backticks)
    expected_files = ['Game.js', 'index.js', 'SmartContract.sol']
    for expected_file in expected_files:
        # Check if file exists on disk without backticks
        file_path = os.path.join(temp_project_dir, expected_file)
        assert os.path.exists(file_path), f"File doesn't exist on disk: {file_path}"
        
        with open(file_path, 'r') as f:
            content = f.read()
            # Verify that the correct content is in each file
            if expected_file == 'Game.js':
                assert "const Game = () =>" in content
            elif expected_file == 'index.js':
                assert "import Game from './Game'" in content
            elif expected_file == 'SmartContract.sol': 
                assert "contract ZKPoker" in content
    
    # Verify that no files with backticks in the name were created
    all_files = os.listdir(temp_project_dir)
    for file in all_files:
        assert '`' not in file, f"File with backticks found: {file}" 