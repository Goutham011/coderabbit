/**
 * Tests for Agentic VS Code Extension
 */
import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Agentic Extension Test Suite', () => {
  test('Extension should be activated', () => {
    assert.ok(vscode.extensions.getExtension('agentic-vscode'));
  });

  test('Review command should be registered', async () => {
    const commands = await vscode.commands.getCommands();
    assert.ok(commands.includes('agentic.reviewFile'));
  });

  test('Open panel command should be registered', async () => {
    const commands = await vscode.commands.getCommands();
    assert.ok(commands.includes('agentic.openPanel'));
  });

  test('Review workspace command should be registered', async () => {
    const commands = await vscode.commands.getCommands();
    assert.ok(commands.includes('agentic.reviewWorkspace'));
  });

  test('Settings should have agentic configuration', async () => {
    const config = vscode.workspace.getConfiguration('agentic');
    assert.ok(config.has('enableOnSave'));
    assert.ok(config.has('autoApplyFixes'));
    assert.ok(config.has('severityThreshold'));
    assert.ok(config.has('skipGeneratedFiles'));
  });
});