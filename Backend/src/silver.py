"""
Silver Layer — Data Cleaning & Standardization.

Reads CSVs from ``bronze/``, applies cleaning rules (column renames, type
coercions, timestamp conversions), and produces:

    silver/clean_vitals.csv
    silver/clean_labs.csv
    silver/patient_master.csv

The patient-master table joins EHR demographics with the *latest* vitals
reading and the *latest* result per lab test for each patient.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import (
    BRONZE_DIR,
    SILVER_DIR,
    log,
    safe_to_numeric,
    unix_to_datetime,
    validate_file_exists,
)


# ======================================================================== #
# 1. Clean Vitals                                                          #
# ======================================================================== #

def clean_vitals(
    bronze_dir: Path = BRONZE_DIR,
    silver_dir: Path = SILVER_DIR,
) -> pd.DataFrame:
    """Rename columns, convert timestamps, coerce vital-sign values."""

    log("Silver layer — cleaning vitals …")
    src = validate_file_exists(bronze_dir / "vitals.csv", "Bronze vitals")
    df = pd.read_csv(src)

    # Column renames
    if "patientId" in df.columns:
        df.rename(columns={"patientId": "patient_id"}, inplace=True)

    # Timestamp conversion
    if "timestamp" in df.columns:
        df["timestamp"] = unix_to_datetime(df["timestamp"])

    # Numeric coercion for vital-sign columns
    for col in ("hr", "ox", "sys", "dia"):
        if col in df.columns:
            df[col] = safe_to_numeric(df[col])

    out_path = silver_dir / "clean_vitals.csv"
    df.to_csv(out_path, index=False)
    log(f"  → silver/clean_vitals.csv  ({len(df)} rows)")
    return df


# ======================================================================== #
# 2. Clean Labs                                                            #
# ======================================================================== #

def clean_labs(
    bronze_dir: Path = BRONZE_DIR,
    silver_dir: Path = SILVER_DIR,
) -> pd.DataFrame:
    """Rename columns, convert timestamps, coerce lab values."""

    log("Silver layer — cleaning labs …")
    src = validate_file_exists(bronze_dir / "labs.csv", "Bronze labs")
    df = pd.read_csv(src)

    # Column renames
    rename_map: dict[str, str] = {}
    if "patientId" in df.columns:
        rename_map["patientId"] = "patient_id"
    if "test" in df.columns:
        rename_map["test"] = "lab_test"
    if "value" in df.columns:
        rename_map["value"] = "lab_value"
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # Timestamp conversion
    if "timestamp" in df.columns:
        df["timestamp"] = unix_to_datetime(df["timestamp"])

    # Numeric coercion
    if "lab_value" in df.columns:
        df["lab_value"] = safe_to_numeric(df["lab_value"])

    out_path = silver_dir / "clean_labs.csv"
    df.to_csv(out_path, index=False)
    log(f"  → silver/clean_labs.csv  ({len(df)} rows)")
    return df


# ======================================================================== #
# 3. Patient Master Table                                                  #
# ======================================================================== #

def _latest_vitals(vitals_df: pd.DataFrame) -> pd.DataFrame:
    """Return the single most-recent vitals row per patient."""
    if vitals_df.empty:
        return vitals_df
    df = vitals_df.sort_values("timestamp")
    latest = df.groupby("patient_id", as_index=False).last()
    # Keep only the vital-sign columns we care about
    keep = [c for c in ("patient_id", "hr", "ox", "sys", "dia") if c in latest.columns]
    return latest[keep]


def _latest_labs(labs_df: pd.DataFrame) -> pd.DataFrame:
    """Return the latest result per (patient, lab_test), then pivot wide."""
    if labs_df.empty:
        return labs_df
    df = labs_df.sort_values("timestamp")
    latest = df.groupby(["patient_id", "lab_test"], as_index=False).last()
    # Pivot so each lab_test becomes its own column
    pivot = latest.pivot_table(
        index="patient_id",
        columns="lab_test",
        values="lab_value",
        aggfunc="first",  # already deduplicated
    )
    pivot.columns = [f"lab_{c}" for c in pivot.columns]
    return pivot.reset_index()


def build_patient_master(
    bronze_dir: Path = BRONZE_DIR,
    silver_dir: Path = SILVER_DIR,
) -> pd.DataFrame:
    """Merge EHR demographics with latest vitals and labs into one table."""

    log("Silver layer — building patient master …")

    ehr_path = validate_file_exists(bronze_dir / "ehr.csv", "Bronze EHR")
    ehr_df = pd.read_csv(ehr_path)

    # Read the *already-cleaned* silver files
    vitals_path = silver_dir / "clean_vitals.csv"
    labs_path = silver_dir / "clean_labs.csv"

    vitals_df = pd.read_csv(vitals_path) if vitals_path.exists() else pd.DataFrame()
    labs_df = pd.read_csv(labs_path) if labs_path.exists() else pd.DataFrame()

    # Ensure timestamp is parsed for sorting
    if not vitals_df.empty and "timestamp" in vitals_df.columns:
        vitals_df["timestamp"] = pd.to_datetime(vitals_df["timestamp"], errors="coerce")
    if not labs_df.empty and "timestamp" in labs_df.columns:
        labs_df["timestamp"] = pd.to_datetime(labs_df["timestamp"], errors="coerce")

    master = ehr_df.copy()

    # Merge latest vitals
    if not vitals_df.empty:
        latest_v = _latest_vitals(vitals_df)
        master = master.merge(latest_v, on="patient_id", how="left")

    # Merge latest labs (wide format)
    if not labs_df.empty:
        latest_l = _latest_labs(labs_df)
        master = master.merge(latest_l, on="patient_id", how="left")

    out_path = silver_dir / "patient_master.csv"
    master.to_csv(out_path, index=False)
    log(f"  → silver/patient_master.csv  ({len(master)} rows, {len(master.columns)} cols)")
    return master


# ======================================================================== #
# 4. Public orchestrator                                                   #
# ======================================================================== #

def process(
    bronze_dir: Path = BRONZE_DIR,
    silver_dir: Path = SILVER_DIR,
) -> None:
    """Run all Silver-layer transformations in the correct order."""
    clean_vitals(bronze_dir, silver_dir)
    clean_labs(bronze_dir, silver_dir)
    build_patient_master(bronze_dir, silver_dir)
    log("Silver layer ✓ — cleaning complete.")


# ======================================================================== #
# 5. Trend Detection (Deterioration Alerts)                               #
# ======================================================================== #

def detect_trends(
    silver_dir: Path = SILVER_DIR,
) -> pd.DataFrame:
    """Detect consistently worsening vital signs across last 3 readings per patient.
    
    A trend is flagged when a patient's last 3 consecutive readings show
    consistent worsening direction (all increasing for HR/SYS/DIA, or all
    decreasing for OX), even if values haven't crossed anomaly thresholds yet.
    
    Args:
        silver_dir: Path to silver directory containing clean_vitals.csv
        
    Returns:
        DataFrame with detected trends
    """
    log("Silver layer — detecting trends …")
    
    vitals_path = silver_dir / "clean_vitals.csv"
    if not vitals_path.exists():
        log("  ⚠️  clean_vitals.csv not found, skipping trend detection", "warning")
        # Create empty CSV with correct headers
        empty_df = pd.DataFrame(columns=[
            "patient_id", "vital", "reading_1", "reading_2", "reading_3",
            "direction", "trend_label", "timestamp_1", "timestamp_2", 
            "timestamp_3", "already_critical"
        ])
        out_path = silver_dir / "trend_alerts.csv"
        empty_df.to_csv(out_path, index=False)
        log("  → silver/trend_alerts.csv  (0 trends)")
        return empty_df
    
    df = pd.read_csv(vitals_path)
    
    # Ensure timestamp is datetime for sorting
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    # Sort by patient and timestamp
    df = df.sort_values(["patient_id", "timestamp"])
    
    trends = []
    
    # Process each patient
    for patient_id, patient_df in df.groupby("patient_id"):
        # Need at least 3 readings
        if len(patient_df) < 3:
            continue
        
        # Get last 3 readings
        last_3 = patient_df.tail(3).reset_index(drop=True)
        
        # Check each vital sign
        vitals_to_check = [
            ("hr", "RISING", "HR trending up: {r1:.0f} → {r2:.0f} → {r3:.0f} — worsening", 120),
            ("ox", "FALLING", "OX trending down: {r1:.0f} → {r2:.0f} → {r3:.0f} — worsening", 92),
            ("sys", "RISING", "SYS trending up: {r1:.0f} → {r2:.0f} → {r3:.0f} — worsening", 160),
            ("dia", "RISING", "DIA trending up: {r1:.0f} → {r2:.0f} → {r3:.0f} — worsening", 100),
        ]
        
        for vital_col, direction, label_template, threshold in vitals_to_check:
            if vital_col not in last_3.columns:
                continue
            
            # Get the 3 values
            values = last_3[vital_col].tolist()
            timestamps = last_3["timestamp"].tolist()
            
            # Skip if any value is NaN
            if any(pd.isna(v) for v in values):
                continue
            
            r1, r2, r3 = values
            t1, t2, t3 = timestamps
            
            # Check for consistent worsening
            is_worsening = False
            
            if direction == "RISING":
                # Each reading strictly higher than previous
                is_worsening = (r1 < r2 < r3)
            elif direction == "FALLING":
                # Each reading strictly lower than previous
                is_worsening = (r1 > r2 > r3)
            
            if is_worsening:
                # Check if already critical
                already_critical = False
                if vital_col == "hr" and r3 > threshold:
                    already_critical = True
                elif vital_col == "ox" and r3 < threshold:
                    already_critical = True
                elif vital_col in ("sys", "dia") and r3 > threshold:
                    already_critical = True
                
                # Create trend label
                trend_label = label_template.format(r1=r1, r2=r2, r3=r3)
                
                trends.append({
                    "patient_id": patient_id,
                    "vital": vital_col,
                    "reading_1": r1,
                    "reading_2": r2,
                    "reading_3": r3,
                    "direction": direction,
                    "trend_label": trend_label,
                    "timestamp_1": str(t1),
                    "timestamp_2": str(t2),
                    "timestamp_3": str(t3),
                    "already_critical": already_critical,
                })
    
    # Create DataFrame
    if trends:
        trends_df = pd.DataFrame(trends)
    else:
        trends_df = pd.DataFrame(columns=[
            "patient_id", "vital", "reading_1", "reading_2", "reading_3",
            "direction", "trend_label", "timestamp_1", "timestamp_2", 
            "timestamp_3", "already_critical"
        ])
    
    # Save to CSV
    out_path = silver_dir / "trend_alerts.csv"
    trends_df.to_csv(out_path, index=False)
    log(f"  → silver/trend_alerts.csv  ({len(trends_df)} trends detected)")
    
    return trends_df
