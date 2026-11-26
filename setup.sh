#!/bin/bash
#
# Coderabbit One-Time Setup
# Makes coderabbit available in all your coding CLIs (Hermes, Claude Code, Code CLI)
#
# Run this script ONCE to configure your environment:
#   bash setup.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "  Coderabbit One-Time Setup"
echo "============================================"
echo ""
echo "Making coderabbit available in your PATH..."
echo ""

# Check if we can write to /usr/local/bin
if [ -w /usr/local/bin ] || [ "$(id -u)" = "0" ]; then
    echo "Creating symlink in /usr/local/bin..."
    if [ -f "/usr/local/bin/coderabbit" ]; then
        echo "Removing existing symlink..."
        rm /usr/local/bin/coderabbit
    fi
    ln -sf "$SCRIPT_DIR/coderabbit" /usr/local/bin/coderabbit
    echo "✅ coderabbit linked to /usr/local/bin/coderabbit"
else
    echo "Adding coderabbit to PATH via shell profile..."
    PROFILE=""
    if [ -f "$HOME/.zshrc" ]; then
        PROFILE="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        PROFILE="$HOME/.bashrc"
    elif [ -f "$HOME/.profile" ]; then
        PROFILE="$HOME/.profile"
    fi
    
    if [ -n "$PROFILE" ]; then
        # Check if already in profile
        if grep -q "opencode_1/coderabbit" "$PROFILE" 2>/dev/null; then
            echo "coderabbit already in $PROFILE"
        else
            echo 'export PATH="'$SCRIPT_DIR':$PATH"' >> "$PROFILE"
            echo "✅ Added to $PROFILE"
        fi
    else
        echo "❌ Could not find shell profile to update"
        echo "Manually add: export PATH=\"$PATH:$SCRIPT_DIR\""
        exit 1
    fi
fi

# Verify the CLI works
echo ""
echo "Verifying installation..."
if command -v coderabbit &> /dev/null; then
    coderabbit help 2>/dev/null || true
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "How to use in any coding CLI:"
    echo "  1. cd /path/to/your/project"
    echo "  2. coderabbit review"
    echo ""
    echo "No manual configuration needed - it auto-detects project type!"
else
    echo ""
    echo "⚠️  coderabbit not found in PATH yet"
    echo "Open a new terminal or run: source ~/.zshrc (or your shell profile)"
    echo "Then try: coderabbit review"
fi
