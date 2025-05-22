#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if CEREBRAS_API_KEY is set
if [ -z "$CEREBRAS_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ CEREBRAS_API_KEY environment variable not set. Some tests may be skipped.${NC}"
fi

# Run the integration tests
pytest tests/test_integration.py -v

# Check the result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests passed!${NC}"
else
    echo -e "${RED}❌ Integration tests failed!${NC}"
    exit 1
fi 