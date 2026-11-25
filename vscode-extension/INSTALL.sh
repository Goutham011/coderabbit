#!/bin/bash
# Install Agentic VS Code Extension dependencies and compile

set -e

echo "Installing dependencies..."
npm install

echo "Compiling TypeScript..."
npx tsc -p ./

echo "Packaging extension..."
npx vsce package

echo "Done. Run: code --install-extension agentic-vscode-0.1.0.vsix"