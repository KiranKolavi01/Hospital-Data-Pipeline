"""
Hospital Data Pipeline — FastAPI Application & Pipeline Orchestrator.

Run with:
    python main.py          # starts uvicorn on http://0.0.0.0:8000
    uvicorn main:app        # alternative

Interactive API docs:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

from __future__ import annotations

import re
import traceback
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from src.utils import (
    GOLD_DIR,
    SILVER_DIR,
    VIZ_DIR,
    log,
    setup_directories,
)
from src.bronze import ingest as bronze_ingest
from src.silver import process as silver_process
from src.gold import detect_anomalies
from src.visualize import generate_all as viz_generate

# ====================================================================== #
# FastAPI App                                                             #
# ====================================================================== #

app = FastAPI(
    title="Hospital Data Pipeline API",
    description=(
        "Production-grade backend that processes hospital data through "
        "Bronze → Silver → Gold layers and exposes cleaned outputs, "
        "anomaly detection results, and visualizations via REST endpoints."
    ),
    version="1.0.0",
)

# ------- CORS (frontend team integration) ---------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================================================================== #
# Pipeline Orchestrator                                                   #
# ====================================================================== #

def run_pipeline() -> dict[str, str]:
    """Execute the full Bronze → Silver → Gold → Visualization pipeline.

    Returns a status dict suitable for JSON response.
    """
    log("=" * 60)
    log("Pipeline execution started")
    log("=" * 60)

    # 1. Setup
    setup_directories()

    # 2. Bronze — raw ingestion
    bronze_ingest()

    # 3. Silver — cleaning & patient master
    silver_process()

    # 4. Gold — anomaly detection
    detect_anomalies()

    # 5. Visualization
    viz_generate()

    log("=" * 60)
    log("Pipeline execution complete ✓")
    log("=" * 60)

    return {"status": "success", "message": "Pipeline executed successfully."}


# ====================================================================== #
# Helper: CSV → JSON-safe dict list                                      #
# ====================================================================== #

_SAFE_FILENAME = re.compile(r"^[\w\-]+\.png$")  # only alphanumeric + dash + .png


def _csv_to_json(path: Path, label: str) -> list[dict]:
    """Read a CSV and return records with NaN replaced by empty strings."""
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{label} data not found. Run the pipeline first (GET /run-pipeline).",
        )
    df = pd.read_csv(path)
    df = df.fillna("")  # NaN → empty string for clean JSON
    return df.to_dict(orient="records")


# ====================================================================== #
# Endpoints                                                               #
# ====================================================================== #

@app.get("/", tags=["Health"])
def root() -> dict:
    """Health-check / welcome endpoint."""
    return {
        "service": "Hospital Data Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy",
    }


@app.get("/run-pipeline", tags=["Pipeline"])
def trigger_pipeline() -> dict:
    """Trigger the full pipeline execution (Bronze → Silver → Gold → Viz)."""
    try:
        result = run_pipeline()
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        log(f"Pipeline error: {exc}\n{traceback.format_exc()}", "error")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {exc}",
        )


@app.get("/anomalies", tags=["Data"])
def get_anomalies() -> list[dict]:
    """Return detected anomalies from ``gold/anomalies.csv``."""
    return _csv_to_json(GOLD_DIR / "anomalies.csv", "Anomalies")


@app.get("/patient-master", tags=["Data"])
def get_patient_master() -> list[dict]:
    """Return the patient master table from ``silver/patient_master.csv``."""
    return _csv_to_json(SILVER_DIR / "patient_master.csv", "Patient Master")


@app.get("/vitals", tags=["Data"])
def get_vitals() -> list[dict]:
    """Return cleaned vitals from ``silver/clean_vitals.csv``."""
    return _csv_to_json(SILVER_DIR / "clean_vitals.csv", "Vitals")


@app.get("/labs", tags=["Data"])
def get_labs() -> list[dict]:
    """Return cleaned labs from ``silver/clean_labs.csv``."""
    return _csv_to_json(SILVER_DIR / "clean_labs.csv", "Labs")


@app.get("/visualizations/{filename}", tags=["Visualizations"])
def get_visualization(filename: str) -> FileResponse:
    """Serve a generated PNG chart from the ``visualizations/`` directory.

    Security: only ``.png`` files with safe names are served (no path traversal).
    """
    # --- Path-traversal protection ---
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Only alphanumeric .png files are allowed.",
        )

    file_path = VIZ_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Visualization '{filename}' not found. "
                "Run the pipeline first (GET /run-pipeline)."
            ),
        )

    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=filename,
    )


# ====================================================================== #
# Entry point                                                             #
# ====================================================================== #

if __name__ == "__main__":
    import uvicorn

    # Run the pipeline on startup so data is immediately available
    log("Running pipeline on startup …")
    run_pipeline()

    # Start the API server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
