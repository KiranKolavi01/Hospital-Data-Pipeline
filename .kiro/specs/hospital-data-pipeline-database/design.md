# Design Document: Hospital Data Pipeline SQLite Database

## Overview

This design specifies a production-ready SQLite database system for the Hospital Data Pipeline. The database serves as the central data store for cleaned hospital data, replacing direct CSV file access in the FastAPI backend. The system implements an idempotent architecture where all tables are dropped and recreated on each pipeline run, ensuring data freshness without state persistence concerns.

The database module integrates seamlessly with the existing Bronze-Silver-Gold pipeline orchestrator, loading data after each processing layer completes. The Backend API will query the database instead of reading CSV files, improving performance and reliability.

Key design principles:
- Idempotent table recreation for clean state on each run
- Efficient batch loading using pandas integration
- Proper connection management with context managers
- Comprehensive error handling and logging
- Minimal changes to existing API contracts

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Pipeline Orchestrator                      │
│                      (main.py)                               │
└───────────┬─────────────────────────────────────┬───────────┘
            │                                     │
            ▼                                     ▼
┌───────────────────────┐           ┌────────────────────────┐
│   Database Manager    │           │   Backend API          │
│   (src/database.py)   │◄──────────│   (main.py endpoints)  │
└───────────┬───────────┘           └────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│              SQLite Database                               │
│         (Backend/hospital_pipeline.db)                     │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────┐│
│  │  vitals  │  │   labs   │  │patient_master│  │anomalies││
│  └──────────┘  └──────────┘  └──────────────┘  └────────┘│
└───────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Pipeline Initialization**: `run_pipeline()` calls `init_database()` to drop and recreate all tables
2. **Bronze Layer**: Raw data ingestion (no database interaction)
3. **Silver Layer**: After CSV files are written, `load_vitals()`, `load_labs()`, and `load_patient_master()` insert data
4. **Gold Layer**: After anomaly detection, `load_anomalies()` inserts results
5. **API Queries**: Backend endpoints call `query_*()` functions to retrieve data

### Integration Points

- **Pipeline Orchestrator**: Calls database initialization before Bronze layer and data loading after Gold layer
- **Backend API**: Replaces CSV file reading with database queries in all data endpoints
- **Logging**: Uses existing `log()` utility from `src/utils.py` for consistent output
- **Error Handling**: Follows existing patterns with descriptive exceptions and HTTP error responses

## Components and Interfaces

### Database Manager Module (`src/database.py`)

The central module providing all database operations.

#### Public Functions

```python
def init_database() -> None:
    """Initialize database with fresh schema (drop and recreate all tables)."""
    
def load_all_data() -> None:
    """Load all CSV data into database tables after pipeline completion."""
    
def query_vitals() -> list[dict]:
    """Query all vitals records, return as list of dicts for JSON serialization."""
    
def query_labs() -> list[dict]:
    """Query all labs records, return as list of dicts for JSON serialization."""
    
def query_patient_master() -> list[dict]:
    """Query all patient master records, return as list of dicts for JSON serialization."""
    
def query_anomalies() -> list[dict]:
    """Query all anomaly records, return as list of dicts for JSON serialization."""
```

#### Internal Functions

```python
def _get_connection() -> sqlite3.Connection:
    """Create and configure a database connection with WAL mode and timeout."""
    
def _drop_tables(conn: sqlite3.Connection) -> None:
    """Drop all tables if they exist."""
    
def _create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables with proper schema and indexes."""
    
def _detect_patient_master_columns() -> list[str]:
    """Dynamically detect columns from patient_master.csv for schema creation."""
    
def _load_vitals(conn: sqlite3.Connection) -> None:
    """Load clean_vitals.csv into vitals table."""
    
def _load_labs(conn: sqlite3.Connection) -> None:
    """Load clean_labs.csv into labs table."""
    
def _load_patient_master(conn: sqlite3.Connection) -> None:
    """Load patient_master.csv into patient_master table."""
    
def _load_anomalies(conn: sqlite3.Connection) -> None:
    """Load anomalies.csv into anomalies table."""
```

### Schema Manager

