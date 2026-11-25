/**
 * Agentic VS Code Extension
 * Real-time AI code review for developers.
 * 
 * SECURITY: This extension sanitizes all user-controlled data before rendering
 * in webviews to prevent XSS attacks.
 */
import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * Represents a code review finding.
 */
interface Finding {
  id: string;
  tool: string;
  rule?: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  message: string;
  file_path?: string;
  line_number?: number;
  column_number?: number;
  suggestion?: string;
  reference?: string;
}

/**
 * Review result from coderabbit CLI.
 */
interface ReviewResult {
  repo: string;
  branch: string;
  overall_severity: string;
  findings_count: number;
  findings: Finding[];
  summary: string;
  confidence: number;
  metadata: Record<string, unknown>;
}

/**
 * SECURITY: Escape HTML special characters to prevent XSS.
 * All user-controlled data must be escaped before embedding in HTML.
 */
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
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
function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

/**
 * SECURITY: Escape URL to prevent javascript: and data: schemes.
 */
function escapeUrl(url: string): string {
  if (!isValidUrl(url)) {
    return '#';
  }
  return escapeHtml(url);
}

/**
 * Get line number safely.
 */
function getLineNumber(finding: Finding): number {
  return finding.line_number ?? 0;
}

/**
 * Get severity color safely.
 */
function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
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
function createDiagnostic(
  finding: Finding,
  severity: vscode.DiagnosticSeverity
): vscode.Diagnostic {
  const line = getLineNumber(finding);
  const message = escapeHtml(finding.message);
  const diagnostic = new vscode.Diagnostic(
    new vscode.Range(
      line,
      finding.column_number || 0,
      line,
      (finding.column_number || 0) + 1
    ),
    message,
    severity
  );

  if (finding.suggestion) {
    diagnostic.code = escapeHtml(finding.suggestion);
    diagnostic.source = 'coderabbit';
  }

  return diagnostic;
}

/**
 * Run coderabbit review on current file.
 */
async function runReviewOnFile(filePath: string): Promise<ReviewResult | null> {
  const config = vscode.workspace.getConfiguration('coderabbit');
  const enableOnSave = config.get<boolean>('enableOnSave', true);

  if (!enableOnSave) {
    return null;
  }

  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders) {
    return null;
  }

  try {
    const output = await execAsync(
      `coderabbit review "${escapeHtml(workspaceFolders[0].uri.fsPath)}" HEAD --output json`
    );

    const result: ReviewResult = JSON.parse(output.stdout);
    return result;
  } catch (error) {
    console.error('Agentic review failed:', error);
    return null;
  }
}

/**
 * Apply a one-click fix for a finding.
 */
