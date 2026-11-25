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
/**
 * Tests for Agentic VS Code Extension
 */
const assert = __importStar(require("assert"));
const vscode = __importStar(require("vscode"));
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
//# sourceMappingURL=extension.test.js.map