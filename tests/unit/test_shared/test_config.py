import pytest
from pathlib import Path
from palace.shared.config import PalaceConfig

def test_default_config():
    config = PalaceConfig()
    assert config.palace_dir == Path(".palace")
    assert config.repo_root == Path(".")
    assert "node_modules" in config.ignore_patterns
    assert config.embedding_model == "all-MiniLM-L6-v2"
    assert config.embedding_dim == 384
    assert config.default_max_depth == 3
    assert config.default_energy_threshold == 0.3

def test_config_from_env(monkeypatch):
    monkeypatch.setenv("PALACE_PALACE_DIR", "/tmp/test_palace")
    monkeypatch.setenv("PALACE_EMBEDDING_MODEL", "multi-qa-mpnet-base-dot-v1")
    config = PalaceConfig()
    assert config.palace_dir == Path("/tmp/test_palace")
    assert config.embedding_model == "multi-qa-mpnet-base-dot-v1"

def test_validation():
    config = PalaceConfig()
    assert 0.0 <= config.default_energy_threshold <= 1.0
    assert 0.0 <= config.default_lambda_decay <= 1.0
