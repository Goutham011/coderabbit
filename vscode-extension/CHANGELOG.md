# Changelog

All notable changes to the Agentic VS Code Extension will be documented in this file.

## [0.1.0] - 2026-11-25

### Added

- Initial VS Code extension release
- Real-time code review on file save
- Inline diagnostics with squiggly underlines
- Review panel webview with detailed findings
- Keyboard shortcuts: Ctrl+Shift+R (review), Ctrl+Shift+A (panel)
- Configurable settings via VS Code settings UI
- Support for Python, JavaScript, TypeScript, Java, Go, Rust
- Auto-skip generated/vendor files
- One-click fix application with user confirmation

### Features

- Review current file (Ctrl+Shift+R)
- Open review panel (Ctrl+Shift+A)
- Review workspace
- Auto-review on save (configurable)

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `agentic.enableOnSave` | true | Run review on file save |
| `agentic.autoApplyFixes` | false | Auto-apply fixes |
| `agentic.severityThreshold` | medium | Minimum severity |
| `agentic.skipGeneratedFiles` | true | Skip vendor files |