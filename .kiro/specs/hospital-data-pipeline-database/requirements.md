# Requirements Document

## Introduction

This document specifies the requirements for a production-ready SQLite database system for the Hospital Data Pipeline project. The database will store cleaned hospital data from the pipeline's Bronze-Silver-Gold processing layers and provide efficient query access for the FastAPI backend and Streamlit frontend. The database must be idempotent, supporting full table recreation on each pipeline run without state persistence between runs.

## Glossary

- **Database_Manager**: The SQLite database management module responsible for schema creation, data loading, and query operations
- **Pipeline_Orchestrator**: The main.py module that coordinates Bronze → Silver → Gold data processing
- **Vitals_Table**: SQLite table storing cleaned patient vital signs (heart rate, oxygen, blood pressure)
- **Labs_Table**: SQLite table storing cleaned laboratory test results
- **Patient_Master_Table**: SQLite table storing one row per patient with latest vitals and lab results
- **Anomalies_Table**: SQLite table storing detected clinical anomalies
- **Backend_API**: The FastAPI application that serves data to the frontend
- **CSV_Loader**: Component that reads pipeline output CSV files and inserts data into database tables
- **Schema_Manager**: Component that creates and drops database tables

## Requirements

### Requirement 1: Database Initialization and Schema Management

**User Story:** As a pipeline operator, I want the database to be automatically initialized with the correct schema, so that data can be stored without manual setup.

#### Acceptance Criteria

1. WHEN the Pipeline_Orchestrator starts, THE Database_Manager SHALL create a SQLite database file at `Backend/hospital_pipeline.db`
2. THE Schema_Manager SHALL create four tables: Vitals_Table, Labs_Table, Patient_Master_Table, and Anomalies_Table
3. THE Vitals_Table SHALL have columns: patient_id (TEXT), timestamp (TEXT), hr (REAL), ox (REAL), sys (REAL), dia (REAL)
4. THE Labs_Table SHALL have columns: patient_id (TEXT), timestamp (TEXT), lab_test (TEXT), lab_value (REAL)
5. THE Patient_Master_Table SHALL have patient_id as PRIMARY KEY (TEXT) and include all EHR fields (TEXT), latest vitals (hr, ox, sys, dia as REAL), and dynamic lab columns (REAL)
6. THE Anomalies_Table SHALL have columns: patient_id (TEXT), anomaly_type (TEXT), value (REAL), timestamp (TEXT)
7. THE Schema_Manager SHALL create indexes on patient_id columns for all tables to optimize query performance

### Requirement 2: Idempotent Table Recreation

**User Story:** As a pipeline operator, I want all database tables to be dropped and recreated on each pipeline run, so that the database always reflects the latest pipeline output without stale data.

#### Acceptance Criteria

1. WHEN the Pipeline_Orchestrator executes, THE Schema_Manager SHALL drop all existing tables before creating new ones
2. THE Schema_Manager SHALL use `DROP TABLE IF EXISTS` statements to avoid errors when tables don't exist
3. AFTER table recreation, THE Database_Manager SHALL have empty tables ready for fresh data loading
4. THE Database_Manager SHALL complete table recreation within 100 milliseconds to minimize pipeline overhead

### Requirement 3: Load Vitals Data from CSV

**User Story:** As a pipeline operator, I want cleaned vitals data to be loaded into the database, so that the backend can query vital signs efficiently.

#### Acceptance Criteria

1. WHEN the Silver layer completes processing, THE CSV_Loader SHALL read `Backend/silver/clean_vitals.csv`
2. THE CSV_Loader SHALL insert all rows from clean_vitals.csv into the Vitals_Table
3. THE CSV_Loader SHALL preserve data types: patient_id as TEXT, timestamp as TEXT, hr/ox/sys/dia as REAL
4. IF clean_vitals.csv does not exist, THEN THE CSV_Loader SHALL log a warning and continue without error
5. THE CSV_Loader SHALL use batch insert operations to load data efficiently

### Requirement 4: Load Labs Data from CSV

**User Story:** As a pipeline operator, I want cleaned laboratory test data to be loaded into the database, so that the backend can query lab results efficiently.

#### Acceptance Criteria

1. WHEN the Silver layer completes processing, THE CSV_Loader SHALL read `Backend/silver/clean_labs.csv`
2. THE CSV_Loader SHALL insert all rows from clean_labs.csv into the Labs_Table
3. THE CSV_Loader SHALL preserve data types: patient_id/timestamp/lab_test as TEXT, lab_value as REAL
4. IF clean_labs.csv does not exist, THEN THE CSV_Loader SHALL log a warning and continue without error
5. THE CSV_Loader SHALL use batch insert operations to load data efficiently

### Requirement 5: Load Patient Master Data from CSV

**User Story:** As a pipeline operator, I want the patient master table to be loaded into the database, so that the backend can query comprehensive patient records efficiently.

#### Acceptance Criteria

1. WHEN the Silver layer completes processing, THE CSV_Loader SHALL read `Backend/silver/patient_master.csv`
2. THE CSV_Loader SHALL dynamically detect all columns in patient_master.csv including EHR fields and lab columns
3. THE Schema_Manager SHALL create the Patient_Master_Table with dynamic columns based on the CSV structure
4. THE CSV_Loader SHALL insert all rows from patient_master.csv into the Patient_Master_Table
5. IF patient_master.csv does not exist, THEN THE CSV_Loader SHALL log a warning and continue without error

