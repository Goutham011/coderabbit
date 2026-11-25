# Agentic VS Code Extension

AI-powered code review for VS Code. Real-time inline annotations and PR review integration.

## Installation

### From VS Code Marketplace (when published)

1. Open VS Code and go to Extensions
2. Search for "Agentic Code Review"
3. Click Install

### From VSIX (local development)

```bash
cd vscode-extension
npm install
npm run compile
npx vsce package
code --install-extension agentic-vscode-0.1.0.vsix
```

### Development Setup

```bash
cd vscode-extension
npm install
npm run compile   # Compile TypeScript
```

## Usage

### Commands

| Command | Keyboard Shortcut | Description |
|---------|------------------|-------------|
| `agentic.reviewFile` | Ctrl+Shift+R (Cmd+Shift+R on macOS) | Review current file |
| `agentic.reviewWorkspace` | - | Review entire workspace |
| `agentic.openPanel` | Ctrl+Shift+A (Cmd+Shift+A on macOS) | Open review panel |

### Features

- **Real-time review on save** - Automatically analyzes code when you save files
- **Inline annotations** - Findings appear as squiggly underlines in the editor
- **Review panel** - Detailed webview panel with all findings
- **One-click fixes** - Apply suggestions directly

### Settings

Open VS Code Settings (Ctrl+,) and search for "agentic":

| Setting | Default | Description |
|---------|---------|-------------|
| `agentic.enableOnSave` | true | Run review on file save |
| `agentic.autoApplyFixes` | false | Auto-apply fixes without prompting |
| `agentic.severityThreshold` | medium | Minimum severity to display |
| `agentic.skipGeneratedFiles` | true | Skip vendor and generated files |

## Requirements

- Agentic CLI v0.5.0 or later (https://github.com/nousresearch/agentic)
- Python 3.8+
- Node.js 18+

## Extension Settings

This extension contributes the following settings:

* `agentic.enableOnSave`: Run code review on file save
* `agentic.autoApplyFixes`: Automatically apply one-click fixes
* `agentic.severityThreshold`: Minimum severity to display
* `agentic.skipGeneratedFiles`: Skip generated and vendor files

## Development

### Building the Extension

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Package for distribution
npm run vscode:prepublish
npx vsce package
```

### Running Tests

```bash
npm run compile
npm test
```

### Debugging

1. Press F5 in VS Code to launch Extension Development Host
2. Open a Python/JavaScript/TypeScript file
3. Run commands via Command Palette (Ctrl+Shift+P):
   - "Agentic: Review Current File"

## Known Issues

- Initial load may take a few seconds
- Large files may have delayed review

## Release Notes

#### 0.1.0

- Initial release
- Real-time review on save
- Inline diagnostics
- Review panel webview
- Keyboard shortcuts