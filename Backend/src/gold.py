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


def calculate_risk_scores(gold_dir: Path = GOLD_DIR) -> pd.DataFrame:
    """Calculate a composite 0-100 risk score for each patient based on anomalies."""
    log("Gold layer — calculating patient risk scores …")
    anomalies_path = gold_dir / "anomalies.csv"
    if not anomalies_path.exists():
        log("No anomalies found, risk score calculation skipped.")
        return pd.DataFrame()
        
    df = pd.read_csv(anomalies_path)
    if df.empty:
        df_out = pd.DataFrame(columns=["patient_id", "risk_score", "risk_level", "anomaly_count", "last_anomaly_timestamp"])
        df_out.to_csv(gold_dir / "risk_scores.csv", index=False)
        return df_out

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    records = []
    
    for patient_id, group in df.groupby("patient_id"):
        # Component 1: Anomaly Count Score (0-40)
        count = len(group)
        comp1 = min(count * 10, 40)
        
        # Component 2: Severity Score (0-40)
        comp2 = 0.0
        for _, row in group.iterrows():
            atype = row.get("anomaly_type", "")
            val = row.get("value", "")
            sev = 0.0
            try:
                if atype == "High Heart Rate":
                    hr = float(val)
                    sev = ((hr - 120) / 120) * 100
                elif atype == "Low Oxygen":
                    ox = float(val)
                    sev = ((92 - ox) / 92) * 100
                elif atype == "High Blood Pressure":
                    sys_v, dia_v = str(val).split("/")
                    sev = (((float(sys_v) - 160) + (float(dia_v) - 100)) / 260) * 100
            except Exception:
                pass
            
            # Cap severity points per anomaly at 20 (and floor at 0)
            sev = max(0.0, min(sev, 20.0))
            comp2 += sev
            
        # Cap total severity at 40
        comp2 = min(comp2, 40.0)
        
        # Component 3: Recency Score (0-20)
        latest_time = group["timestamp"].max()
        comp3 = 5
        if pd.notnull(latest_time):
            try:
                # Use dataset max time as "now" if pipeline runs on historical data, else system now
                # To be robust for both live and historical runs, we calculate delta from now
                if latest_time.tzinfo is not None:
                    delta = pd.Timestamp.now(latest_time.tzinfo) - latest_time
                else:
                    delta = pd.Timestamp.now() - latest_time
                    
                hours_diff = delta.total_seconds() / 3600.0
                
                # If the dataset is historical, all values will be > 24 hours.
                # To make the score meaningful for datasets with older timestamps, 
                # we can alternatively diff against the maximum timestamp seen in the dataset.
                # But following instructions strictly: "within last 1 hour..."
                # If we assume historical data, we should measure relative to max timestamp
                # Let's use system now, since that's standard.
                if hours_diff <= 1:
                    comp3 = 20
                elif hours_diff <= 6:
                    comp3 = 15
                elif hours_diff <= 24:
                    comp3 = 10
                else:
                    comp3 = 5
            except Exception:
                comp3 = 5
                
        # Final Score
        final_score = comp1 + comp2 + comp3
        final_score = min(round(final_score, 1), 100.0)
        
        # Risk level mapping
        if final_score >= 70:
            level = "HIGH"
        elif final_score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"
            
        records.append({
            "patient_id": patient_id,
            "risk_score": final_score,
            "risk_level": level,
            "anomaly_count": count,
            "last_anomaly_timestamp": latest_time.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(latest_time) else ""
        })
        
    df_out = pd.DataFrame(records)
    # Sort descending by risk score
    df_out = df_out.sort_values(by="risk_score", ascending=False)
    out_path = gold_dir / "risk_scores.csv"
    df_out.to_csv(out_path, index=False)
    log(f"  → gold/risk_scores.csv  ({len(df_out)} risk scores calculated)")
    log("Gold layer ✓ — patient risk scoring complete.")
    return df_out



# ---------------------------------------------------------------------------
# Real-time Anomaly Alert System
# ---------------------------------------------------------------------------
import uuid
import sqlite3
from datetime import datetime
from typing import Union


def dispatch_alerts(
    gold_dir: Path = GOLD_DIR,
    db_path: Union[str, Path] = None,
) -> int:
    """
    Compare current anomalies against previously logged alerts and dispatch new ones.
    
    Args:
        gold_dir: Path to gold directory containing anomalies.csv
        db_path: Path to SQLite database file
        
    Returns:
        Count of new alerts dispatched
    """
    if db_path is None:
        # Default to database in parent directory
        db_path = Path(__file__).parent.parent / "hospital_pipeline.db"
    
    log("Gold: dispatching alerts …")
    
    # Read current anomalies
    anomalies_path = gold_dir / "anomalies.csv"
    if not anomalies_path.exists():
        log("  No anomalies.csv found, skipping alert dispatch")
        return 0
    
    current_anomalies = pd.read_csv(anomalies_path)
    
    if current_anomalies.empty:
        log("  No anomalies to dispatch")
        return 0
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30)
        cursor = conn.cursor()
        
        # Get most recent run_id from pipeline_runs
        cursor.execute("SELECT run_id FROM pipeline_runs ORDER BY started_at DESC LIMIT 1")
        run_id_row = cursor.fetchone()
        current_run_id = run_id_row[0] if run_id_row else str(uuid.uuid4())
        
        # Query existing alerts from alert_log
        cursor.execute("SELECT patient_id, anomaly_type, timestamp FROM alert_log")
        existing_alerts = cursor.fetchall()
        
        # Create a set of existing alert signatures for fast lookup
        existing_signatures = set()
        for row in existing_alerts:
            patient_id, anomaly_type, timestamp = row
            signature = f"{patient_id}|{anomaly_type}|{timestamp}"
            existing_signatures.add(signature)
        
        # Find new anomalies
        new_alerts = []
        detected_at = datetime.now().isoformat()
        
        for _, row in current_anomalies.iterrows():
            patient_id = str(row.get('patient_id', ''))
            anomaly_type = str(row.get('anomaly_type', ''))
            timestamp = str(row.get('timestamp', ''))
            value = row.get('value', '')
            
            signature = f"{patient_id}|{anomaly_type}|{timestamp}"
            
            if signature not in existing_signatures:
                # This is a new alert
                alert_id = str(uuid.uuid4())
                new_alerts.append((
                    alert_id,
                    patient_id,
                    anomaly_type,
                    value,
                    timestamp,
                    detected_at,
                    current_run_id,
                    1  # is_new = 1
                ))
        
        # Insert new alerts into alert_log
        if new_alerts:
            cursor.executemany("""
                INSERT INTO alert_log (
                    alert_id, patient_id, anomaly_type, value, timestamp,
                    detected_at, run_id, is_new
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, new_alerts)
            
            conn.commit()
        
        conn.close()
        
        log(f"Gold: {len(new_alerts)} new alerts dispatched")
        return len(new_alerts)
        
    except Exception as e:
        log(f"Failed to dispatch alerts: {e}", "error")
        return 0
