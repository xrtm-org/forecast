#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting local development setup...${NC}"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please install it first: https://github.com/astral-sh/uv"
    exit 1
fi

echo -e "${GREEN}Syncing dependencies...${NC}"
uv sync

# Ensure sibling projects are installed in editable mode
# This is often handled by uv sync if specified in dependencies, 
# but we enforce it here for clarity and robustness.
echo -e "${GREEN}Installing sibling projects (data, eval, train) in editable mode...${NC}"
uv pip install -e ../data -e ../eval -e ../train

echo -e "${BLUE}Setup complete!${NC}"
echo -e "Run ${GREEN}uv run pytest${NC} to verify your environment."
