"""
Bronze Layer — Raw Data Ingestion.

Reads source files from the ``data/`` directory and writes exact raw copies
as CSV files into ``bronze/``.  No transformations are applied.

Input files:
    data/ehr.csv       (CSV)
    data/vitals.json   (JSONL)
    data/labs.json     (JSONL)

Output files:
    bronze/ehr.csv
    bronze/vitals.csv
    bronze/labs.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.utils import (
    BRONZE_DIR,
    DATA_DIR,
    log,
    validate_file_exists,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> pd.DataFrame:
    """Read a JSON-Lines file into a DataFrame, one JSON object per line."""
    records: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue  # skip blank lines
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                log(
                    f"Skipping malformed JSON on line {lineno} of {path.name}: {exc}",
                    level="warning",
                )
    if not records:
        raise ValueError(f"No valid records found in {path}")
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest(data_dir: Path = DATA_DIR, bronze_dir: Path = BRONZE_DIR) -> None:
    """Ingest raw data files and write them as CSVs to the bronze layer.

    Raises
    ------
    FileNotFoundError
        If any expected input file is missing.
    ValueError
        If a JSONL file contains zero valid records.
    """
    log("Bronze layer — starting raw ingestion …")

    # --- EHR (already CSV) -------------------------------------------------
    ehr_path = validate_file_exists(data_dir / "ehr.csv", "EHR data file")
    ehr_df = pd.read_csv(ehr_path)
    if ehr_df.empty:
        raise ValueError("ehr.csv is empty — nothing to ingest.")
    ehr_df.to_csv(bronze_dir / "ehr.csv", index=False)
    log(f"  → bronze/ehr.csv  ({len(ehr_df)} rows)")

    # --- Vitals (JSONL) ----------------------------------------------------
    vitals_path = validate_file_exists(data_dir / "vitals.json", "Vitals data file")
    vitals_df = _read_jsonl(vitals_path)
    vitals_df.to_csv(bronze_dir / "vitals.csv", index=False)
    log(f"  → bronze/vitals.csv  ({len(vitals_df)} rows)")

    # --- Labs (JSONL) ------------------------------------------------------
    labs_path = validate_file_exists(data_dir / "labs.json", "Labs data file")
    labs_df = _read_jsonl(labs_path)
    labs_df.to_csv(bronze_dir / "labs.csv", index=False)
    log(f"  → bronze/labs.csv  ({len(labs_df)} rows)")

    log("Bronze layer ✓ — raw ingestion complete.")
