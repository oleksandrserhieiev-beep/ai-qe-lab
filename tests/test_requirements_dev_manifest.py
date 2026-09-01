from pathlib import Path


def test_requirements_dev_includes_pytest():
    content = Path("requirements-dev.txt").read_text(encoding="utf-8")
    assert "-r requirements.txt" in content
    assert "pytest==" in content
