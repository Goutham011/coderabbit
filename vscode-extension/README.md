<p align="center">
  <img src="assets/app_icon.png" width="150" alt="Coderabbit VS Code Logo" />
</p>

<h1 align="center">Coderabbit VS Code</h1>

<p align="center">
  <strong>Code review for AI agents — inside VS Code.</strong><br>
  Real-time inline annotations and PR review integration for your AI-powered development workflow.
</p>

<p align="center">
  <strong>English</strong>
</p>

<p align="center">
  <a href="https://github.com/Goutham011/coderabbit/stargazers"><img src="https://img.shields.io/github/stars/Goutham011/coderabbit?style=flat-square&color=gold" alt="GitHub stars" /></a>
  <a href="https://github.com/Goutham011/coderabbit/releases/latest"><img src="https://img.shields.io/github/v/release/Goutham011/coderabbit?style=flat-square&color=blue" alt="Latest release" /></a>
  <img src="https://img.shields.io/badge/platform-VS%20Code-neon?style=flat-square&color=green" alt="VS Code" />
  <img src="https://img.shields.io/badge/language-TypeScript-blue?style=flat-square" alt="TypeScript" />
</p>

---

## Why Coderabbit VS Code?

Bring AI-powered code review directly into your development environment. Get instant feedback, find issues before they become bugs, and let your agent understand code quality metrics in real-time.

- **Native VS Code integration** — Seamlessly works with VS Code's ecosystem
- **Real-time on save** — Automatically reviews code when you save files
- **Inline annotations** — Findings appear as squiggly underlines in the editor
- **One-click fixes** — Apply suggestions directly without leaving your workflow
- **Webview panel** — Detailed review results with interactive filtering
- **Agent-friendly output** — JSON-compatible data for AI agent consumption

---

## Features at a glance

<table>
<tr>
<td width="33%" valign="top">

### 🔍 Review
- **File review** — Analyze the current file on-demand
- **Workspace review** — Scan your entire project
- **On-save analysis** — Automatic review when files are saved
- **Severity filtering** — Show only issues above a threshold

</td>
<td width="33%" valign="top">

### 📋 Panel
- **Webview dashboard** — Comprehensive review results
- **Group by file/type** — Organize findings logically
- **Export findings** — Copy or save review results as JSON
- **Toggle annotations** — Show/hide inline markers

</td>
<td width="33%" valign="top">

### ⚙️ Configuration
- **Settings UI** — Configure via VS Code Settings
- **Auto-fixes** — Apply corrections automatically
- **Generated files** — Skip node_modules, build outputs
- **Custom rules** — Extend via `.agentic.yaml`

</td>
</tr>
</table>

---

## Features in detail

### 🔍 Inline Review
| Feature | Shortcut | Description |
|---------|----------|-------------|
| Review Current File | `Ctrl+Shift+R` | Analyze the active editor file |
| Review Workspace | `Ctrl+Shift+A` | Full project scan with results panel |
| Open Panel | `Ctrl+Shift+A` | Show detailed review dashboard |
| Auto-apply Fixes | Settings | One-click resolution of found issues |

### 📋 Webview Panel
| Section | Description |
|---------|-------------|
| **Findings list** | All issues with severity and location |
| **File view** | Group issues by affected file |
| **Severity filter** | Show high/medium/low priority only |
| **Export JSON** | Copy results for agent processing |

### ⚙️ Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `agentic.enableOnSave` | true | Run review automatically on file save |
| `agentic.autoApplyFixes` | false | Apply one-click fixes without prompting |
| `agentic.severityThreshold` | medium | Minimum severity to display |
| `agentic.skipGeneratedFiles` | true | Skip vendor and generated files |

---

## Installation

### From VS Code Marketplace (when published)

1. Open VS Code and go to Extensions
2. Search for "Coderabbit Code Review"
3. Click Install

### From VSIX (local development)

```bash
cd vscode-extension
npm install
npm run compile
npx vsce package
code --install-extension agentic-vscode-0.1.0.vsix
```

---

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
   - "Coderabbit: Review Current File"
   - "Coderabbit: Review Workspace"

---

## Requirements

- **Coderabbit CLI v0.5.0 or later** — Install with `pip install -e .`
- **Python 3.8+** — For running the review engine
- **Node.js 18+** — For the VS Code extension

---

## Architecture

```
┌──────────────────────────────────────────┐
│           VS Code Extension              │
│  ┌─────────────────┐  ┌────────────────┐  │
│  │  Commands       │  │  Webview     │  │
│  │  (Ctrl+Shift+R)│  │  (Results)   │  │
│  └───────┬─────────┘  └───────┬────────┘  │
└──────────┼────────────────────┼───────────┘
           │                    │
           ▼                    ▼
┌──────────────────────────────────────────┐
│           JSON API Layer                 │
│  ┌─────────────────┐  ┌────────────────┐  │
│  │   Request       │  │   Response     │  │
│  │   Builder       │  │   Parser       │  │
│  └─────────────────┘  └────────────────┘  │
└───────────────────────┬─────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────┐
│           Coderabbit CLI                 │
│  ┌─────────────────┐  ┌────────────────┐  │
│  │   Analyzer      │  │   Reporter     │  │
│  │   (Semgrep,     │  │   (JSON, Human)│  │
│  │    ESLint, etc)  │  └────────────────┘  │
│  └─────────────────┘                      │
└──────────────────────────────────────────┘
```

---

## Known Issues

- Initial load may take a few seconds
- Large files may have delayed review
- Requires Coderabbit CLI to be in PATH

---

## Release Notes

#### 0.1.0
- Initial release
- Real-time review on save
- Inline diagnostics
- Review panel webview
- Keyboard shortcuts

---

## License

MIT License — See [LICENSE](../LICENSE) file for details.

---

## Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Acknowledgments

- [VS Code Extension API](https://code.visualstudio.com/api) — Official extension framework
- [Semgrep](https://semgrep.dev/) — Static analysis rules
- [Ruff](https://ruff.rs/) — Python linter

<p align="center">
  <strong>Built for AI-powered development workflows.</strong><br>
  If you're building the next generation of code, a ⭐ helps others find it.
</p>