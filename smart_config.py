#!/usr/bin/env python3
"""
Smart Project Type Detector for Coderabbit
Detects project type and auto-configures appropriate analysis rules
Works without external dependencies - uses native Python
"""

import os
import sys
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

# All supported project types with their indicators
PROJECT_INDICATORS = {
    'android': {
        'files': ['build.gradle', 'build.gradle.kts', 'AndroidManifest.xml', 'gradle.properties'],
        'dirs': ['src/main', 'gradle'],
        'keywords': ['com.android.application', 'com.google.gms', 'HiltAndroidApp', 'RoomDatabase']
    },
    'react': {
        'files': ['package.json', 'tsconfig.json', 'tsconfig.tsx'],
        'keywords': ['react', 'next', 'vite', 'webpack', '@types/react']
    },
    'vue': {
        'files': ['package.json', 'vue.config.js', 'vite.config.ts'],
        'keywords': ['vue', 'nuxt', '@types/vue']
    },
    'python': {
        'files': ['requirements.txt', 'setup.py', 'pyproject.toml'],
        'keywords': ['flask', 'django', 'fastapi', 'requests']
    },
    'node_api': {
        'files': ['package.json', 'index.js', 'server.js'],
        'keywords': ['express', 'koa', 'fastify']
    },
    'rust': {
        'files': ['Cargo.toml'],
        'keywords': ['serde', 'tokio', 'actix']
    },
    'go': {
        'files': ['go.mod', 'main.go'],
        'keywords': ['gin', 'gorm', 'echo', 'grpc']
    }
}

# Security patterns to detect (for all project types)
SECURITY_PATTERNS = [
    # Android hardcoded secrets
    (r'storePassword\s*=\s*["\'][^"\']+["\']', 'CRITICAL', 
     'Hardcoded keystore password', 
     'Use env vars or gradle.properties: `storePassword = System.getenv("KEYSTORE_PASSWORD")`'),
    (r'keyPassword\s*=\s*["\'][^"\']+["\']', 'CRITICAL', 
     'Hardcoded keystore key password',
     'Use env vars: `keyPassword = System.getenv("KEY_PASSWORD")`'),
    (r'API_KEY\s*=\s*["\'][^"\']{10,}["\']', 'HIGH', 
     'Hardcoded API key',
     'Move to local.properties or secure storage'),
    (r'PASSPHRASE\s*=\s*["\'][^"\']+["\']', 'HIGH', 
     'Hardcoded database passphrase',
     'Use environment variables or encrypted storage'),
    
    # Web XSS
    (r'innerHTML\s*=', 'MEDIUM', 
     'Potential XSS vulnerability',
     'Use textContent or sanitization library like DOMPurify'),
    (r'dangerouslySetInnerHTML', 'HIGH', 
     'Potential XSS vulnerability',
     'Sanitize HTML before rendering: use DOMPurify.sanitize()'),
    (r'document\.write\s*\(', 'MEDIUM', 
     'DOM injection risk',
     'Use innerHTML/textContent or DOM manipulation methods'),
    
    # Python security
    (r'execute\s*\([^)]*format', 'CRITICAL', 
     'Potential SQL injection',
     'Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))'),
    (r'\+.*execute\s*\(', 'CRITICAL', 
     'Potential SQL injection',
     'Use parameterized queries instead of string concatenation'),
    (r'password\s*=\s*["\'][^"\']{3,}["\']', 'HIGH', 
     'Hardcoded password',
     'Use environment variables: `password = os.getenv("DB_PASSWORD")`'),
    (r'api_key\s*=\s*["\'][^"\']{10,}["\']', 'HIGH', 
     'Hardcoded API key',
     'Move to .env file and load with python-dotenv'),
    
    # General security
    (r'\beval\s*\(', 'HIGH', 
     'Code injection risk',
     'Avoid eval - use json.loads, ast.literal_eval, or built-ins'),
    (r'\bexec\s*\(', 'HIGH', 
     'Code injection risk',
     'Avoid exec - refactor to use functions/dynamic imports'),
    (r'pickle\.loads?\s*\(', 'HIGH', 
     'Unsafe deserialization',
     'Use json, YAML with safe_load, or protobuf instead'),
    (r'subprocess\..*shell\s*=\s*True', 'MEDIUM', 
     'Shell injection risk',
     'Use shell=False and pass args as list: subprocess.run(cmd, shell=False)'),
]

