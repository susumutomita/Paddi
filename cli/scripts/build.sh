#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Paddi CLI...${NC}"

# Change to CLI directory
cd "$(dirname "$0")/.."

# Build for multiple targets
targets=(
    "x86_64-unknown-linux-gnu"
    "x86_64-apple-darwin"
    "aarch64-apple-darwin"
    "x86_64-pc-windows-gnu"
)

# Create dist directory
mkdir -p dist

for target in "${targets[@]}"; do
    echo -e "${YELLOW}Building for ${target}...${NC}"
    
    # Check if target is installed
    if ! rustup target list --installed | grep -q "$target"; then
        echo -e "${YELLOW}Installing target ${target}...${NC}"
        rustup target add "$target"
    fi
    
    # Build release binary
    if cargo build --release --target "$target"; then
        # Copy to dist with target suffix
        if [[ "$target" == *"windows"* ]]; then
            cp "target/$target/release/paddi.exe" "dist/paddi-$target.exe"
        else
            cp "target/$target/release/paddi" "dist/paddi-$target"
        fi
        echo -e "${GREEN}✓ Built ${target}${NC}"
    else
        echo -e "${RED}✗ Failed to build ${target}${NC}"
    fi
done

# Generate shell completions
echo -e "${YELLOW}Generating shell completions...${NC}"
mkdir -p dist/completions

# Build once for the host platform to generate completions
cargo build --release

# Generate completions
./target/release/paddi completions bash > dist/completions/paddi.bash
./target/release/paddi completions zsh > dist/completions/_paddi
./target/release/paddi completions fish > dist/completions/paddi.fish
./target/release/paddi completions powershell > dist/completions/_paddi.ps1

echo -e "${GREEN}Build complete! Binaries are in cli/dist/${NC}"