/**
 * Tests for Agentic VS Code Extension
 */
import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Agentic Extension Test Suite', () => {
  test('Extension should be activated', () => {
    assert.ok(vscode.extensions.getExtension('coderabbit-vscode'));
  });

  test('Review command should be registered', async () => {
    const commands = await vscode.commands.getCommands();
    assert.ok(commands.includes('coderabbit.reviewFile'));
  });

  test('Open panel command should be registered', async () => {
    const commands = await vscode.commands.getCommands();
    assert.ok(commands.includes('coderabbit.openPanel'));
  });

  test('Review workspace command should be registered', async () => {
    const commands = await vscode.commands.getCommands();
    assert.ok(commands.includes('coderabbit.reviewWorkspace'));
  });

  test('Settings should have coderabbit configuration', async () => {
    const config = vscode.workspace.getConfiguration('coderabbit');
    assert.ok(config.has('enableOnSave'));
    assert.ok(config.has('autoApplyFixes'));
    assert.ok(config.has('severityThreshold'));
    assert.ok(config.has('skipGeneratedFiles'));
  });
});