# Architecture issues
ARCHITECTURE_PATTERNS = [
    (r'private\s+companion\s+object', 'MEDIUM', 
     'Consider using object instead',
     'Replace with: `object MyManager` - singletons in Kotlin should use object declarations'),
    (r'Handler\s*\(\s*\)', 'MEDIUM', 
     'Handler without Looper may crash',
     'Use Handler(Looper.getMainLooper()) for UI thread or Looper.myLooper() for current thread'),
    (r'Bitmap\.createBitmap', 'MEDIUM', 
     'Consider bitmap reuse',
     'Use inBitmap option for memory-efficient bitmap reuse: Bitmap.createBitmap(width, height, config, true, true, inBitmap)'),
]

# AI Slop / Quality issues - patterns to detect verbose/inflated code
AI_SLIP_PATTERNS = [
    # Overly verbose comments
    (r'//\s*[a-zA-Z\s]{50,}', 'INFO', 
     'Overly verbose comment - consider shorter, meaningful comments',
     'Remove redundant explanation. Code should be self-documenting.'),
    # Overly detailed TODOs
    (r'TODO.*[a-zA-Z\s]{40,}', 'INFO',
     'Overly detailed TODO comment - split into smaller issues',
     'Break into specific tickets. Keep TODOs under 80 chars with clear action items'),
    # Redundant code
    (r'if\s*\(\s*true\s*\)', 'LOW', 
     'Redundant true check',
     'Remove the redundant if(condition) wrapper'),
    (r'if\s*\(\s*false\s*\)', 'LOW',
     'Dead code - condition is always false',
     'Remove the if(false) block or add proper condition'),
    (r'duplicate\s*=\s*true', 'LOW',
     'Duplicate marker found - review if truly duplicate',
     'Remove duplicate=true if code is intentionally duplicated, or refactor'),
    # Verbose variable names
    (r'\b[a-zA-Z]{30,}\s*[=:]', 'MEDIUM',
     'Overly verbose variable name',
     'Rename to shorter, meaningful name (max 20 chars) e.g., `userDatabase` instead of `userDatabaseDataSource`'),
    # Nested conditions (code complexity)
    (r'if\s*\([^)]*\s*if\s*\([^)]*', 'MEDIUM',
     'Nesting depth too high - consider early returns or extracting methods',
     'Extract inner condition to separate method or use guard clause'),
    # Magic numbers
    (r'=\s*-?\d{3,}', 'LOW',
     'Magic number detected - use named constant',
     'Replace with named constant: `val MAX_RETRIES = 3`'),
    # Empty catch blocks
    (r'catch\s*\([^)]*\)\s*\{\s*\}', 'MEDIUM',
     'Empty catch block - swallowing exceptions',
     'Add proper error handling: log exception, rethrow, or provide fallback'),
    # Unnecessary comments
    (r'//\s*[^a-zA-Z]*\s*(equals|gettersetter|constructor|this is|this method)', 'LOW',
     'Redundant comment - code is self-explanatory',
     'Remove: method names should be self-documenting'),
]

def detect_project_type(project_path: str) -> Tuple[str, int]:
    """Detect project type based on files present"""
    project_path = Path(project_path)
    
    if not project_path.exists():
        return 'unknown', 0
    
    best_type = 'unknown'
    best_score = 0
    
    for project_type, config in PROJECT_INDICATORS.items():
        score = 0
        
        # Check for files
        for file in config['files']:
            if (project_path / file).exists():
                score += 5
        
        # Check for directories
        for dir_pattern in config.get('dirs', []):
            if list(project_path.rglob(dir_pattern)):
                score += 3
        
        # Check for keywords in files
        for pattern in config.get('keywords', []):
            for ext in ['*.kt', '*.java', '*.js', '*.ts', '*.py', '*.go', '*.rs']:
                for file in list(project_path.rglob(ext))[:20]:  # Limit files for speed
                    try:
                        content = file.read_text().lower()
                        if pattern.lower() in content:
                            score += 1
                    except:
                        pass
        
        if score > best_score:
            best_type = project_type
            best_score = score
    
    return best_type, best_score

