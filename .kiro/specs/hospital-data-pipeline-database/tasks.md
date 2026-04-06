# Implementation Plan: Hospital Data Pipeline SQLite Database

## Overview

This implementation plan converts the database design into actionable coding tasks. The database module will be created in `Backend/src/database.py` and integrated with the existing pipeline orchestrator and FastAPI backend. All tables are dropped and recreated on each pipeline run (idempotent design). The implementation follows a bottom-up approach: core database operations first, then data loading, then API integration, with testing tasks integrated throughout.

## Tasks

- [x] 1. Set up database module structure and connection management
  - Create `Backend/src/database.py` with imports (sqlite3, pandas, pathlib, traceback)
  - Implement `_get_connection()` function with WAL mode, 30-second timeout, and database path configuration
  - Implement connection context manager pattern for automatic cleanup
  - Add logging using existing `log()` utility from `src/utils.py`
  - _Requirements: 8.1, 8.2, 8.4, 8.5, 9.2, 10.1, 10.2, 12.5_

- [ ]* 1.1 Write property test for connection cleanup
  - **Property 7: Connection Cleanup**
  - **Validates: Requirements 8.2**
  - Verify that database connections are closed after operations complete
  - _Requirements: 8.2_

- [x] 2. Implement schema management functions
  - [x] 2.1 Implement `_drop_tables()` function using DROP TABLE IF EXISTS for all four tables
    - Drop tables: vitals, labs, patient_master, anomalies
    - Use IF EXISTS to avoid errors when tables don't exist
    - _Requirements: 2.1, 2.2_

  - [x] 2.2 Implement `_detect_patient_master_columns()` function
    - Read `Backend/silver/patient_master.csv` using pandas
    - Extract column names and infer data types (TEXT for strings, REAL for numeric)
    - Return list of column definitions for CREATE TABLE statement
    - Handle missing file gracefully with warning log
    - _Requirements: 5.2, 5.3, 9.3_

  - [x] 2.3 Implement `_create_tables()` function with static and dynamic schemas
    - Create vitals table with columns: patient_id (TEXT), timestamp (TEXT), hr (REAL), ox (REAL), sys (REAL), dia (REAL)
    - Create labs table with columns: patient_id (TEXT), timestamp (TEXT), lab_test (TEXT), lab_value (REAL)
    - Create patient_master table with dynamic columns from `_detect_patient_master_columns()`
    - Create anomalies table with columns: patient_id (TEXT), anomaly_type (TEXT), value (REAL), timestamp (TEXT)
    - Create indexes: idx_vitals_patient, idx_labs_patient, idx_patient_master_patient, idx_anomalies_patient
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 5.3_

  - [x] 2.4 Implement `init_database()` public function
    - Call `_get_connection()` to establish database connection
    - Call `_drop_tables()` to remove existing tables
    - Call `_create_tables()` to create fresh schema
    - Log successful initialization
    - Handle errors with logging and exception raising
    - _Requirements: 1.1, 2.1, 2.3, 9.4, 10.2_

- [ ]* 2.5 Write property test for idempotent table initialization
  - **Property 1: Idempotent Table Initialization**
  - **Validates: Requirements 2.1, 2.3**
  - Verify that calling `init_database()` multiple times results in empty tables with correct schema
  - _Requirements: 2.1, 2.3_

- [ ]* 2.6 Write property test for dynamic schema matching
  - **Property 4: Dynamic Schema Matching**
  - **Validates: Requirements 5.2, 5.3**
  - Generate random patient_master.csv files with arbitrary columns and verify table schema matches
  - _Requirements: 5.2, 5.3_

- [x] 3. Checkpoint - Verify schema creation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement CSV data loading functions
  - [x] 4.1 Implement `_load_vitals()` function
    - Check if `Backend/silver/clean_vitals.csv` exists
    - If missing, log warning and return without error
    - Read CSV using pandas with appropriate dtypes
    - Convert NaN values to NULL
    - Use pandas `to_sql()` with `if_exists='append'` for batch insert into vitals table
    - Log row count and success message
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.3, 11.1, 11.2, 12.4_

  - [x] 4.2 Implement `_load_labs()` function
    - Check if `Backend/silver/clean_labs.csv` exists
    - If missing, log warning and return without error
    - Read CSV using pandas with appropriate dtypes
    - Convert NaN values to NULL
    - Use pandas `to_sql()` with `if_exists='append'` for batch insert into labs table
    - Log row count and success message
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.3, 11.1, 11.2, 12.4_

  - [x] 4.3 Implement `_load_patient_master()` function
    - Check if `Backend/silver/patient_master.csv` exists
    - If missing, log warning and return without error
    - Read CSV using pandas with dynamic column detection
    - Convert NaN values to NULL
    - Use pandas `to_sql()` with `if_exists='append'` for batch insert into patient_master table
    - Log row count and success message
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 9.3, 11.1, 11.2, 12.4_

  - [x] 4.4 Implement `_load_anomalies()` function
    - Check if `Backend/gold/anomalies.csv` exists
    - If missing, log warning and return without error
    - Read CSV using pandas with appropriate dtypes
    - Convert NaN values to NULL
    - Use pandas `to_sql()` with `if_exists='append'` for batch insert into anomalies table
    - Log row count and success message
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.3, 11.1, 11.2, 12.4_

  - [x] 4.5 Implement `load_all_data()` public function
    - Call `_get_connection()` to establish database connection
    - Call `_load_vitals()`, `_load_labs()`, `_load_patient_master()`, `_load_anomalies()` in sequence
    - Log overall completion message
    - Handle errors with logging and exception raising
    - _Requirements: 9.1, 9.5, 10.2_

