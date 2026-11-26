#!/usr/bin/env python3
"""
Android Build Configuration Validator for Agentic OS
This script validates build.gradle.kts, proguard-rules.pro, and signing configuration
to catch issues that standard static analysis might miss.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

class BuildConfigValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "android-app" / "app"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def check_signing_config(self) -> bool:
        """Check if signing configurations are properly defined"""
        build_gradle = self.app_dir / "build.gradle.kts"
        
        if not build_gradle.exists():
            self.errors.append("build.gradle.kts not found")
            return False
            
        content = build_gradle.read_text()
        
        # Check for signingConfigs block
        if "signingConfigs" not in content:
            self.errors.append("CRITICAL: No signingConfigs block found")
            return False
            
        # Check for release signing config
        if 'create("release")' not in content and 'create("release")' not in content:
            self.errors.append("CRITICAL: Release signing config not defined")
            
        # Check for signing config assignment in release build type
        if 'signingConfig = signingConfigs.getByName("release")' not in content and \
           'signingConfig = signingConfigs.getByName("release")' not in content:
            self.errors.append("CRITICAL: Release build type not using signing config")
            
        # Check for keystore file reference
        if 'release.keystore' not in content:
            self.warnings.append("WARNING: release.keystore not referenced in signing config")
            
        # Check for keystore file existence
        keystore_path = self.app_dir / "release.keystore"
        if not keystore_path.exists():
            self.errors.append(f"CRITICAL: Keystore file not found: {keystore_path}")
            
        return len(self.errors) == 0
    
    def check_proguard_rules(self) -> bool:
        """Check if ProGuard rules are properly configured"""
        proguard_file = self.app_dir / "proguard-rules.pro"
        
        if not proguard_file.exists():
            self.errors.append("CRITICAL: proguard-rules.pro not found")
            return False
            
        content = proguard_file.read_text()
        
        # Required keeps for Android Room + Hilt + Serialize
        required_patterns = [
            (r'dagger\.hilt\.\*\*', "Hilt dependency injection"),
            (r'androidx\.room\.\*\*', "Room database"),
            (r'kotlinx\.serialization\.\*\*', "kotlinx serialization"),
            (r'net\.zetetic\.\*\*', "SQLCipher"),
            (r'retrofit2\.\*\*', "Retrofit"),
            (r'okhttp3\.\*\*', "OkHttp"),
            (r'androidx\.work\.\*\*', "WorkManager"),
        ]
        
        for pattern, description in required_patterns:
            if not re.search(pattern, content):
                self.warnings.append(f"WARNING: Missing ProGuard rules for {description}")
                
        # Check for dontwarn directives
        if 'dontwarn' not in content:
            self.warnings.append("WARNING: No -dontwarn directives found - may cause build warnings")
            
        return True
    
    def check_build_type_config(self) -> bool:
        """Check build type configuration"""
        build_gradle = self.app_dir / "build.gradle.kts"
        
        if not build_gradle.exists():
            return False
            
        content = build_gradle.read_text()
        
        # Check minify settings
        if 'isMinifyEnabled = true' in content:
            self.warnings.append("WARNING: Minification enabled - ensure ProGuard rules are complete")
            
        # Check resource shrinking
        if 'isShrinkResources = true' in content:
            self.warnings.append("WARNING: Resource shrinking enabled - may cause issues if rules incomplete")
            
        # Check that both debug and release have configs
        if 'buildTypes {' in content:
            build_types = content[content.find('buildTypes'):]
            if '"release"' not in build_types:
                self.errors.append("CRITICAL: Release build type not defined")
            if '"debug"' not in build_types:
                self.warnings.append("WARNING: Debug build type not explicitly defined")
                
        return True
    
    def check_android_manifest(self) -> bool:
        """Check AndroidManifest.xml for required permissions"""
        manifest_file = self.app_dir / "src" / "main" / "AndroidManifest.xml"
        
        if not manifest_file.exists():
            self.errors.append("AndroidManifest.xml not found")
            return False
            
        content = manifest_file.read_text()
        
        # Check for POST_NOTIFICATIONS (required for Android 13+)
        if 'POST_NOTIFICATIONS' not in content:
            self.warnings.append("WARNING: POST_NOTIFICATIONS permission not declared")
            
        # Check for FOREGROUND_SERVICE
        if 'FOREGROUND_SERVICE' not in content:
            self.warnings.append("WARNING: FOREGROUND_SERVICE permission not declared")
            
        return True
    
    def check_database_encryption(self) -> bool:
        """Check if database encryption is properly configured"""
        database_file = self.app_dir / "src" / "main" / "java" / "com" / "agenticos" / "agent" / "data" / "Database.kt"
        
        if not database_file.exists():
            self.errors.append("Database.kt not found")
            return False
            
        content = database_file.read_text()
        
        # Check for SQLCipher
        if 'SupportFactory' in content or 'sqlcipher' in content.lower():
            # Check for passphrase
            if 'PASSPHRASE' not in content and 'passphrase' not in content:
                self.errors.append("CRITICAL: SQLCipher enabled but no passphrase defined")
            else:
                self.warnings.append("INFO: SQLCipher encryption enabled")
                
        # Check for fallbackToDestructiveMigration
        if 'fallbackToDestructiveMigration' not in content:
            self.warnings.append("WARNING: No fallbackToDestructiveMigration - may fail on schema changes")
            
        return True
    
    def validate(self) -> Dict:
        """Run all checks and return results"""
        print("=" * 60)
        print("Android Build Configuration Validator")
        print("=" * 60)
        print()
        
        self.check_signing_config()
        self.check_proguard_rules()
        self.check_build_type_config()
        self.check_android_manifest()
        self.check_database_encryption()
        
        result = {
            "errors": self.errors,
            "warnings": self.warnings,
            "valid": len(self.errors) == 0
        }
        
        # Print results
        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")
            print()
            
        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()
            
        if result["valid"]:
            print("✅ Build configuration is valid")
        else:
            print("❌ Build configuration has errors that will cause release build failures")
            
        return result

def main():
    # Find project root
    project_root = os.environ.get('PROJECT_ROOT', '/Users/gouthamsai/opencode_1/Agentic_OS')
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    
    validator = BuildConfigValidator(project_root)
    result = validator.validate()
    
    # Exit with error code if validation failed
    sys.exit(0 if result["valid"] else 1)

if __name__ == "__main__":
    main()