def scan_file(file_path: Path) -> List[Dict]:
    """Scan a single file for issues"""
    issues = []
    seen_lines = set()  # Track lines already reported for this file
    
    try:
        content = file_path.read_text()
        lines = content.split('\n')
    except:
        return issues
    
    # Try to detect language from file extension
    ext = file_path.suffix.lower()
    is_text_file = ext in ['.kt', '.java', '.js', '.ts', '.tsx', '.jsx', '.py', '.go', '.rs', '.gradle', '.kts']
    
    if not is_text_file:
        return issues
    
    # Check all pattern categories with fix suggestions
    for patterns in [SECURITY_PATTERNS, ARCHITECTURE_PATTERNS, AI_SLIP_PATTERNS]:
        for item in patterns:
            pattern = item[0]
            severity = item[1]
            name = item[2]
            fix = item[3]
            
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                for i, line in enumerate(lines, 1):
                    if regex.search(line):
                        # Skip if this line was already reported for a similar issue
                        line_key = (i, name)
                        if line_key in seen_lines:
                            continue
                        seen_lines.add(line_key)
                        
                        rel_path = str(file_path)
                        issues.append({
                            'rule_id': f'{file_path.stem}_{severity.lower()}_{len(issues)}',
                            'name': name,
                            'message': f"{name} in {file_path.name}",
                            'severity': severity,
                            'file': rel_path,
                            'line': i,
                            'column': 0,
                            'fix': fix
                        })
            except re.error:
                continue
    
    return issues

def scan_project(project_path: str, project_type: str) -> List[Dict]:
    """Scan all code files in project"""
    all_issues = []
    seen = set()  # Deduplication: track (file, line, name) tuples
    project_path = Path(project_path)
    
    # File extensions to scan by type
    ext_patterns = ['*.kt', '*.java', '*.js', '*.ts', '*.tsx', '*.jsx', '*.py', '*.go', '*.rs', 
                   'build.gradle*', 'build.gradle.kts', 'proguard*.pro', 'Dockerfile']
    
    for pattern in ext_patterns:
        for file in project_path.rglob(pattern):
            issues = scan_file(file)
            for issue in issues:
                key = (issue['file'], issue['line'], issue['name'])
                if key not in seen:
                    seen.add(key)
                    all_issues.append(issue)
    
    return all_issues

def check_unused_files(project_path: str, project_type: str) -> List[Dict]:
    """Check for unused files, assets, and dependencies"""
    unused = []
    project_path = Path(project_path)
    
    if project_type == 'android':
        # Check for unused drawables in drawable-* directories
        all_drawables = []
        for d in project_path.rglob('drawable-*'):
            if d.is_dir():
                all_drawables.extend(d.rglob('*.png'))
                all_drawables.extend(d.rglob('*.xml'))
        
        # Check for used drawables in XML/java/kotlin files
        used_refs = set()
        for ext in ['*.kt', '*.java', '*.xml']:
            for f in project_path.rglob(ext):
                try:
                    content = f.read_text()
                    refs = re.findall(r'@drawable/([a-zA-Z0-9_\.]+)', content)
                    used_refs.update(refs)
                except:
                    pass
        
        # Also check for resource names without underscores (Android naming)
        for drawable in all_drawables:
            name = drawable.stem
            if name not in used_refs and name.replace('.', '_') not in used_refs:
                unused.append({
                    'rule_id': 'unused_asset',
                    'name': 'Potentially unused drawable resource',
                    'message': f"Drawable {drawable.name} may not be referenced",
                    'severity': 'INFO',
                    'file': str(drawable),
                    'line': 0,
                    'column': 0,
                    'fix': f"Remove {drawable.name} or add @drawable/{name} reference in layouts"
                })
    
    elif project_type in ['react', 'vue', 'nodejs']:
        # Check for package.json
        if (project_path / 'package.json').exists():
            pass  # Would need depcheck for full analysis
    
    return unused

