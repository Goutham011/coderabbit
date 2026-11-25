"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
/**
 * Agentic VS Code Extension
 * Real-time AI code review for developers.
 *
 * SECURITY: This extension sanitizes all user-controlled data before rendering
 * in webviews to prevent XSS attacks.
 */
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
/**
 * SECURITY: Escape HTML special characters to prevent XSS.
 * All user-controlled data must be escaped before embedding in HTML.
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    };
    return text.replace(/[&<>"'`=/]/g, (m) => map[m]);
}
/**
 * SECURITY: Validate URL to prevent javascript: and data: schemes.
 */
function isValidUrl(url) {
    try {
        const parsed = new URL(url);
        return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    }
    catch {
        return false;
    }
}
/**
 * SECURITY: Escape URL to prevent javascript: and data: schemes.
 */
function escapeUrl(url) {
    if (!isValidUrl(url)) {
        return '#';
    }
    return escapeHtml(url);
}
/**
 * Get line number safely.
 */
function getLineNumber(finding) {
    return finding.line_number ?? 0;
}
/**
 * Get severity color safely.
 */
function getSeverityColor(severity) {
    const colors = {
        critical: '#ff5252',
        high: '#ff9800',
        medium: '#ffc107',
        low: '#4caf50',
        info: '#2196f3'
    };
    return colors[severity] || '#9e9e9e';
}
/**
 * Decorate a location with a diagnostic.
 */
function createDiagnostic(finding, severity) {
    const line = getLineNumber(finding);
    const message = escapeHtml(finding.message);
    const diagnostic = new vscode.Diagnostic(new vscode.Range(line, finding.column_number || 0, line, (finding.column_number || 0) + 1), message, severity);
    if (finding.suggestion) {
        diagnostic.code = escapeHtml(finding.suggestion);
        diagnostic.source = 'agentic';
    }
    return diagnostic;
}
/**
 * Run agentic review on current file.
 */
async function runReviewOnFile(filePath) {
    const config = vscode.workspace.getConfiguration('agentic');
    const enableOnSave = config.get('enableOnSave', true);
    if (!enableOnSave) {
        return null;
    }
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        return null;
    }
    try {
        const output = await execAsync(`agentic review "${escapeHtml(workspaceFolders[0].uri.fsPath)}" HEAD --output json`);
        const result = JSON.parse(output.stdout);
        return result;
    }
    catch (error) {
        console.error('Agentic review failed:', error);
        return null;
    }
}
/**
 * Apply a one-click fix for a finding.
 */
async function applyFix(finding, document) {
    if (!finding.suggestion) {
        vscode.window.showInformationMessage('No fix available for this finding');
        return false;
    }
    const config = vscode.workspace.getConfiguration('agentic');
    const autoApply = config.get('autoApplyFixes', false);
    if (!autoApply) {
        const apply = await vscode.window.showInformationMessage(`Apply fix: ${escapeHtml(finding.message)}`, 'Apply', 'Cancel');
        if (apply !== 'Apply') {
            return false;
        }
    }
    try {
        const line = getLineNumber(finding);
        const edit = new vscode.WorkspaceEdit();
        edit.replace(document.uri, new vscode.Range(line, 0, line, document.lineAt(line).text.length), finding.suggestion);
        await vscode.workspace.applyEdit(edit);
        await document.save();
        return true;
    }
    catch (error) {
        vscode.window.showErrorMessage(`Failed to apply fix: ${error}`);
        return false;
    }
}
/**
 * Show the review panel with detailed findings.
 */
function showReviewPanel(result) {
    const panel = vscode.window.createWebviewPanel('agenticReview', `Code Review: ${escapeHtml(result.repo)}@${escapeHtml(result.branch)}`, vscode.ViewColumn.Beside, {
        enableScripts: true,
        retainContextWhenHidden: true
    });
    const html = generateReviewHtml(result);
    panel.webview.html = html;
}
/**
 * Generate HTML for the review panel.
 * SECURITY: All user-controlled data is properly escaped to prevent XSS.
 */
function generateReviewHtml(result) {
    const findingsHtml = result.findings
        .map(f => {
        const color = getSeverityColor(f.severity);
        const ruleOrId = f.rule || f.id;
        const escapedRuleId = escapeHtml(ruleOrId);
        const escapedMessage = escapeHtml(f.message);
        const escapedSuggestion = f.suggestion ? escapeHtml(f.suggestion) : '';
        const escapedReference = f.reference ? escapeUrl(f.reference) : '';
        let suggestionHtml = '';
        if (f.suggestion) {
            suggestionHtml = `<details><summary>Suggestion</summary><p>${escapedSuggestion}</p></details>`;
        }
        let referenceHtml = '';
        if (f.reference && isValidUrl(f.reference)) {
            referenceHtml = `<p><a href="${escapedReference}" target="_blank">Reference</a></p>`;
        }
        return `
        <div class="finding" style="border-left: 4px solid ${color};">
          <h4>${escapeHtml(f.severity.toUpperCase())}: ${escapedRuleId}</h4>
          <p>${escapedMessage}</p>
          ${suggestionHtml}
          ${referenceHtml}
        </div>
      `;
    })
        .join('');
    const severityColor = getSeverityColor(result.overall_severity);
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agentic Review</title>
  <style>
    body { font-family: var(--vscode-font-family); padding: 16px; background: var(--vscode-editor-background); color: var(--vscode-editor-foreground); }
    .header { margin-bottom: 16px; }
    .summary { background: var(--vscode-editorBlock-start-background); padding: 12px; border-radius: 4px; margin-bottom: 16px; }
    .severity-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; color: white; font-weight: bold; }
    .finding { background: var(--vscode-editorBlock-begin-background); padding: 12px; margin-bottom: 8px; border-radius: 4px; }
    .details { margin-top: 8px; }
  </style>
