# Frontend – Hospital Data Pipeline (Streamlit + HTML/CSS)

## Tech Stack
- Python
- Streamlit
- HTML + CSS (UI polish only)

---

## Pages / Sections to Build

### 1. Run Pipeline
- A button to trigger the pipeline: calls `GET /run-pipeline` backend endpoint
- Show log/status messages indicating each step completed (Setup → Bronze → Silver → Gold → Visualization)

---

### 2. Patient Master View
- Fetch data from `GET /patient-master`
- Display as an interactive table
- Each row represents one patient with their latest vitals and latest lab results

---

### 3. Anomalies View
- Fetch data from `GET /anomalies`
- Display detected anomalies in a table
- Anomaly types to display:
  - High Heart Rate (HR > 120 bpm)
  - Low Oxygen (OX < 92%)
  - High Blood Pressure (SYS > 160 OR DIA > 100 mmHg)

---

### 4. Vitals View
- Fetch data from `GET /vitals`
- Display cleaned vitals data as an interactive table

---

### 5. Labs View
- Fetch data from `GET /labs`
- Display cleaned labs data as an interactive table

---

### 6. Visualizations View
- Fetch and display the following images from `GET /visualizations/{filename}`:
  1. **Heart Rate Trend** (`hr_trend.png`) – Multi-line plot, heart rate over time for all patients
  2. **Oxygen Distribution** (`oxygen_distribution.png`) – Histogram with 92% threshold line
  3. **Anomaly Counts** (`anomaly_counts.png`) – Bar chart of anomaly type counts