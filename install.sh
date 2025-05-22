#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Installing Cerebras Coding Agent...${NC}"

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is not installed. Please install pip first.${NC}"
    exit 1
fi

# Create a virtual environment (optional)
if [ "$1" == "--venv" ] || [ "$1" == "-v" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment created and activated.${NC}"
fi

# Install the package
echo -e "${YELLOW}Installing package...${NC}"
pip install -e .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Cerebras Coding Agent installed successfully!${NC}"
    echo -e "${YELLOW}You can now use the 'cerebras-agent' command.${NC}"
    
    # Check if CEREBRAS_API_KEY is set
    if [ -z "$CEREBRAS_API_KEY" ]; then
        echo -e "${YELLOW}⚠️ CEREBRAS_API_KEY environment variable not set.${NC}"
        echo -e "${YELLOW}Please set your API key using:${NC}"
        echo -e "export CEREBRAS_API_KEY=your_api_key_here"
        echo -e "${YELLOW}Or create a .env file in your project directory.${NC}"
    fi
else
    echo -e "${RED}❌ Installation failed.${NC}"
    exit 1
fi 