### Requirement 6: Load Anomalies Data from CSV

**User Story:** As a pipeline operator, I want detected anomalies to be loaded into the database, so that the backend can query clinical alerts efficiently.

#### Acceptance Criteria

1. WHEN the Gold layer completes processing, THE CSV_Loader SHALL read `Backend/gold/anomalies.csv`
2. THE CSV_Loader SHALL insert all rows from anomalies.csv into the Anomalies_Table
3. THE CSV_Loader SHALL preserve data types: patient_id/anomaly_type/timestamp as TEXT, value as REAL
4. IF anomalies.csv does not exist, THEN THE CSV_Loader SHALL log a warning and continue without error
5. THE CSV_Loader SHALL use batch insert operations to load data efficiently

### Requirement 7: Backend API Database Integration

**User Story:** As a backend developer, I want API endpoints to query the database instead of reading CSV files, so that data access is faster and more reliable.

#### Acceptance Criteria

1. THE Backend_API SHALL modify the `/vitals` endpoint to query the Vitals_Table instead of reading clean_vitals.csv
2. THE Backend_API SHALL modify the `/labs` endpoint to query the Labs_Table instead of reading clean_labs.csv
3. THE Backend_API SHALL modify the `/patient-master` endpoint to query the Patient_Master_Table instead of reading patient_master.csv
4. THE Backend_API SHALL modify the `/anomalies` endpoint to query the Anomalies_Table instead of reading anomalies.csv
5. THE Backend_API SHALL return data in the same JSON format as the current CSV-based implementation to maintain frontend compatibility
6. IF a database query fails, THEN THE Backend_API SHALL return an HTTP 500 error with a descriptive error message

### Requirement 8: Database Connection Management

**User Story:** As a backend developer, I want database connections to be managed properly, so that resources are not leaked and the application remains stable.

#### Acceptance Criteria

1. THE Database_Manager SHALL use context managers (with statements) for all database connections
2. THE Database_Manager SHALL close database connections after each operation completes
3. THE Database_Manager SHALL use a connection pool WHERE concurrent access is required
4. IF a database connection fails, THEN THE Database_Manager SHALL log the error and raise an exception
5. THE Database_Manager SHALL set a connection timeout of 30 seconds to prevent hanging operations

### Requirement 9: Error Handling and Logging

**User Story:** As a pipeline operator, I want comprehensive error handling and logging, so that I can diagnose issues when database operations fail.

#### Acceptance Criteria

1. WHEN a database operation fails, THE Database_Manager SHALL log the error with the operation name, error message, and stack trace
2. THE Database_Manager SHALL use the existing `log()` utility function from `src/utils.py` for consistent logging
3. IF a CSV file is missing during data loading, THEN THE CSV_Loader SHALL log a warning but not stop the pipeline
4. IF a database schema creation fails, THEN THE Schema_Manager SHALL log an error and raise an exception to stop the pipeline
5. THE Database_Manager SHALL log successful completion of each major operation (table creation, data loading)

### Requirement 10: Database Module Structure

**User Story:** As a backend developer, I want the database code to be well-organized and maintainable, so that future enhancements are easy to implement.

#### Acceptance Criteria

1. THE Database_Manager SHALL be implemented in a new file `Backend/src/database.py`
2. THE database.py module SHALL export functions: `init_database()`, `load_all_data()`, `query_vitals()`, `query_labs()`, `query_patient_master()`, `query_anomalies()`
3. THE Pipeline_Orchestrator SHALL call `init_database()` before Bronze layer processing
4. THE Pipeline_Orchestrator SHALL call `load_all_data()` after Gold layer processing completes
5. THE Backend_API SHALL import and use the query functions from database.py in each endpoint

### Requirement 11: Data Type Preservation and NULL Handling

**User Story:** As a data analyst, I want NULL values and data types to be preserved correctly, so that data integrity is maintained throughout the pipeline.

#### Acceptance Criteria

1. THE CSV_Loader SHALL convert empty strings in CSV files to NULL values in the database
2. THE CSV_Loader SHALL convert pandas NaN values to NULL values in the database
3. THE Backend_API SHALL convert NULL values to empty strings in JSON responses to match current frontend expectations
4. THE Database_Manager SHALL enforce REAL data type for numeric columns (hr, ox, sys, dia, lab_value)
5. THE Database_Manager SHALL enforce TEXT data type for string columns (patient_id, timestamp, lab_test, anomaly_type)

### Requirement 12: Performance and Scalability

**User Story:** As a pipeline operator, I want database operations to be fast, so that the pipeline completes quickly even with large datasets.

#### Acceptance Criteria

1. THE CSV_Loader SHALL load 10,000 rows of vitals data in less than 2 seconds
2. THE Backend_API SHALL return query results for any table in less than 500 milliseconds for datasets up to 10,000 rows
3. THE Schema_Manager SHALL create all indexes during table creation to optimize query performance
4. THE CSV_Loader SHALL use pandas `to_sql()` method with `if_exists='append'` for efficient bulk inserts
5. THE Database_Manager SHALL use `PRAGMA journal_mode=WAL` to enable concurrent reads during writes
