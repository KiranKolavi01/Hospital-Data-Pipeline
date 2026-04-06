# HSDPL — Hospital Data Pipeline & Risk Engine

A complete data pipeline for healthcare analytics. Drop in raw EHR, vitals, and lab records, get clean validated data, anomaly detection, patient risk scores, health trend alerts, and an interactive dashboard — all powered by Python and SQLite with zero external database setup.


---

## What It Does

HSDPL takes messy hospital data and turns it into actionable health insights:

- **Cleans and standardizes** raw JSON and CSV health records into a structured format
- **Detects health anomalies** like irregular heart rates, low oxygen, or high blood pressure automatically
- **Calculates patient risk scores** to identify which patients need immediate medical attention
- **Flags deteriorating trends** by tracking vitals across multiple visits for early warnings
- **Visualizes everything** through an interactive Streamlit dashboard and static matplotlib charts

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.8+ |
| Backend API | FastAPI |
| Database | SQLite3 |
| Data Processing | pandas, numpy |
| Visualization | Streamlit, matplotlib |
| Orchestration | Uvicorn |

---

## Project Structure

```
HSDPL/
├── Backend/
│   ├── data/              # Put your raw input files here (CSV/JSON)
│   ├── bronze/            # Raw ingested records (auto-generated)
│   ├── silver/            # Cleaned and standardized records (auto-generated)
│   ├── gold/              # Detected anomalies and risk scores (auto-generated)
│   ├── visualizations/    # Generated static charts
│   ├── src/
│   │   ├── bronze.py      # Raw data ingestion
│   │   ├── silver.py      # Data cleaning & patient master builder
│   │   ├── gold.py        # Anomaly & risk detection engine
│   │   ├── visualize.py   # Chart generation logic
│   │   ├── database.py    # SQLite database operations
│   │   └── utils.py       # Shared utilities
│   ├── hospital_pipeline.db # SQLite database (auto-created)
│   ├── main.py            # FastAPI app & pipeline orchestrator
│   ├── requirements.txt   # Backend dependencies
│   └── verify_backend.sh  # System verification script
├── Frontend/
│   ├── api/               # API client connector
│   ├── pages/             # One file per dashboard page
│   ├── styles/            # Custom CSS and design system
│   ├── utils/             # Helper components
│   ├── app.py             # Main Streamlit app
│   ├── config.py          # Configuration settings
│   └── requirements.txt   # Frontend dependencies
└── README.md
```

---

## Getting Started

### 1. Install dependencies

Open two terminals (one for backend, one for frontend) and run:

```bash
# In Terminal 1 (Backend)
cd Backend
pip install -r requirements.txt

# In Terminal 2 (Frontend)
cd Frontend
pip install -r requirements.txt
```

### 2. Add your data files

Place your input files in `Backend/data/`:

```
ehr.csv
vitals.json
labs.json
```

### 3. Start the backend & run pipeline

```bash
cd Backend
python main.py
```

The system will automatically run the full pipeline (Bronze → Silver → Gold), load the database, and start the API at `http://localhost:8000`.

### 4. Launch the dashboard

```bash
# In your second terminal
cd Frontend
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## Dashboard Pages

| Page | What It Shows |
|---|---|
| Run Pipeline | Trigger the full pipeline and watch the live deployment logs |
| Patient Master | A consolidated view merging EHR demographics with latest vitals and labs |
| Risk Leaderboard | Ranking of patients from critical to stable based on their total risk score |
| Anomalies | Detailed view of specific health anomalies detected |
| Alert Log | A real-time timeline of new alerts and a webhook subscription feature |
| Trend Alerts | Smart warnings for patients with deteriorating health conditions |
| Vitals & Labs | Cleaned raw data for every recorded vital sign and lab result |
| Visualizations | Static matplotlib dashboard charts and data distributions |

---

## Anomaly Detection Rules

The Gold layer scans every record for critical health anomalies. A patient is flagged if they meet any of these 3 conditions:

1. **High Heart Rate** — Heart rate is greater than 120 bpm
2. **Low Oxygen** — Oxygen saturation falls below 92%
3. **High Blood Pressure** — Systolic BP > 160 OR Diastolic BP > 100

*Any detected records are immediately sent to the `anomalies` table.*

---

## Patient Risk Scoring

Risk scores help triage patients based on the severity and count of their anomalies.

| Risk Level | Total Score Needed | Description |
|---|---|---|
| CRITICAL | 200+ points | Multiple severe anomalies, needs immediate action |
| HIGH | 100-199 points | At least one severe anomaly |
| MEDIUM | 50-99 points | Borderline conditions, needs monitoring |
| STABLE | Under 50 points | Normal or near-normal conditions |

---

## Health Trend Alerts

The pipeline analyzes historical records to find deteriorating trends across multiple visits. It automatically flags situations such as:
- Steadily increasing heart rate across the last 3 measurements
- Dropping oxygen levels over the last 24 hours

---

## API Endpoints

Once `python main.py` is running:

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/` | Health check |
| GET | `/run-pipeline` | Triggers all pipeline stages from scratch |
| GET | `/vitals` | Cleaned vital signs |
| GET | `/labs` | Cleaned lab results |
| GET | `/patient-master` | Complete merged patient records |
| GET | `/anomalies` | Detected anomaly flags |
| GET | `/risk-scores` | Computed risk scores per patient |
| GET | `/trend-alerts` | Deteriorating health trend warnings |
| GET | `/alert-log` | Timeline of alerts |
| GET | `/new-alerts-count` | Number of new alerts in the most recent run |
| GET | `/visualizations/{filename}` | Static chart images |

---

## Output Files

After running the pipeline, these files are generated automatically and completely overwritten with fresh data on every run:

| Location | Contents |
|---|---|
| `Backend/hospital_pipeline.db` | SQLite database with all tables |
| `Backend/bronze/*.csv` | Raw snapshots of ingested data |
| `Backend/silver/*.csv` | Validated, standardized, and merged records |
| `Backend/gold/*.csv` | Anomalies, risk scores, and trend alerts |
| `Backend/visualizations/*.png`| Distribution charts and health trend plots |

---

## Troubleshooting

### "ERR_CONNECTION_REFUSED" on the Dashboard
- Make sure you left Terminal 2 running (`streamlit run app.py`)
- Check that the Streamlit terminal says it's running on port 8501 (sometimes it picks 8502)

### Backend won't start
- Ensure you have Python 3.8+ installed (`python --version`)
- Double-check that `data/ehr.csv`, `data/vitals.json`, and `data/labs.json` exist

### No Data in Dashboard
- The database is created automatically when the backend starts. If you don't see data, hit the **Run Pipeline** button in the dashboard or open `http://localhost:8000/run-pipeline`.
