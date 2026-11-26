# Coderabbit Configuration Guide for Agentic OS

## Overview
This guide explains how to configure Coderabbit to catch build, security, and architecture issues that standard static analysis might miss.

## Why Standard Coderabbit Misses These Issues

### 1. Build Configuration Blind Spots
- **Build files are not analyzed** - `.gradle.kts` files are often excluded
- **Release-only issues** - Debug builds work fine; problems appear only in release
- **Configuration is not code** - ProGuard rules, signing configs, manifest entries
- **Environment-specific** - Keystore paths, SDK versions

### 2. Release Build Crashes
- **ProGuard R8 stripping** - Classes removed during minification
- **Resource shrinking** - Essential files removed
- **Native library loading** - SQLCipher, MediaPipe libs

## Key Patterns to Add to Coderabbit Configuration

### Critical: Release Build Failures
```json
{
  "release_crash_patterns": [
    {
      "pattern": "isMinifyEnabled\\s*=\\s*true(?!.*Proguard)",
      "severity": "CRITICAL",
      "message": "Release minification enabled without ProGuard rules verification"
    },
    {
      "pattern": "isShrinkResources\\s*=\\s*true",
      "severity": "HIGH",
      "message": "Resource shrinking enabled - verify resources are kept"
    },
    {
      "pattern": "signingConfig.*not.*defined|missing.*signing.*release",
      "severity": "CRITICAL",
      "message": "Release build missing signing configuration"
    }
  ]
}
```

### Security: Hardcoded Secrets
```json
{
  "secret_patterns": [
    {
      "pattern": "storePassword\\s*=\\s*[\"'][^\"']+[\"']",
      "severity": "HIGH",
      "message": "Hardcoded keystore password"
    },
    {
      "pattern": "PASSPHRASE\\s*=\\s*[\"'][^\"']+[\"']",
      "severity": "HIGH",
      "message": "Hardcoded database passphrase"
    },
    {
      "pattern": "API_KEY|SECRET_KEY.*=.*[\"'][^\"']{10,}[\"']",
      "severity": "MEDIUM",
      "message": "Potential hardcoded API key"
    }
  ]
}
```

### Architecture: Thread Safety
```json
{
  "thread_safety_patterns": [
    {
      "pattern": "@Volatile.*private.*var INSTANCE",
      "negative": true,
      "severity": "CRITICAL",
      "message": "Database singleton not thread-safe - missing @Volatile"
    },
    {
      "pattern": "initialized.*=\\s*null.*unregisterReceiver.*!!",
      "severity": "CRITICAL",
      "message": "BroadcastReceiver NPE risk - unregister without null check"
    }
  ]
}
```

## Integration with CI/CD

### GitHub Actions Workflow
```yaml
name: Code Review

on: [push, pull_request]

jobs:
  coderabbit-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install dependencies
        run: |
          pip install hermes_tools
          pip install -r requirements.txt || true
          
      - name: Validate build configuration
        run: python3 .coderabbit/validate_build.py
        
      - name: Run enhanced code review
        uses: coderabbitai/coderabbit-action@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          config_file: .coderabbit/config.json
          include_build_files: true
          severity: detailed
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running build validation..."
python3 .coderabbit/validate_build.py
if [ $? -ne 0 ]; then
  echo "Build validation failed - commit rejected"
  exit 1
fi

echo "Running code quality checks..."
coderabbit review . --config .coderabbit/config.json
```

## Running the Validation

### Manual Validation
```bash
# Run build configuration validator
python3 .coderabbit/validate_build.py

# Run ProGuard rules checker
python3 .coderabbit/check_proguard.py

# ManualCoderabbit analysis
coderabbit review . \
  --config .coderabbit/config.json \
  --include-build-files \
  --include-proguard-rules \
  --output json > review-report.json
```

### Docker-based Validation
```dockerfile
FROM python:3.11-slim

RUN pip install hermes_tools

WORKDIR /app
COPY .coderabbit/ /app/.coderabbit/
COPY android-app/app/build.gradle.kts /app/
COPY android-app/app/proguard-rules.pro /app/

CMD ["python3", "/app/.coderabbit/validate_build.py"]
```

## Key Files to Monitor

| File | What to Check | Common Issues |
|------|---------------|---------------|
| `build.gradle.kts` | Signing configs, minify settings | Missing release signing, minify enabled |
| `proguard-rules.pro` | Keep rules for Hilt/Room/Serialize | Missing @Entity, @Dao, Hilt classes |
| `AndroidManifest.xml` | Permissions, services | Missing POST_NOTIFICATIONS, exported issues |
| `gradle.properties` | SDK versions, JVM args | Hardcoded paths, missing versions |
| `Database.kt` | Singleton pattern, encryption | Missing @Volatile, no passphrase fallback |

## Best Practices to Add to Rules

### 1. Always verify keystore exists for release
```
pattern: "release\\.keystore" needs filesystem check
```

### 2. ProGuard rules must match Room entities
```
pattern: "@Entity" requires "keep @room.Entity class ** { *; }"
pattern: "@Dao" requires "keep @room.Dao class ** { *; }"
```

### 3. Hilt dependency injection must be preserved
```
pattern: "HiltAndroidApp" requires full dagger.hilt.** rules
```

### 4. SQLCipher requires special handling
```
pattern: "net.zetetic:android-database-sqlcipher" requires:
  - loadLibs() in Application.onCreate()
  - SupportFactory with passphrase
  - Fallback for upgrade from plain SQLite
```

## Common False Negatives

### What Standard Review Misses:
1. **Release build won't compile** - Debug builds work fine
2. **Classes stripped at runtime** - Present in debug, gone in release
3. **Native library issues** - SQLCipher, MediaPipe libs
4. **Exact alarm permission** - Required on Android 12+
5. **Scoped storage issues** - Android 11+ changes
6. **Foreground service types** - Android 9+ requirements
7. **Notification permission** - Android 13+ runtime permission

## Adding New Patterns

When you discover a new issue:

1. **Add to config.json**:
```json
{
  "pattern": "your_regex_pattern",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "message": "Description of the issue",
  "file_types": ["gradle", "kt", "pro"]
}
```

2. **Add to validation script**:
```python
def check_your_pattern(self) -> bool:
    # Pattern-specific checks
    pass
```

3. **Document in this guide**
4. **Test with example file**

## Verification Checklist

Before release, verify:
- [ ] Keystore exists and is valid
- [ ] Signing config matches keystore
- [ ] ProGuard rules cover all used classes
- [ ] Build variant configuration correct
- [ ] Dependencies with native libs included
- [ ] Thread-safe singletons
- [ ] No hardcoded secrets
- [ ] Required permissions declared
- [ ] Notification channels configured