"""Configuration management for Palacio Mental."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List


class PalaceConfig(BaseSettings):
    """Configuration loaded from env vars and .palace/config.toml"""

    # Paths
    palace_dir: Path = Path(".palace")
    repo_root: Path = Path(".")

    # Ingestion
    ignore_patterns: List[str] = [
        "node_modules",
        ".git",
        "__pycache__",
        "*.log",
        "dist",
        "build",
        ".venv",
        "venv",
        ".eggs",
        "*.egg-info",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".palace"
    ]
    max_file_size_mb: int = 10

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Activation
    default_max_depth: int = 3
    default_energy_threshold: float = 0.3
    default_decay_factor: float = 0.8

    # Sleep
    default_lambda_decay: float = 0.05
    default_prune_threshold: float = 0.1
    auto_sleep_after_ingest: bool = False

    # Performance
    db_connection_pool_size: int = 4
    batch_size: int = 100

    model_config = SettingsConfigDict(
        env_prefix="PALACE_",
        env_file=".palace/.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
