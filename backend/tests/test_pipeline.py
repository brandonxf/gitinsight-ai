"""Tests del pipeline determinista sobre un repo de muestra en disco."""
from pathlib import Path

import pytest

from app.analyzers import build_context, run_pipeline

SAMPLE_APP = '''\
import os
import subprocess

API_KEY = "AKIAIOSFODNN7EXAMPLE"

def run(cmd):
    return subprocess.call(cmd, shell=True)
'''


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["fastapi", "sqlalchemy"]\n'
    )
    (tmp_path / "app.py").write_text(SAMPLE_APP)
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.py").write_text("x = 1\n")
    return tmp_path


def test_build_context_ignores_node_modules(sample_repo: Path):
    ctx = build_context(sample_repo)
    rel = {f.rel_path for f in ctx.files}
    assert "app.py" in rel
    assert "pyproject.toml" in rel
    assert not any("node_modules" in p for p in rel)


def test_pipeline_detects_tech_and_findings(sample_repo: Path):
    out = run_pipeline(build_context(sample_repo))

    assert out.data["primary_language"] == "Python"
    assert "FastAPI" in out.data["frameworks"]
    assert "SQLAlchemy" in out.data["frameworks"]

    categories = {f.category for f in out.findings}
    assert "secret" in categories  # AWS key detectada

    agg = out.data["aggregate"]
    assert agg["risk_level"] == "high"  # hay un secreto
    assert 0 <= agg["quality_score"] <= 100


def test_secret_scan_detects_aws_key(sample_repo: Path):
    out = run_pipeline(build_context(sample_repo))
    secrets = [f for f in out.findings if f.category == "secret"]
    assert any(f.rule_id == "AWS_ACCESS_KEY" for f in secrets)
    assert all(f.file_path == "app.py" for f in secrets)
