# Hospital Data Pipeline - Quick Start Guide

Get the entire system running in 3 simple steps.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Step 1: Install Dependencies

```bash
# Install Backend dependencies
cd Backend
pip install -r requirements.txt

# Install Frontend dependencies (in a new terminal)
cd Frontend
pip install -r requirements.txt
```

## Step 2: Start the Backend

```bash
cd Backend
python main.py
```

You should see:
```
2026-03-28 00:38:20 | INFO    | Running pipeline on startup …
2026-03-28 00:38:20 | INFO    | ============================================================
2026-03-28 00:38:20 | INFO    | Pipeline execution started
...
2026-03-28 00:38:20 | INFO    | Pipeline execution complete ✓
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The backend will:
- ✅ Run the full pipeline (Bronze → Silver → Gold → Visualization)
- ✅ Create all output files
- ✅ Initialize and populate the SQLite database
- ✅ Start the API server on http://localhost:8000

## Step 3: Start the Frontend

Open a **new terminal** and run:

```bash
cd Frontend
streamlit run app.py
```

The frontend will open automatically in your browser at http://localhost:8501

## What You Can Do Now

### Backend API
Visit http://localhost:8000/docs for interactive API documentation

Test endpoints:
```bash
curl http://localhost:8000/
curl http://localhost:8000/vitals
curl http://localhost:8000/anomalies
```

### Frontend Web App
Navigate through 6 pages:
1. **Run Pipeline** - Trigger pipeline execution
2. **Patient Master** - View consolidated patient data
3. **Anomalies** - Monitor health anomalies
4. **Vitals** - Browse vitals data
5. **Labs** - Explore lab results
6. **Visualizations** - View charts

## Verify Everything Works

Run the verification script:

```bash
cd Backend
./verify_backend.sh
```

This checks:
- ✅ Backend server is running
- ✅ All output files exist
- ✅ All API endpoints work
- ✅ Database has all 4 tables
- ✅ Security measures in place

## Adding New Data

1. Add rows to input files:
   - `Backend/data/ehr.csv`
   - `Backend/data/vitals.json`
   - `Backend/data/labs.json`

2. Re-run the pipeline:
   ```bash
   curl http://localhost:8000/run-pipeline
   ```
   Or click "Run Pipeline" in the frontend

3. All outputs will automatically update!

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.8+)
- Install dependencies: `pip install -r requirements.txt`
- Check if port 8000 is in use: `lsof -i :8000`

### Frontend can't connect
- Ensure backend is running on http://localhost:8000
- Check `Frontend/config.py` has correct API_BASE_URL
- Try restarting both backend and frontend

### No data showing
- Run the pipeline first: `python main.py` or `curl http://localhost:8000/run-pipeline`
- Check input files exist in `Backend/data/`
- Look for error messages in terminal

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Check the generated visualizations in `Backend/visualizations/`
- Query the database: `sqlite3 Backend/hospital_pipeline.db`
- Read the full README.md for detailed documentation

## Quick Commands Reference

```bash
# Start backend
cd Backend && python main.py

# Start frontend (new terminal)
cd Frontend && streamlit run app.py

# Verify everything
cd Backend && ./verify_backend.sh

# Trigger pipeline via API
curl http://localhost:8000/run-pipeline

# Check database
sqlite3 Backend/hospital_pipeline.db ".tables"

# View API docs
open http://localhost:8000/docs
```

## Support

If you encounter issues:
1. Check the terminal output for error messages
2. Run the verification script: `./verify_backend.sh`
3. Review the full README.md for detailed troubleshooting
4. Check AUDIT_COMPLETE.md to verify all components

---

🎉 **You're all set!** The Hospital Data Pipeline is now running.
