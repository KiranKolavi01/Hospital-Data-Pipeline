# Database – Hospital Data Pipeline (SQLite)

## Tech Stack
- Python
- SQLite

---

## Tables

### 1. `vitals`
Stores cleaned vitals data from `clean_vitals.csv`.

| Column      | Type    | Notes                        |
|-------------|---------|------------------------------|
| patient_id  | TEXT    |                              |
| timestamp   | TEXT    | Converted from UNIX datetime |
| hr          | REAL    | Heart rate                   |
| ox          | REAL    | Oxygen level                 |
| sys         | REAL    | Systolic blood pressure      |
| dia         | REAL    | Diastolic blood pressure     |

---

### 2. `labs`
Stores cleaned labs data from `clean_labs.csv`.

| Column      | Type    | Notes                        |
|-------------|---------|------------------------------|
| patient_id  | TEXT    |                              |
| timestamp   | TEXT    | Converted from UNIX datetime |
| lab_test    | TEXT    | Name of the lab test         |
| lab_value   | REAL    | Numeric lab result           |

---

### 3. `patient_master`
Stores one row per patient combining EHR data with latest vitals and latest lab results per test.

| Column      | Type    | Notes                                        |
|-------------|---------|----------------------------------------------|
| patient_id  | TEXT    | Primary key                                  |
| (ehr fields)| TEXT    | All relevant columns from EHR data           |
| hr          | REAL    | Latest heart rate                            |
| ox          | REAL    | Latest oxygen level                          |
| sys         | REAL    | Latest systolic BP                           |
| dia         | REAL    | Latest diastolic BP                          |
| (lab columns)| REAL   | One column per lab_test with latest lab_value|

---

### 4. `anomalies`
Stores detected anomalies from `anomalies.csv`.

| Column          | Type    | Notes                                              |
|-----------------|---------|----------------------------------------------------|
| patient_id      | TEXT    |                                                    |
| anomaly_type    | TEXT    | `high_heart_rate`, `low_oxygen`, `high_bp`         |
| value           | REAL    | The offending measurement value                    |
| timestamp       | TEXT    | When the anomaly was recorded                      |

---

## Behavior

- On each pipeline run, all tables are dropped and re-created (no caching or state persistence)
- Data is loaded directly from the corresponding pipeline output CSV files after each layer completes
