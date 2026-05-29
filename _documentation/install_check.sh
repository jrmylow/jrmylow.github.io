#!/bin/bash

# Dependency checker for Jekyll blog project
# Checks for required tools without installing anything

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

missing=0

check_command() {
    local cmd=$1
    local name=$2
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}[OK]${NC} $name found: $(command -v "$cmd")"
    else
        echo -e "${RED}[MISSING]${NC} $name not found"
        missing=1
    fi
}

echo "Checking dependencies..."
echo ""

# Ruby ecosystem
echo "=== Ruby Dependencies ==="
check_command ruby "Ruby"
check_command bundle "Bundler"
check_command jekyll "Jekyll"

echo ""

# Python ecosystem
echo "=== Python Dependencies ==="
check_command python3 "Python 3"
check_command uv "uv"

echo ""

# Summary
if [ $missing -eq 0 ]; then
    echo -e "${GREEN}All dependencies found.${NC}"
    exit 0
else
    echo -e "${RED}Some dependencies are missing. Please install them before proceeding.${NC}"
    exit 1
fi
