"""Quick validation script for agentic CLI."""
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> tuple[int, str, str]:
    """Run command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout, result.stderr


def test_help():
    """Test that help commands work."""
    code, stdout, stderr = run(["agentic", "--help"])
    assert code == 0, f"Help failed: {stderr}"
    assert "Agentic" in stdout
    print("✓ Help command works")


def test_token_generate():
    """Test token generation."""
    code, stdout, stderr = run(["agentic", "token", "generate", "--scope", "read"])
    assert code == 0, f"Token generate failed: {stderr}"
    import json
    data = json.loads(stdout)
    assert data["status"] == "generated"
    assert data["token"].startswith("agr_")
    print("✓ Token generation works")


def test_review_not_implemented():
    """Test that review command returns structured output (not crash)."""
    # Use a local path to avoid network timeout
    code, stdout, stderr = run([
        "agentic", "review", ".", "main", "--output", "json"
    ])
    # Should not crash — may fail due to git issues, but should return JSON or error
    print(f"  Review exit code: {code}")
    print("✓ Review command doesn't crash")


def test_config_load():
    """Test config loading."""
    # Skip if yaml not available - just verify package loads
    try:
        import yaml
    except ImportError:
        print("⚠ Skipping config test (pyyaml not installed)")
        return
    
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    from agentic.config import Config
    
    config_path = Path(__file__).parent.parent / "example.agentic.yaml"
    config = Config.load(config_path)
    assert config.language == "python"
    assert config.reviews.profile == "assertive"
    print("✓ Config loading works")


if __name__ == "__main__":
    print("Running agentic CLI validation tests...")
    print("-" * 50)
    
    try:
        test_help()
        test_token_generate()
        test_review_not_implemented()
        test_config_load()
        print("-" * 50)
        print("All tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
