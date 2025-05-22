# Cerebras Coding Agent

```
 ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
██║     ██║   ██║██║  ██║█████╗  ██████╔╝
██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗
╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                         
 Cerebras Agent - Your AI coding assistant
```

A local agent for code development using the Cerebras API. This tool allows you to interact with your codebase through natural language, helping you understand, modify, and extend your code more efficiently.

## Features

- Code generation and modification based on natural language instructions
- Repository analysis and question answering
- Interactive command-line interface
- Automatic error detection and fixing
- Support for multiple programming languages and frameworks
- Proper handling of project file structures

## Installation

### From PyPI (Recommended)

```bash
pip install cerebras-agent
```

### From Source

```bash
# Clone the repository
git clone https://github.com/jio-gl/cerebras-coding-agent.git
cd cerebras-coding-agent

# Option 1: Use the installation script
./install.sh

# Option 2: Use the installation script with virtual environment
./install.sh --venv

# Option 3: Manual installation
pip install -e .
```

## Configuration

1. Get a Cerebras API key from [Cerebras Cloud](https://cloud.cerebras.ai/)

2. Create a `.env` file in your project root:
```bash
CEREBRAS_API_KEY=your_api_key_here
```

3. Alternatively, set your API key as an environment variable:
```bash
export CEREBRAS_API_KEY=your_api_key_here
```

## Usage

### Command Line Interface

```bash
# Start the agent in interactive mode
cerebras-agent

# Ask a specific question about the repository without making changes
cerebras-agent --ask "How does this codebase handle authentication?"
cerebras-agent -a "How does this codebase handle authentication?"

# Prompt the agent to perform changes in the repository
cerebras-agent --agent "Add error handling to all database functions"
cerebras-agent -g "Add error handling to all database functions"

# Specify a repository path (default: current directory)
cerebras-agent --repo /path/to/your/repo
cerebras-agent -r /path/to/your/repo
```

### Interactive Commands

Once in the interactive mode, you can use the following commands:

- **`<prompt>`**: Enter any natural language prompt to generate code changes
- **`ask <question>`**: Ask a question about the repository without making changes
- **`checkpoint`**: Show current checkpoint and change history
- **`revert <number>`**: Revert to a specific checkpoint number
- **`help`**: Show available commands
- **`exit`**: Exit the program

## Development

1. Clone the repository:
```bash
git clone https://github.com/jio-gl/cerebras-coding-agent.git
cd cerebras-coding-agent
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
./run_tests.sh
```

4. Run integration tests (requires API key):
```bash
export CEREBRAS_API_KEY=your_api_key_here
./run_integration_tests.sh
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 