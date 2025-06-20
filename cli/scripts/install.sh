#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
COMPLETIONS_DIR="${COMPLETIONS_DIR:-$HOME/.local/share/bash-completion/completions}"

# Detect OS and architecture
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
    linux)
        case "$ARCH" in
            x86_64) TARGET="x86_64-unknown-linux-gnu" ;;
            *) echo -e "${RED}Unsupported architecture: $ARCH${NC}"; exit 1 ;;
        esac
        ;;
    darwin)
        case "$ARCH" in
            x86_64) TARGET="x86_64-apple-darwin" ;;
            arm64) TARGET="aarch64-apple-darwin" ;;
            *) echo -e "${RED}Unsupported architecture: $ARCH${NC}"; exit 1 ;;
        esac
        ;;
    *)
        echo -e "${RED}Unsupported OS: $OS${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Installing Paddi CLI...${NC}"
echo "Target: $TARGET"
echo "Install directory: $INSTALL_DIR"

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Change to CLI directory
cd "$(dirname "$0")/.."

# Build if dist doesn't exist
if [ ! -d "dist" ]; then
    echo -e "${YELLOW}Building Paddi...${NC}"
    bash scripts/build.sh
fi

# Install binary
if [ -f "dist/paddi-$TARGET" ]; then
    echo -e "${YELLOW}Installing binary...${NC}"
    cp "dist/paddi-$TARGET" "$INSTALL_DIR/paddi"
    chmod +x "$INSTALL_DIR/paddi"
    echo -e "${GREEN}✓ Binary installed${NC}"
else
    echo -e "${RED}Binary not found for $TARGET${NC}"
    echo "Please run: cargo build --release --target $TARGET"
    exit 1
fi

# Install shell completions
echo -e "${YELLOW}Installing shell completions...${NC}"

# Detect shell
if [ -n "${BASH_VERSION:-}" ]; then
    SHELL_NAME="bash"
elif [ -n "${ZSH_VERSION:-}" ]; then
    SHELL_NAME="zsh"
elif [ -n "${FISH_VERSION:-}" ]; then
    SHELL_NAME="fish"
else
    SHELL_NAME="unknown"
fi

case "$SHELL_NAME" in
    bash)
        mkdir -p "$COMPLETIONS_DIR"
        cp "dist/completions/paddi.bash" "$COMPLETIONS_DIR/paddi"
        echo -e "${GREEN}✓ Bash completions installed${NC}"
        echo "Add this to your .bashrc:"
        echo "  source $COMPLETIONS_DIR/paddi"
        ;;
    zsh)
        # ZSH completions go in a different place
        ZSH_COMPLETIONS="${ZSH_COMPLETIONS:-${ZDOTDIR:-$HOME}/.zsh/completions}"
        mkdir -p "$ZSH_COMPLETIONS"
        cp "dist/completions/_paddi" "$ZSH_COMPLETIONS/_paddi"
        echo -e "${GREEN}✓ Zsh completions installed${NC}"
        echo "Add this to your .zshrc:"
        echo "  fpath=($ZSH_COMPLETIONS \$fpath)"
        echo "  autoload -U compinit && compinit"
        ;;
    fish)
        FISH_COMPLETIONS="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
        mkdir -p "$FISH_COMPLETIONS"
        cp "dist/completions/paddi.fish" "$FISH_COMPLETIONS/paddi.fish"
        echo -e "${GREEN}✓ Fish completions installed${NC}"
        ;;
    *)
        echo -e "${YELLOW}Could not detect shell for completions${NC}"
        ;;
esac

# Check if install directory is in PATH
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo -e "${YELLOW}Warning: $INSTALL_DIR is not in your PATH${NC}"
    echo "Add this to your shell profile:"
    echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
fi

echo -e "${GREEN}Installation complete!${NC}"
echo "Run 'paddi --help' to get started."