def analyze_complexity(project_path: str) -> Dict:
    """Analyze code complexity metrics"""
    project_path = Path(project_path)
    
    metrics = {
        'total_files': 0,
        'total_lines': 0,
        'avg_lines_per_file': 0,
        'quality_score': 85,
        'complexity_issues': 0
    }
    
    ext_patterns = ['*.kt', '*.java', '*.js', '*.ts', '*.tsx', '*.jsx', '*.py', '*.go', '*.rs']
    
    for pattern in ext_patterns:
        for file in project_path.rglob(pattern):
            metrics['total_files'] += 1
            try:
                content = file.read_text()
                lines = len(content.split('\n'))
                metrics['total_lines'] += lines
                metrics['complexity_issues'] += lines // 50  # Rough complexity estimate
            except:
                pass
    
    if metrics['total_files'] > 0:
        metrics['avg_lines_per_file'] = metrics['total_lines'] // metrics['total_files']
    
    # Adjust quality score based on findings
    metrics['quality_score'] -= min(metrics['complexity_issues'] // 10, 20)
    metrics['quality_score'] = max(0, min(100, metrics['quality_score']))
    
    return metrics

def generate_report(project_path: str, project_type: str, issues: List[Dict], metrics: Dict):
    """Generate comprehensive report with detailed fix suggestions"""
    project_path = Path(project_path)
    report_dir = project_path / '.coderabbit' / 'reports'
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Sort issues by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'WARNING': 2, 'MEDIUM': 3, 'LOW': 4, 'INFO': 5}
    issues.sort(key=lambda x: severity_order.get(x['severity'], 5))
    
    # Write JSON report with all details
    with open(report_dir / 'issues.json', 'w') as f:
        json.dump(issues, f, indent=2)
    
    # Write markdown report with fix suggestions
    with open(report_dir / 'summary.md', 'w') as f:
        f.write(f"# Coderabbit Deep Analysis Report\n\n")
        f.write(f"## Project Summary\n\n")
        f.write(f"- **Type:** {project_type}\n")
        f.write(f"- **Location:** {project_path}\n")
        f.write(f"- **Analysis Date:** {datetime.now().isoformat()}\n")
        f.write(f"- **Quality Score:** {metrics['quality_score']}/100\n\n")
        
        f.write(f"## Code Metrics\n\n")
        f.write(f"- **Total Files:** {metrics['total_files']}\n")
        f.write(f"- **Total Lines:** {metrics['total_lines']}\n")
        f.write(f"- **Avg Lines/File:** {metrics['avg_lines_per_file']}\n\n")
        
        f.write(f"## Issues Found\n\n")
        f.write(f"**{len(issues)} issues detected**\n\n")
        
        if issues:
            by_severity = defaultdict(list)
            for issue in issues:
                by_severity[issue['severity']].append(issue)
            
            for severity in ['CRITICAL', 'HIGH', 'WARNING', 'MEDIUM', 'LOW']:
                if by_severity.get(severity):
                    f.write(f"### {severity} Issues ({len(by_severity[severity])})\n\n")
                    for issue in by_severity[severity][:10]:  # Top 10 per severity
                        rel_path = str(Path(issue['file']).relative_to(project_path)) if Path(issue['file']).is_relative_to(project_path) else issue['file']
                        f.write(f"#### {issue['name']}\n\n")
                        f.write(f"```\n{rel_path}:{issue['line']}\n```\n\n")
                        if issue.get('fix'):
                            f.write(f"**Fix:** {issue['fix']}\n\n")
                    if len(by_severity[severity]) > 10:
                        f.write(f"\n*... and {len(by_severity[severity]) - 10} more*\n\n")
        else:
            f.write("No critical issues found. 🎉\n\n")
        
        f.write(f"## Fix Recommendations\n\n")
        f.write("### Critical Priority\n\n")
        f.write("1. **Review signing configuration for release builds**\n")
        f.write("2. **Verify ProGuard rules prevent class stripping**\n")
        f.write("3. **Check for hardcoded secrets** - move to secure storage\n\n")
        
        f.write("### Optimization Opportunities\n\n")
        f.write("1. **Code Duplication** - extract common logic to shared functions/classes\n")
        f.write("2. **Unused Imports/Assets** - remove to reduce APK/IPA size\n")
        f.write("3. **Consider code splitting** - lazy load features in React/Next.js\n\n")
        
        f.write("### Quality Improvements\n\n")
        f.write("1. **Add missing unit tests** - aim for 80%+ coverage\n")
        f.write("2. **Fix linter warnings** - improve code maintainability\n")
        f.write("3. **Remove AI slop** - verbose comments, redundant code, over-named variables\n\n")
        
        f.write(f"## Next Steps\n\n")
        f.write(f"Run `coderabbit fix` or manually apply the suggested fixes above.\n")
        f.write(f"After fixes, re-run `coderabbit review` to verify improvements.\n")