async function applyFix(
  finding: Finding,
  document: vscode.TextDocument
): Promise<boolean> {
  if (!finding.suggestion) {
    vscode.window.showInformationMessage('No fix available for this finding');
    return false;
  }

  const config = vscode.workspace.getConfiguration('coderabbit');
  const autoApply = config.get<boolean>('autoApplyFixes', false);

  if (!autoApply) {
    const apply = await vscode.window.showInformationMessage(
      `Apply fix: ${escapeHtml(finding.message)}`,
      'Apply',
      'Cancel'
    );

    if (apply !== 'Apply') {
      return false;
    }
  }

  try {
    const line = getLineNumber(finding);
    const edit = new vscode.WorkspaceEdit();
    edit.replace(
      document.uri,
      new vscode.Range(
        line,
        0,
        line,
        document.lineAt(line).text.length
      ),
      finding.suggestion
    );

    await vscode.workspace.applyEdit(edit);
    await document.save();
    return true;
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to apply fix: ${error}`);
    return false;
  }
}

/**
 * Show the review panel with detailed findings.
 */
function showReviewPanel(result: ReviewResult): void {
  const panel = vscode.window.createWebviewPanel(
    'coderabbitReview',
    `Code Review: ${escapeHtml(result.repo)}@${escapeHtml(result.branch)}`,
    vscode.ViewColumn.Beside,
    {
      enableScripts: true,
      retainContextWhenHidden: true
    }
  );

  const html = generateReviewHtml(result);
  panel.webview.html = html;
}

/**
 * Generate HTML for the review panel.
 * SECURITY: All user-controlled data is properly escaped to prevent XSS.
 */
function generateReviewHtml(result: ReviewResult): string {
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
export function activate(context: vscode.ExtensionContext): void {
  console.log('Agentic Code Review extension activated');

  // Diagnostic collection for all documents
  const diagnosticCollection = vscode.languages.createDiagnosticCollection('coderabbit');
  context.subscriptions.push(diagnosticCollection);

  // Command: Review current file
  const reviewFile = vscode.commands.registerCommand(
    'coderabbit.reviewFile',
    async () => {
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
      const diagnostics: vscode.Diagnostic[] = [];
      for (const finding of result.findings) {
        const severityMap: Record<string, vscode.DiagnosticSeverity> = {
          critical: vscode.DiagnosticSeverity.Error,
          high: vscode.DiagnosticSeverity.Error,
          medium: vscode.DiagnosticSeverity.Warning,
          low: vscode.DiagnosticSeverity.Information,
          info: vscode.DiagnosticSeverity.Information
        };

        const diagnostic = createDiagnostic(
          finding,
          severityMap[finding.severity] || vscode.DiagnosticSeverity.Information
        );
        diagnostics.push(diagnostic);
      }

      diagnosticCollection.set(
        editor.document.uri,
        diagnostics
      );

      vscode.window.showInformationMessage(
        `Agentic review complete: ${result.findings_count} findings`
      );
    }
  );

  // Command: Open review panel
  const openPanel = vscode.commands.registerCommand(
    'coderabbit.openPanel',
    () => {
      vscode.commands.executeCommand('workbench.view.explorer', 'coderabbitReviewPanel');
    }
  );

  // Command: Review workspace
  const reviewWorkspace = vscode.commands.registerCommand(
    'coderabbit.reviewWorkspace',
    async () => {
      const result = await runReviewOnFile('workspace');
      if (result) {
        showReviewPanel(result);
      }
    }
  );

  // Command: Review last save
  const reviewSaved = vscode.commands.registerCommand(
    'coderabbit.reviewSaved',
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        return;
      }

      const result = await runReviewOnFile(editor.document.fileName);
      if (result) {
        showReviewPanel(result);
      }
    }
  );

  // Handle file saves
  const saveObserver = vscode.workspace.onDidSaveTextDocument(
    async (document) => {
      const config = vscode.workspace.getConfiguration('coderabbit');
      const enableOnSave = config.get<boolean>('enableOnSave', true);

      if (!enableOnSave) {
        return;
      }

      const skipGenerated = config.get<boolean>('skipGeneratedFiles', true);
      if (skipGenerated) {
        const fileName = document.fileName.toLowerCase();
        if (
          fileName.includes('node_modules') ||
          fileName.includes('.min.') ||
          fileName.includes('vendor/') ||
          document.fileName.endsWith('.map')
        ) {
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
        const diagnostics: vscode.Diagnostic[] = [];
        for (const finding of result.findings) {
          const severityMap: Record<string, vscode.DiagnosticSeverity> = {
            critical: vscode.DiagnosticSeverity.Error,
            high: vscode.DiagnosticSeverity.Error,
            medium: vscode.DiagnosticSeverity.Warning,
            low: vscode.DiagnosticSeverity.Information,
            info: vscode.DiagnosticSeverity.Information
          };

          const diagnostic = createDiagnostic(
            finding,
            severityMap[finding.severity] || vscode.DiagnosticSeverity.Information
          );
          diagnostics.push(diagnostic);
        }

        const currentEditor = vscode.window.activeTextEditor;
        if (currentEditor?.document.uri === document.uri) {
          diagnosticCollection.set(document.uri, diagnostics);
        }
      }, 100);
    }
  );

  context.subscriptions.push(reviewFile, openPanel, reviewWorkspace, reviewSaved, saveObserver);
}

/**
 * Main extension deactivation.
 */
export function deactivate(): void {
  // Extension cleanup handled by VS Code
}