Embedded within the Database Manager, responsible for DDL operations.

#### Table Schemas

**vitals**
```sql
CREATE TABLE vitals (
    patient_id TEXT,
    timestamp TEXT,
    hr REAL,
    ox REAL,
    sys REAL,
    dia REAL
);
CREATE INDEX idx_vitals_patient ON vitals(patient_id);
```

**labs**
```sql
CREATE TABLE labs (
    patient_id TEXT,
    timestamp TEXT,
    lab_test TEXT,
    lab_value REAL
);
CREATE INDEX idx_labs_patient ON labs(patient_id);
```

**patient_master**
```sql
CREATE TABLE patient_master (
    patient_id TEXT PRIMARY KEY,
    -- EHR columns (dynamically detected)
    -- Latest vitals columns: hr, ox, sys, dia
    -- Lab columns: lab_<test_name> (dynamically detected)
);
CREATE INDEX idx_patient_master_patient ON patient_master(patient_id);
```

**anomalies**
```sql
CREATE TABLE anomalies (
    patient_id TEXT,
    anomaly_type TEXT,
    value REAL,
    timestamp TEXT
);
CREATE INDEX idx_anomalies_patient ON anomalies(patient_id);
```

### CSV Loader

Embedded within the Database Manager, responsible for data loading.

#### Loading Strategy

- Use pandas `read_csv()` to load CSV files
- Use pandas `to_sql()` with `if_exists='append'` for batch inserts
- Convert NaN values to NULL during insertion
- Log warnings for missing files without stopping pipeline
- Use transactions for atomic operations

### Connection Manager

Handles SQLite connection lifecycle.

#### Configuration

- Database path: `Backend/hospital_pipeline.db`
- Journal mode: WAL (Write-Ahead Logging) for concurrent reads
- Connection timeout: 30 seconds
- Context manager pattern for automatic cleanup

## Data Models

### Vitals Table

Stores cleaned patient vital signs with temporal data.

| Column      | Type | Constraints | Description                    |
|-------------|------|-------------|--------------------------------|
| patient_id  | TEXT | NOT NULL    | Patient identifier             |
| timestamp   | TEXT | NOT NULL    | ISO 8601 datetime string       |
| hr          | REAL | NULL OK     | Heart rate (bpm)               |
| ox          | REAL | NULL OK     | Oxygen saturation (%)          |
| sys         | REAL | NULL OK     | Systolic blood pressure (mmHg) |
| dia         | REAL | NULL OK     | Diastolic blood pressure (mmHg)|

**Index**: `idx_vitals_patient` on `patient_id` for efficient patient lookups

### Labs Table

Stores cleaned laboratory test results in long format.

| Column      | Type | Constraints | Description                    |
|-------------|------|-------------|--------------------------------|
| patient_id  | TEXT | NOT NULL    | Patient identifier             |
| timestamp   | TEXT | NOT NULL    | ISO 8601 datetime string       |
| lab_test    | TEXT | NOT NULL    | Laboratory test name           |
| lab_value   | REAL | NULL OK     | Numeric test result            |

**Index**: `idx_labs_patient` on `patient_id` for efficient patient lookups

### Patient Master Table

Stores one row per patient with demographics, latest vitals, and latest lab results.

| Column      | Type | Constraints | Description                           |
|-------------|------|-------------|---------------------------------------|
| patient_id  | TEXT | PRIMARY KEY | Patient identifier                    |
| (EHR fields)| TEXT | NULL OK     | Demographics from EHR (age, gender, etc.) |
| hr          | REAL | NULL OK     | Latest heart rate                     |
| ox          | REAL | NULL OK     | Latest oxygen saturation              |
| sys         | REAL | NULL OK     | Latest systolic BP                    |
| dia         | REAL | NULL OK     | Latest diastolic BP                   |
| lab_*       | REAL | NULL OK     | Latest value per lab test (dynamic)   |

**Dynamic Schema**: The exact columns are detected from `patient_master.csv` at runtime. EHR fields and lab columns vary based on source data.

**Index**: `idx_patient_master_patient` on `patient_id` (redundant with PRIMARY KEY but explicit)