</head>
<body>
  <div class="header">
    <h2>Code Review Results</h2>
    <p><strong>Repository:</strong> ${escapeHtml(result.repo)}</p>
    <p><strong>Branch:</strong> ${escapeHtml(result.branch)}</p>
  </div>
  <div class="summary">
    <p><strong>Overall Severity:</strong> 
      <span class="severity-badge" style="background: ${severityColor};">
        ${escapeHtml(result.overall_severity.toUpperCase())}
      </span>
    </p>
    <p><strong>Findings:</strong> ${result.findings_count} | <strong>Confidence:</strong> ${(result.confidence * 100).toFixed(1)}%</p>
    <p>${escapeHtml(result.summary)}</p>
  </div>
  ${findingsHtml || '<p>No findings.</p>'}
</body>
</html>`;
}
/**
 * Main extension activation.
 */
function activate(context) {
    console.log('Agentic Code Review extension activated');
    // Diagnostic collection for all documents
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('agentic');
    context.subscriptions.push(diagnosticCollection);
    // Command: Review current file
    const reviewFile = vscode.commands.registerCommand('agentic.reviewFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showInformationMessage('No active editor');
            return;
        }
        const result = await runReviewOnFile(editor.document.fileName);
        if (!result) {
            return;
        }
        // Show findings in the panel
        showReviewPanel(result);
        // Update diagnostics
        const diagnostics = [];
        for (const finding of result.findings) {
            const severityMap = {
                critical: vscode.DiagnosticSeverity.Error,
                high: vscode.DiagnosticSeverity.Error,
                medium: vscode.DiagnosticSeverity.Warning,
                low: vscode.DiagnosticSeverity.Information,
                info: vscode.DiagnosticSeverity.Information
            };
            const diagnostic = createDiagnostic(finding, severityMap[finding.severity] || vscode.DiagnosticSeverity.Information);
            diagnostics.push(diagnostic);
        }
        diagnosticCollection.set(editor.document.uri, diagnostics);
        vscode.window.showInformationMessage(`Agentic review complete: ${result.findings_count} findings`);
    });
    // Command: Open review panel
    const openPanel = vscode.commands.registerCommand('agentic.openPanel', () => {
        vscode.commands.executeCommand('workbench.view.explorer', 'agenticReviewPanel');
    });
    // Command: Review workspace
    const reviewWorkspace = vscode.commands.registerCommand('agentic.reviewWorkspace', async () => {
        const result = await runReviewOnFile('workspace');
        if (result) {
            showReviewPanel(result);
        }
    });
    // Command: Review last save
    const reviewSaved = vscode.commands.registerCommand('agentic.reviewSaved', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }
        const result = await runReviewOnFile(editor.document.fileName);
        if (result) {
            showReviewPanel(result);
        }
    });
    // Handle file saves
    const saveObserver = vscode.workspace.onDidSaveTextDocument(async (document) => {
        const config = vscode.workspace.getConfiguration('agentic');
        const enableOnSave = config.get('enableOnSave', true);
        if (!enableOnSave) {
            return;
        }
        const skipGenerated = config.get('skipGeneratedFiles', true);
        if (skipGenerated) {
            const fileName = document.fileName.toLowerCase();
            if (fileName.includes('node_modules') ||
                fileName.includes('.min.') ||
                fileName.includes('vendor/') ||
                document.fileName.endsWith('.map')) {
                return;
            }
        }
        // Run review asynchronously
        setTimeout(async () => {
            const result = await runReviewOnFile(document.fileName);
            if (!result) {
                return;
            }
            // Update diagnostics
            const diagnostics = [];
            for (const finding of result.findings) {
                const severityMap = {
                    critical: vscode.DiagnosticSeverity.Error,
                    high: vscode.DiagnosticSeverity.Error,
                    medium: vscode.DiagnosticSeverity.Warning,
                    low: vscode.DiagnosticSeverity.Information,
                    info: vscode.DiagnosticSeverity.Information
                };
                const diagnostic = createDiagnostic(finding, severityMap[finding.severity] || vscode.DiagnosticSeverity.Information);
                diagnostics.push(diagnostic);
            }
            const currentEditor = vscode.window.activeTextEditor;
            if (currentEditor?.document.uri === document.uri) {
                diagnosticCollection.set(document.uri, diagnostics);
            }
        }, 100);
    });
    context.subscriptions.push(reviewFile, openPanel, reviewWorkspace, reviewSaved, saveObserver);
}
/**
 * Main extension deactivation.
 */
function deactivate() {
    // Extension cleanup handled by VS Code
}
//# sourceMappingURL=extension.js.map