- [ ]* 4.6 Write property test for CSV to database row preservation
  - **Property 2: CSV to Database Row Preservation**
  - **Validates: Requirements 3.2, 4.2, 5.4, 6.2**
  - Generate random CSV files and verify row counts match database after loading
  - _Requirements: 3.2, 4.2, 5.4, 6.2_

- [ ]* 4.7 Write property test for missing file graceful handling
  - **Property 6: Missing File Graceful Handling**
  - **Validates: Requirements 3.4, 4.4, 5.5, 6.4, 9.3**
  - Verify that missing CSV files log warnings without raising exceptions
  - _Requirements: 3.4, 4.4, 5.5, 6.4, 9.3_

- [x] 5. Checkpoint - Verify data loading
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement database query functions
  - [x] 6.1 Implement `query_vitals()` function
    - Call `_get_connection()` to establish database connection
    - Execute SELECT * FROM vitals query
    - Convert result rows to list of dictionaries
    - Convert NULL values to empty strings for JSON compatibility
    - Return list of dicts for API serialization
    - Handle errors with logging and exception raising
    - _Requirements: 7.1, 10.2, 11.3_

  - [x] 6.2 Implement `query_labs()` function
    - Call `_get_connection()` to establish database connection
    - Execute SELECT * FROM labs query
    - Convert result rows to list of dictionaries
    - Convert NULL values to empty strings for JSON compatibility
    - Return list of dicts for API serialization
    - Handle errors with logging and exception raising
    - _Requirements: 7.2, 10.2, 11.3_

  - [x] 6.3 Implement `query_patient_master()` function
    - Call `_get_connection()` to establish database connection
    - Execute SELECT * FROM patient_master query
    - Convert result rows to list of dictionaries
    - Convert NULL values to empty strings for JSON compatibility
    - Return list of dicts for API serialization
    - Handle errors with logging and exception raising
    - _Requirements: 7.3, 10.2, 11.3_

  - [x] 6.4 Implement `query_anomalies()` function
    - Call `_get_connection()` to establish database connection
    - Execute SELECT * FROM anomalies query
    - Convert result rows to list of dictionaries
    - Convert NULL values to empty strings for JSON compatibility
    - Return list of dicts for API serialization
    - Handle errors with logging and exception raising
    - _Requirements: 7.4, 10.2, 11.3_

- [ ]* 6.5 Write property test for data type preservation
  - **Property 3: Data Type Preservation**
  - **Validates: Requirements 3.3, 4.3, 6.3, 11.4, 11.5**
  - Verify that TEXT columns return strings, REAL columns return floats, and NULL values are preserved
  - _Requirements: 3.3, 4.3, 6.3, 11.4, 11.5_

- [ ]* 6.6 Write property test for NULL value round trip
  - **Property 5: NULL Value Round Trip**
  - **Validates: Requirements 11.1, 11.2, 11.3**
  - Verify that empty strings and NaN values convert to NULL in database and back to empty strings in API responses
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 7. Integrate database with pipeline orchestrator
  - [ ] 7.1 Modify `Backend/main.py` to import database module
    - Add import statement: `from src.database import init_database, load_all_data`
    - _Requirements: 10.5_

  - [ ] 7.2 Add `init_database()` call before Bronze layer processing
    - Insert call to `init_database()` at the start of `run_pipeline()` function
    - Ensure it runs before any Bronze layer processing
    - _Requirements: 10.3_

  - [ ] 7.3 Add `load_all_data()` call after Gold layer processing
    - Insert call to `load_all_data()` after Gold layer completes in `run_pipeline()` function
    - Ensure it runs after all CSV files are written
    - _Requirements: 10.4_

- [ ] 8. Integrate database with Backend API endpoints
  - [ ] 8.1 Modify `/vitals` endpoint in `Backend/main.py`
    - Import `query_vitals` from `src.database`
    - Replace CSV file reading logic with `query_vitals()` call
    - Maintain existing JSON response format
    - Add try-except block to return HTTP 500 on database errors
    - _Requirements: 7.1, 7.5, 7.6_

  - [ ] 8.2 Modify `/labs` endpoint in `Backend/main.py`
    - Import `query_labs` from `src.database`
    - Replace CSV file reading logic with `query_labs()` call
    - Maintain existing JSON response format
    - Add try-except block to return HTTP 500 on database errors
    - _Requirements: 7.2, 7.5, 7.6_

  - [ ] 8.3 Modify `/patient-master` endpoint in `Backend/main.py`
    - Import `query_patient_master` from `src.database`
    - Replace CSV file reading logic with `query_patient_master()` call
    - Maintain existing JSON response format
    - Add try-except block to return HTTP 500 on database errors
    - _Requirements: 7.3, 7.5, 7.6_

  - [ ] 8.4 Modify `/anomalies` endpoint in `Backend/main.py`
    - Import `query_anomalies` from `src.database`
    - Replace CSV file reading logic with `query_anomalies()` call
    - Maintain existing JSON response format
    - Add try-except block to return HTTP 500 on database errors
    - _Requirements: 7.4, 7.5, 7.6_

- [ ]* 8.5 Write property test for API response format consistency
  - **Property 8: API Response Format Consistency**
  - **Validates: Requirements 7.5**
  - Verify that JSON responses from database-backed API match the format of CSV-based implementation
  - _Requirements: 7.5_

- [x] 9. Final checkpoint - End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across randomized inputs
- Unit tests (not listed here) should cover specific examples, edge cases, and error conditions
- The database file will be created at `Backend/hospital_pipeline.db`
- All database operations use the existing `log()` utility from `src/utils.py` for consistent logging
- Connection management uses context managers (with statements) for automatic cleanup
- CSV loading uses pandas `to_sql()` for efficient batch inserts
- Dynamic schema detection for patient_master table handles arbitrary columns from CSV