def generate_config(project_path: str, project_type: str):
    """Generate configuration files"""
    project_path = Path(project_path)
    config_dir = project_path / '.coderabbit'
    config_dir.mkdir(exist_ok=True)
    (config_dir / 'rules').mkdir(exist_ok=True)
    (config_dir / 'scripts').mkdir(exist_ok=True)
    (config_dir / 'reports').mkdir(exist_ok=True)
    
    # Determine language
    lang_map = {
        'android': 'kotlin',
        'react': 'typescript',
        'vue': 'typescript',
        'web_plain': 'javascript',
        'python': 'python',
        'node_api': 'javascript',
        'rust': 'rust',
        'go': 'go',
        'java': 'java'
    }
    language = lang_map.get(project_type, 'python')
    
    # Generate main config as YAML-like (simple format)
    config_content = f"""version: 1
language: {language}
project_type: {project_type}

reviews:
  profile: assertive
  auto_review: false
  deep_scan: true
  ai_enhancement: true
  optimization_suggestions: true
  unused_analysis: true
  quality_score: true

tools:
  semgrep: true
  custom_scanner: true

knowledge_base:
  guidelines: docs/coding-standards.md

analysis_config:
  ai_suggestions: true
  optimization_level: deep
  quality_threshold: 85
  ai_slop_detection: true
  unused_analysis: true
  code_reduction: true
  reuse_opportunities: true

project_specific:
  max_line_reduction: 15%
  duplicate_threshold: 0.3
  complexity_threshold: 10
"""
    
    with open(config_dir / 'coderabbit.yaml', 'w') as f:
        f.write(config_content)

def main():
    if len(sys.argv) < 2:
        print("Usage: smart_config.py <project_path>")
        print("       smart_config.py --detect-only <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    detect_only = '--detect-only' in sys.argv
    
    if not os.path.exists(project_path):
        print(f"Error: Project path does not exist: {project_path}")
        sys.exit(1)
    
    # Detect project type
    project_type, confidence = detect_project_type(project_path)
    print(f"Detected project type: {project_type}")
    print(f"Confidence: {confidence}")
    
    if project_type == 'unknown':
        print("\n⚠️ Could not determine project type")
        sys.exit(1)
    
    # Generate configuration
    if not detect_only:
        print("\n🔧 Generating configuration...")
        generate_config(project_path, project_type)
        
        print("🔍 Running deep scan...")
        issues = scan_project(project_path, project_type)
        unused = check_unused_files(project_path, project_type)
        issues.extend(unused)
        
        metrics = analyze_complexity(project_path)
        generate_report(project_path, project_type, issues, metrics)
        
        print(f"\n✅ Scan complete!")
        print(f"   Found {len(issues)} issues")
        print(f"   Quality score: {metrics['quality_score']}/100")
        print(f"   Report: {project_path}/.coderabbit/reports/summary.md")

if __name__ == "__main__":
    main()