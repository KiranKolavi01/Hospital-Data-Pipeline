"""
Visualization Module — Chart Generation.

Produces three PNG plots from the pipeline's silver and gold outputs:

    1.  hr_trend.png            — multi-line heart-rate over time per patient
    2.  oxygen_distribution.png — histogram with 92 % threshold line
    3.  anomaly_counts.png      — bar chart of anomaly-type frequencies
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — safe for headless servers
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.utils import (  # noqa: E402
    GOLD_DIR,
    SILVER_DIR,
    VIZ_DIR,
    log,
)


# Global style
plt.rcParams.update(
    {
        "figure.facecolor": "#ffffff",
        "axes.facecolor": "#f8f9fa",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "font.size": 11,
    }
)


# ======================================================================== #
# 1.  Heart Rate Trend                                                     #
# ======================================================================== #

def _heart_rate_trend(silver_dir: Path, viz_dir: Path) -> None:
    vitals_path = silver_dir / "clean_vitals.csv"
    if not vitals_path.exists():
        log("  ⚠ clean_vitals.csv not found — skipping HR trend.", "warning")
        return

    df = pd.read_csv(vitals_path)
    if "timestamp" not in df.columns or "hr" not in df.columns:
        log("  ⚠ Required columns missing for HR trend.", "warning")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["hr"] = pd.to_numeric(df["hr"], errors="coerce")
    df.dropna(subset=["timestamp", "hr"], inplace=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    for pid, grp in df.groupby("patient_id"):
        grp_sorted = grp.sort_values("timestamp")
        ax.plot(grp_sorted["timestamp"], grp_sorted["hr"], marker="o", label=str(pid))

    ax.set_title("Heart Rate Trend Over Time", fontweight="bold")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Heart Rate (bpm)")
    ax.axhline(y=120, color="red", linestyle="--", linewidth=1, label="Threshold (120 bpm)")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(viz_dir / "hr_trend.png", dpi=150)
    plt.close(fig)
    log("  → visualizations/hr_trend.png")


# ======================================================================== #
# 2.  Oxygen Distribution                                                 #
# ======================================================================== #

def _oxygen_distribution(silver_dir: Path, viz_dir: Path) -> None:
    vitals_path = silver_dir / "clean_vitals.csv"
    if not vitals_path.exists():
        log("  ⚠ clean_vitals.csv not found — skipping O₂ distribution.", "warning")
        return

    df = pd.read_csv(vitals_path)
    if "ox" not in df.columns:
        log("  ⚠ 'ox' column missing — skipping O₂ distribution.", "warning")
        return

    ox = pd.to_numeric(df["ox"], errors="coerce").dropna()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(ox, bins=15, color="#4a90d9", edgecolor="white", alpha=0.85)
    ax.axvline(x=92, color="red", linestyle="--", linewidth=2, label="Threshold (92%)")
    ax.set_title("Oxygen Saturation Distribution", fontweight="bold")
    ax.set_xlabel("SpO₂ (%)")
    ax.set_ylabel("Frequency")
    ax.legend()
    fig.tight_layout()
    fig.savefig(viz_dir / "oxygen_distribution.png", dpi=150)
    plt.close(fig)
    log("  → visualizations/oxygen_distribution.png")


# ======================================================================== #
# 3.  Anomaly Counts                                                       #
# ======================================================================== #

def _anomaly_counts(gold_dir: Path, viz_dir: Path) -> None:
    anomaly_path = gold_dir / "anomalies.csv"
    if not anomaly_path.exists():
        log("  ⚠ anomalies.csv not found — skipping anomaly chart.", "warning")
        return

    df = pd.read_csv(anomaly_path)
    if df.empty or "anomaly_type" not in df.columns:
        log("  ⚠ No anomaly data — skipping anomaly chart.", "warning")
        return

    counts = df["anomaly_type"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#e74c3c", "#e67e22", "#2ecc71", "#3498db", "#9b59b6"]
    bars = ax.bar(
        counts.index,
        counts.values,
        color=colors[: len(counts)],
        edgecolor="white",
    )
    # Value labels on bars
    for bar, val in zip(bars, counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            str(val),
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    ax.set_title("Anomaly Counts by Type", fontweight="bold")
    ax.set_xlabel("Anomaly Type")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(viz_dir / "anomaly_counts.png", dpi=150)
    plt.close(fig)
    log("  → visualizations/anomaly_counts.png")


# ======================================================================== #
# Public API                                                               #
# ======================================================================== #

def generate_all(
    silver_dir: Path = SILVER_DIR,
    gold_dir: Path = GOLD_DIR,
    viz_dir: Path = VIZ_DIR,
) -> None:
    """Generate all three visualizations and save PNGs."""
    log("Visualization — generating charts …")
    _heart_rate_trend(silver_dir, viz_dir)
    _oxygen_distribution(silver_dir, viz_dir)
    _anomaly_counts(gold_dir, viz_dir)
    log("Visualization ✓ — all charts generated.")