### Anomalies Table

Stores detected clinical anomalies for alerting.

| Column        | Type | Constraints | Description                              |
|---------------|------|-------------|------------------------------------------|
| patient_id    | TEXT | NOT NULL    | Patient identifier                       |
| anomaly_type  | TEXT | NOT NULL    | Type: high_heart_rate, low_oxygen, high_bp |
| value         | REAL | NOT NULL    | The measurement value that triggered alert |
| timestamp     | TEXT | NOT NULL    | ISO 8601 datetime when anomaly occurred  |

**Index**: `idx_anomalies_patient` on `patient_id` for efficient patient lookups

### NULL Handling

- Empty strings in CSV files are converted to NULL in database
- Pandas NaN values are converted to NULL in database
- API responses convert NULL back to empty strings for frontend compatibility
- Numeric columns (REAL type) store NULL for missing measurements
- Text columns store NULL for missing identifiers or labels


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Idempotent Table Initialization

*For any* database state (empty or with existing tables), calling `init_database()` multiple times should result in empty tables with correct schema, without errors.

**Validates: Requirements 2.1, 2.3**

### Property 2: CSV to Database Row Preservation

*For any* valid CSV file (vitals, labs, patient_master, or anomalies), after loading into the database, the number of rows in the corresponding table should equal the number of rows in the CSV file.

**Validates: Requirements 3.2, 4.2, 5.4, 6.2**

### Property 3: Data Type Preservation

*For any* loaded data across all tables, querying the database should return values with the correct types: TEXT columns as strings, REAL columns as floats, and NULL for missing values.

**Validates: Requirements 3.3, 4.3, 6.3, 11.4, 11.5**

### Property 4: Dynamic Schema Matching

*For any* patient_master.csv with arbitrary columns, the created patient_master table schema should include all columns from the CSV with appropriate data types.

**Validates: Requirements 5.2, 5.3**

### Property 5: NULL Value Round Trip

*For any* CSV file containing empty strings or NaN values, after loading into the database and querying via the API, empty strings should be converted to NULL in the database and back to empty strings in JSON responses.

**Validates: Requirements 11.1, 11.2, 11.3**

### Property 6: Missing File Graceful Handling

*For any* missing CSV file (vitals, labs, patient_master, or anomalies), the loader should log a warning and continue without raising an exception, allowing the pipeline to complete.

**Validates: Requirements 3.4, 4.4, 5.5, 6.4, 9.3**

### Property 7: Connection Cleanup

*For any* database operation (query or write), after completion, the database connection should be closed and resources released.

**Validates: Requirements 8.2**

### Property 8: API Response Format Consistency

*For any* table data, the JSON response from the API should match the format of the previous CSV-based implementation (list of dictionaries with same keys and value types).

**Validates: Requirements 7.5**

## Error Handling

### Database Connection Errors

- **Timeout Configuration**: All connections set a 30-second timeout to prevent indefinite hangs
- **Connection Failure**: Log error with full stack trace and raise exception to stop pipeline
- **File Lock Errors**: SQLite WAL mode reduces lock contention; if locks occur, retry with exponential backoff (up to 3 attempts)

### Schema Creation Errors

- **Table Creation Failure**: Log error with SQL statement and exception details, raise exception to stop pipeline
- **Index Creation Failure**: Log error but continue (indexes are performance optimization, not critical for correctness)
- **Dynamic Column Detection Failure**: If patient_master.csv cannot be read, log error and skip patient_master table creation

### Data Loading Errors

- **Missing CSV File**: Log warning with file path, continue pipeline execution (allows partial data loading)
- **CSV Parse Error**: Log error with file path and line number, skip that file, continue pipeline
- **Type Conversion Error**: Log warning with row details, insert NULL for invalid values, continue loading
- **Constraint Violation**: Log error with row details, skip that row, continue loading remaining rows

### Query Errors

- **Table Not Found**: Return HTTP 404 with message "Data not available. Run pipeline first."
- **SQL Syntax Error**: Log error with query details, return HTTP 500 with generic error message
- **Connection Timeout**: Log error, return HTTP 503 with message "Database temporarily unavailable"

