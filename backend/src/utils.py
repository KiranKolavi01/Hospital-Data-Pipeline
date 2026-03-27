"""
Shared utilities for the Hospital Data Pipeline.

Provides:
- Directory path constants (DATA_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, VIZ_DIR)
- setup_directories()  — idempotent folder creation
- log()                — timestamped console logging
- safe_to_numeric()    — pandas numeric coercion with NaN fallback
- unix_to_datetime()   — UNIX epoch → pandas Timestamp conversion
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

import pandas as pd

# ---------------------------------------------------------------------------
# Directory layout (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # one level above src/

DATA_DIR: Path = PROJECT_ROOT / "data"
BRONZE_DIR: Path = PROJECT_ROOT / "bronze"
SILVER_DIR: Path = PROJECT_ROOT / "silver"
GOLD_DIR: Path = PROJECT_ROOT / "gold"
VIZ_DIR: Path = PROJECT_ROOT / "visualizations"

ALL_DIRS: list[Path] = [DATA_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, VIZ_DIR]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")


def log(message: str, level: str = "info") -> None:
    """Print a timestamped log message to the console."""
    getattr(logger, level.lower(), logger.info)(message)


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------
def setup_directories() -> None:
    """Create every required directory if it does not already exist."""
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    log("Setup complete — all directories verified.")


# ---------------------------------------------------------------------------
# Data conversion helpers
# ---------------------------------------------------------------------------
def safe_to_numeric(series: pd.Series) -> pd.Series:
    """Convert a pandas Series to numeric, coercing errors to NaN."""
    return pd.to_numeric(series, errors="coerce")


def unix_to_datetime(series: pd.Series) -> pd.Series:
    """Convert a Series of UNIX timestamps (seconds) to pandas datetime."""
    numeric = safe_to_numeric(series)
    return pd.to_datetime(numeric, unit="s", errors="coerce")


def validate_file_exists(path: Union[str, Path], label: str = "File") -> Path:
    """Raise FileNotFoundError with a clear message if *path* is missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{label} not found: {p}")
    return p
