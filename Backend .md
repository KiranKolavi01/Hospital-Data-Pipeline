# Backend – Hospital Data Pipeline (FastAPI)

## Tech Stack
- Python
- FastAPI
- pandas
- numpy
- matplotlib
- json
- pathlib

---

## Project Structure (Backend Scope)

```
project/
├── data/               # Input files (ehr.csv, vitals.json, labs.json)
├── bronze/             # Raw ingested CSV files
├── silver/             # Cleaned and standardized CSV files
├── gold/               # Anomaly detection results
├── visualizations/     # Generated plots (PNG)
├── src/
│   ├── bronze.py
│   ├── silver.py
│   ├── gold.py
│   ├── visualize.py
│   └── utils.py
└── main.py             # Pipeline orchestration + FastAPI app entry point
```

---

## How to Run

```bash
python main.py
```

---

## Pipeline Execution Flow

1. **Setup** – Create required folders (data, bronze, silver, gold, visualizations)
2. **Bronze** – Ingest raw data
3. **Silver** – Clean and standardize data, create patient master
4. **Gold** – Detect anomalies
5. **Visualization** – Generate plots

Each step prints a log message indicating completion.

---

## Bronze Layer (Raw Ingestion)

- Read source files from `/data` directory (`ehr.csv`, `vitals.json`, `labs.json`)
- Store exact raw copies as CSV files in `/bronze`
- No transformations applied
- Output files: `ehr.csv`, `vitals.csv`, `labs.csv`

---

## Silver Layer (Cleaning & Standardization)

### Clean Vitals
- Rename `patientId` → `patient_id`
- Convert UNIX timestamps to datetime
- Ensure numeric types for columns: `hr`, `ox`, `sys`, `dia`

### Clean Labs
- Rename columns: `patientId` → `patient_id`, `test` → `lab_test`, `value` → `lab_value`
- Convert timestamps
- Ensure numeric lab values

### Patient Master Table
- Combine EHR data with latest vitals and latest lab results per test for each patient
- Latest record selection:
  - Vitals: sorted by timestamp, grouped by `patient_id`, select last record
  - Labs: sorted by timestamp, grouped by `patient_id` and `lab_test`, select last record per test

### Type Conversions
- UNIX timestamps converted to pandas datetime
- All vital signs and lab values converted to numeric with error handling

### Output Files
- `clean_vitals.csv`
- `clean_labs.csv`
- `patient_master.csv`

---

## Gold Layer (Anomaly Detection)

Detect anomalies based on:

- **High Heart Rate**: HR > 120 bpm
- **Low Oxygen**: OX < 92%
- **High Blood Pressure**: SYS > 160 OR DIA > 100 mmHg

Output file: `anomalies.csv`

---

## Visualizations

Generate and save to `/visualizations/`:

1. **Heart Rate Trend** (`hr_trend.png`) – Multi-line plot showing heart rate over time for all patients
2. **Oxygen Distribution** (`oxygen_distribution.png`) – Histogram with threshold line at 92%
3. **Anomaly Counts** (`anomaly_counts.png`) – Bar chart showing count of each anomaly type

---

## Re-runnable Pipeline Behavior

- Always reads fresh input files from `/data`
- Overwrites all outputs in bronze, silver, and gold layers
- Regenerates all visualizations
- No caching or state persistence

---

## FastAPI Endpoints (expose pipeline outputs to frontend)

Expose the following via FastAPI REST endpoints:

- `GET /run-pipeline` – Trigger full pipeline execution (`main.py` logic)
- `GET /anomalies` – Return contents of `anomalies.csv` as JSON
- `GET /patient-master` – Return contents of `patient_master.csv` as JSON
- `GET /vitals` – Return contents of `clean_vitals.csv` as JSON
- `GET /labs` – Return contents of `clean_labs.csv` as JSON
- `GET /visualizations/{filename}` – Serve PNG files from `/visualizations/` directory

---

## Adding New Data

Add rows to input files (`ehr.csv`, `vitals.json`, `labs.json`) and re-run the pipeline. All outputs will automatically reflect the new data.