### Logging Strategy

All errors use the existing `log()` utility from `src/utils.py`:

```python
from src.utils import log

# Success logging
log(f"Created table: {table_name}")
log(f"Loaded {row_count} rows into {table_name}")

# Warning logging
log(f"CSV file not found: {file_path}", level="warning")

# Error logging
log(f"Database operation failed: {operation}\n{traceback.format_exc()}", level="error")
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, integration points, and error conditions
- **Property tests**: Verify universal properties across all inputs using randomized data generation

### Unit Testing Focus

Unit tests should cover:

1. **Schema Validation**: Verify exact table structures match specifications (Requirements 1.3-1.6)
2. **Integration Points**: Test pipeline orchestrator calls database functions in correct order (Requirements 10.3-10.5)
3. **Error Conditions**: Test missing files, connection failures, schema errors (Requirements 8.4, 9.4)
4. **Edge Cases**: Empty CSV files, single-row files, files with only headers
5. **Configuration**: Verify WAL mode, timeout settings, index creation (Requirements 1.7, 8.5, 12.5)
6. **Performance Benchmarks**: Measure loading and query times against thresholds (Requirements 12.1, 12.2)

Example unit tests:
- `test_init_database_creates_all_tables()`: Verify 4 tables exist after initialization
- `test_vitals_table_schema()`: Verify exact column names and types
- `test_missing_csv_logs_warning()`: Verify warning logged when CSV missing
- `test_api_returns_500_on_query_error()`: Verify error handling in endpoints

### Property-Based Testing Focus

Property tests should verify universal behaviors across randomized inputs:

1. **Idempotency**: Multiple init calls produce same result (Property 1)
2. **Data Preservation**: Row counts match between CSV and database (Property 2)
3. **Type Preservation**: Data types maintained through load/query cycle (Property 3)
4. **Dynamic Schema**: Table schema matches arbitrary CSV columns (Property 4)
5. **NULL Handling**: Round-trip conversion of empty/NaN/NULL values (Property 5)
6. **Graceful Degradation**: Missing files don't crash pipeline (Property 6)
7. **Resource Cleanup**: Connections closed after operations (Property 7)
8. **Format Consistency**: API responses match expected format (Property 8)

### Property-Based Testing Library

**Python**: Use `hypothesis` library for property-based testing

```python
from hypothesis import given, strategies as st
import hypothesis.extra.pandas as pdst

@given(pdst.data_frames(columns=[
    pdst.column('patient_id', dtype=str),
    pdst.column('hr', dtype=float),
    # ... more columns
]))
def test_csv_to_database_row_preservation(df):
    """Property 2: CSV row count equals database row count."""
    # Feature: hospital-data-pipeline-database, Property 2: CSV to Database Row Preservation
    # Save df to CSV, load to database, verify row counts match
    ...
```

### Test Configuration

- **Property test iterations**: Minimum 100 iterations per test (due to randomization)
- **Test data generators**: Use hypothesis strategies for DataFrames with various column types
- **Tag format**: Each property test must include comment: `# Feature: hospital-data-pipeline-database, Property {number}: {property_text}`

### Test Organization

```
Backend/tests/
├── test_database_unit.py          # Unit tests for database operations
├── test_database_properties.py    # Property-based tests
├── test_api_integration.py        # API endpoint integration tests
└── fixtures/
    ├── sample_vitals.csv
    ├── sample_labs.csv
    └── sample_patient_master.csv
```

### Testing Best Practices

1. **Isolation**: Each test should create a fresh database file in a temp directory
2. **Cleanup**: Use pytest fixtures to ensure database files are deleted after tests
3. **Mocking**: Mock the `log()` function to verify logging behavior without console spam
4. **Determinism**: Use hypothesis seed for reproducible property test failures
5. **Coverage**: Aim for 90%+ code coverage on database.py module

### Manual Testing

After implementation, manually verify:

1. Run full pipeline and check database file exists at correct path
2. Query each API endpoint and verify JSON responses
3. Delete CSV files and verify pipeline continues with warnings
4. Check database file size is reasonable (not bloated)
5. Verify frontend still works with database-backed API
