"""
Gold Layer — Anomaly Detection.

Reads cleaned vitals from ``silver/clean_vitals.csv`` and flags rows that
breach clinical thresholds:

    • High Heart Rate : hr  > 120  bpm
    • Low Oxygen      : ox  < 92   %
    • High Blood Pressure : sys > 160  OR  dia > 100  mmHg

Output: ``gold/anomalies.csv``
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import (
    GOLD_DIR,
    SILVER_DIR,
    log,
    validate_file_exists,
)

# ---------------------------------------------------------------------------
# Threshold constants (easy to adjust)
# ---------------------------------------------------------------------------
HR_HIGH: int = 120       # bpm
OX_LOW: int = 92         # %
SYS_HIGH: int = 160      # mmHg
DIA_HIGH: int = 100      # mmHg


def _collect_anomalies(
    df: pd.DataFrame,
    mask: pd.Series,
    anomaly_type: str,
    value_col: str,
) -> list[dict[str, Any]]:
    """Return a list of anomaly dicts for rows matching *mask*."""
    flagged = df.loc[mask].copy()
    records: list[dict[str, Any]] = []
    for _, row in flagged.iterrows():
        records.append(
            {
                "patient_id": row.get("patient_id", ""),
                "timestamp": row.get("timestamp", ""),
                "anomaly_type": anomaly_type,
                "value": row.get(value_col, ""),
            }
        )
    return records


def detect_anomalies(
    silver_dir: Path = SILVER_DIR,
    gold_dir: Path = GOLD_DIR,
) -> pd.DataFrame:
    """Scan cleaned vitals for clinical anomalies and write results to CSV.

    Returns
    -------
    pd.DataFrame
        A frame with columns ``patient_id``, ``timestamp``,
        ``anomaly_type``, ``value``.
    """
    log("Gold layer — running anomaly detection …")

    src = validate_file_exists(silver_dir / "clean_vitals.csv", "Clean vitals")
    df = pd.read_csv(src)

    # Ensure columns are numeric for comparisons
    for col in ("hr", "ox", "sys", "dia"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    anomalies: list[dict[str, Any]] = []

    # 1. High Heart Rate
    if "hr" in df.columns:
        mask_hr = df["hr"] > HR_HIGH
        anomalies.extend(_collect_anomalies(df, mask_hr, "High Heart Rate", "hr"))
        log(f"  • High Heart Rate (>{HR_HIGH} bpm): {mask_hr.sum()} flags")

    # 2. Low Oxygen
    if "ox" in df.columns:
        mask_ox = df["ox"] < OX_LOW
        anomalies.extend(_collect_anomalies(df, mask_ox, "Low Oxygen", "ox"))
        log(f"  • Low Oxygen (<{OX_LOW}%): {mask_ox.sum()} flags")

    # 3. High Blood Pressure
    sys_high = df["sys"] > SYS_HIGH if "sys" in df.columns else pd.Series(False, index=df.index)
    dia_high = df["dia"] > DIA_HIGH if "dia" in df.columns else pd.Series(False, index=df.index)
    mask_bp = sys_high | dia_high
    if mask_bp.any():
        # Use the systolic value as the reported value (or diastolic if sys is missing)
        val_col = "sys" if "sys" in df.columns else "dia"
        for _, row in df.loc[mask_bp].iterrows():
            anomalies.append(
                {
                    "patient_id": row.get("patient_id", ""),
                    "timestamp": row.get("timestamp", ""),
                    "anomaly_type": "High Blood Pressure",
                    "value": f"{row.get('sys', '')}/{row.get('dia', '')}",
                }
            )
    log(f"  • High Blood Pressure (SYS>{SYS_HIGH} or DIA>{DIA_HIGH}): {mask_bp.sum()} flags")

    result = pd.DataFrame(anomalies)
    out_path = gold_dir / "anomalies.csv"
    result.to_csv(out_path, index=False)
    log(f"  → gold/anomalies.csv  ({len(result)} total anomalies)")
    log("Gold layer ✓ — anomaly detection complete.")
    return result
