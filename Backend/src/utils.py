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


# ---------------------------------------------------------------------------
# Pipeline Run Logging
# ---------------------------------------------------------------------------
import uuid
import sqlite3
from datetime import datetime


def start_run_log() -> dict:
    """
    Initialize a pipeline run log dictionary.
    
    Returns:
        Dictionary with run metadata and counters initialized to 0
    """
    return {
        "run_id": str(uuid.uuid4()),
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "duration_seconds": None,
        "bronze_ehr_count": 0,
        "bronze_vitals_count": 0,
        "bronze_labs_count": 0,
        "silver_vitals_count": 0,
        "silver_labs_count": 0,
        "silver_patient_master_count": 0,
        "gold_anomalies_count": 0,
        "gold_risk_scores_count": 0,
        "silver_trends_count": 0,
        "new_alerts_count": 0,
        "status": "RUNNING"
    }


def finish_run_log(run_log: dict, db_path: Union[str, Path]) -> None:
    """
    Complete the pipeline run log and write it to the database.
    
    Args:
        run_log: Dictionary containing run metadata and counts
        db_path: Path to SQLite database file
    """
    # Calculate finish time and duration
    run_log["finished_at"] = datetime.now().isoformat()
    
    started = datetime.fromisoformat(run_log["started_at"])
    finished = datetime.fromisoformat(run_log["finished_at"])
    duration = (finished - started).total_seconds()
    run_log["duration_seconds"] = round(duration, 2)
    
    # Set status to SUCCESS
    run_log["status"] = "SUCCESS"
    
    # Write to database
    try:
        conn = sqlite3.connect(str(db_path), timeout=30)
        cursor = conn.cursor()
        
        # Insert the run log
        cursor.execute("""
            INSERT INTO pipeline_runs (
                run_id, started_at, finished_at, duration_seconds,
                bronze_ehr_count, bronze_vitals_count, bronze_labs_count,
                silver_vitals_count, silver_labs_count, silver_patient_master_count,
                gold_anomalies_count, gold_risk_scores_count, silver_trends_count,
                new_alerts_count, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_log["run_id"],
            run_log["started_at"],
            run_log["finished_at"],
            run_log["duration_seconds"],
            run_log["bronze_ehr_count"],
            run_log["bronze_vitals_count"],
            run_log["bronze_labs_count"],
            run_log["silver_vitals_count"],
            run_log["silver_labs_count"],
            run_log["silver_patient_master_count"],
            run_log["gold_anomalies_count"],
            run_log["gold_risk_scores_count"],
            run_log["silver_trends_count"],
            run_log["new_alerts_count"],
            run_log["status"]
        ))
        
        conn.commit()
        conn.close()
        
        log(f"Pipeline run logged — run_id: {run_log['run_id']}, duration: {run_log['duration_seconds']}s")
        
    except Exception as e:
        log(f"Failed to log pipeline run: {e}", "error")
        raise
