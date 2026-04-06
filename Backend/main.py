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
    BRONZE_DIR,
    VIZ_DIR,
    log,
    setup_directories,
    start_run_log,
    finish_run_log,
)
from src.bronze import ingest as bronze_ingest
from src.silver import process as silver_process, detect_trends
from src.gold import detect_anomalies, calculate_risk_scores, dispatch_alerts
from src.visualize import generate_all as viz_generate
from src.database import init_database, load_all_data, query_pipeline_runs, query_alert_log, query_new_alerts_count

# Database path
DB_PATH = Path(__file__).parent / "hospital_pipeline.db"

# Webhook subscribers (in-memory list)
webhook_subscribers: list[str] = []

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
    # Start run log
    run_log = start_run_log()
    
    log("=" * 60)
    log("Pipeline execution started")
    log("=" * 60)

    # 1. Setup
    setup_directories()
    
    # Initialize database (drop and recreate tables)
    init_database()

    # 2. Bronze — raw ingestion
    bronze_ingest()
    
    # Update bronze counts
    run_log["bronze_ehr_count"] = len(pd.read_csv(BRONZE_DIR / "ehr.csv"))
    run_log["bronze_vitals_count"] = len(pd.read_csv(BRONZE_DIR / "vitals.csv"))
    run_log["bronze_labs_count"] = len(pd.read_csv(BRONZE_DIR / "labs.csv"))

    # 3. Silver — cleaning & patient master
    silver_process()
    
    # Update silver counts
    run_log["silver_vitals_count"] = len(pd.read_csv(SILVER_DIR / "clean_vitals.csv"))
    run_log["silver_labs_count"] = len(pd.read_csv(SILVER_DIR / "clean_labs.csv"))
    run_log["silver_patient_master_count"] = len(pd.read_csv(SILVER_DIR / "patient_master.csv"))
    
    detect_trends(SILVER_DIR)
    
    # Update trends count
    run_log["silver_trends_count"] = len(pd.read_csv(SILVER_DIR / "trend_alerts.csv"))

    # 4. Gold — anomaly detection
    detect_anomalies()
    
    # Update anomalies count
    run_log["gold_anomalies_count"] = len(pd.read_csv(GOLD_DIR / "anomalies.csv"))
    
    calculate_risk_scores(GOLD_DIR)
    
    # Update risk scores count
    run_log["gold_risk_scores_count"] = len(pd.read_csv(GOLD_DIR / "risk_scores.csv"))
    
    # Dispatch alerts for new anomalies
    new_alert_count = dispatch_alerts(GOLD_DIR, DB_PATH)
    run_log["new_alerts_count"] = new_alert_count

    # 5. Visualization
    viz_generate()
    
    # 6. Load data into database
    load_all_data()

    log("=" * 60)
    log("Pipeline execution complete ✓")
    log("=" * 60)
    
    # Finish run log and write to database
    finish_run_log(run_log, DB_PATH)

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


@app.get("/risk-scores", tags=["Data"])
def get_risk_scores() -> list[dict]:
    """Return the calculated patient risk scores from ``gold/risk_scores.csv``."""
    return _csv_to_json(GOLD_DIR / "risk_scores.csv", "Risk Scores")


@app.get("/trend-alerts", tags=["Data"])
def get_trend_alerts() -> list[dict]:
    """Return detected trend alerts from ``silver/trend_alerts.csv``."""
    return _csv_to_json(SILVER_DIR / "trend_alerts.csv", "Trend Alerts")


@app.get("/pipeline-history", tags=["Data"])
def get_pipeline_history() -> list[dict]:
    """Return pipeline run history from the database."""
    try:
        return query_pipeline_runs()
    except Exception as exc:
        log(f"Pipeline history error: {exc}\n{traceback.format_exc()}", "error")
        # Return empty list if table doesn't exist yet
        return []


@app.get("/alert-log", tags=["Alerts"])
def get_alert_log() -> list[dict]:
    """Return all alert log records from the database."""
    try:
        return query_alert_log()
    except Exception as exc:
        log(f"Alert log error: {exc}\n{traceback.format_exc()}", "error")
        # Return empty list if table doesn't exist yet
        return []


@app.get("/new-alerts-count", tags=["Alerts"])
def get_new_alerts_count() -> dict:
    """Return the count of new alerts from the most recent pipeline run."""
    try:
        return query_new_alerts_count()
    except Exception as exc:
        log(f"New alerts count error: {exc}\n{traceback.format_exc()}", "error")
        return {"count": 0, "run_id": None}


@app.post("/webhook/subscribe", tags=["Webhooks"])
def subscribe_webhook(body: dict) -> dict:
    """Subscribe a webhook URL to receive alert notifications."""
    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    if url not in webhook_subscribers:
        webhook_subscribers.append(url)
    
    return {"status": "subscribed", "url": url}


@app.post("/webhook/notify", tags=["Webhooks"])
async def notify_webhooks() -> dict:
    """Notify all subscribed webhooks about new alerts (internal use)."""
    try:
        import httpx
        
        # Get new alerts from most recent run
        alert_data = query_new_alerts_count()
        
        if alert_data["count"] == 0:
            return {"status": "no_alerts", "notified": 0}
        
        # Get the actual alert records
        all_alerts = query_alert_log()
        current_run_id = alert_data["run_id"]
        
        # Filter alerts for current run
        new_alerts = [a for a in all_alerts if a.get("run_id") == current_run_id]
        
        notified_count = 0
        failed_urls = []
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for url in webhook_subscribers:
                try:
                    response = await client.post(url, json={"alerts": new_alerts})
                    if response.status_code < 400:
                        notified_count += 1
                    else:
                        failed_urls.append(url)
                        log(f"Webhook notification failed for {url}: HTTP {response.status_code}", "warning")
                except Exception as e:
                    failed_urls.append(url)
                    log(f"Webhook notification failed for {url}: {str(e)}", "warning")
        
        return {
            "status": "completed",
            "notified": notified_count,
            "failed": len(failed_urls),
            "failed_urls": failed_urls
        }
        
    except ImportError:
        log("httpx not installed, webhook notifications disabled", "warning")
        return {"status": "error", "message": "httpx not installed"}
    except Exception as exc:
        log(f"Webhook notification error: {exc}\n{traceback.format_exc()}", "error")
        raise HTTPException(status_code=500, detail=str(exc))


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
