"""
Hospital Data Pipeline SQLite Database Module

This module provides database operations for the Hospital Data Pipeline:
- Schema management (create/drop tables)
- CSV data loading (vitals, labs, patient_master, anomalies)
- Query functions for Backend API integration

All tables are dropped and recreated on each pipeline run (idempotent design).
"""

import sqlite3
import pandas as pd
from pathlib import Path
import traceback
from typing import List, Dict, Any, Optional


# Database configuration
DB_PATH = Path(__file__).parent.parent / "hospital_pipeline.db"
CONNECTION_TIMEOUT = 30

# Path to CSV files
BACKEND_ROOT = Path(__file__).parent.parent


def log(message: str, level: str = "info") -> None:
    """
    Logging utility function.
    
    Args:
        message: Log message
        level: Log level (info, warning, error)
    """
    prefix = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌"
    }.get(level, "ℹ️")
    
    print(f"{prefix} {message}")


def _get_connection() -> sqlite3.Connection:
    """
    Create and configure a database connection.
    
    Returns:
        Configured SQLite connection with WAL mode and timeout
    """
    try:
        conn = sqlite3.Connection(str(DB_PATH), timeout=CONNECTION_TIMEOUT)
        
        # Enable WAL mode for concurrent reads during writes
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Enable foreign keys (if needed in future)
        conn.execute("PRAGMA foreign_keys=ON")
        
        return conn
        
    except Exception as e:
        log(f"Database connection failed: {str(e)}\n{traceback.format_exc()}", level="error")
        raise



def _drop_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all tables if they exist.
    
    Args:
        conn: SQLite database connection
    """
    # Note: pipeline_runs is NOT dropped - it's an append-only audit log
    tables = ["vitals", "labs", "patient_master", "anomalies", "risk_scores", "trend_alerts"]
    
    try:
        cursor = conn.cursor()
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            log(f"Dropped table (if existed): {table}")
        
        conn.commit()
        
    except Exception as e:
        log(f"Failed to drop tables: {str(e)}\n{traceback.format_exc()}", level="error")
        raise



def _detect_patient_master_columns() -> List[tuple]:
    """
    Dynamically detect columns from patient_master.csv for schema creation.
    
    Returns:
        List of (column_name, sql_type) tuples
    """
    csv_path = BACKEND_ROOT / "silver" / "patient_master.csv"
    
    try:
        if not csv_path.exists():
            log(f"patient_master.csv not found at {csv_path}, using default schema", level="warning")
            return [
                ("patient_id", "TEXT PRIMARY KEY"),
                ("hr", "REAL"),
                ("ox", "REAL"),
                ("sys", "REAL"),
                ("dia", "REAL")
            ]
        
        # Read CSV to detect columns
        df = pd.read_csv(csv_path, nrows=0)  # Read only headers
        columns = []
        
        for col in df.columns:
            if col == "patient_id":
                columns.append((col, "TEXT PRIMARY KEY"))
            else:
                # Infer type from column name patterns
                if any(keyword in col.lower() for keyword in ["id", "name", "type", "test"]):
                    columns.append((col, "TEXT"))
                else:
                    columns.append((col, "REAL"))
        
        log(f"Detected {len(columns)} columns from patient_master.csv")
        return columns
        
    except Exception as e:
        log(f"Failed to detect patient_master columns: {str(e)}", level="warning")
        # Return default schema
        return [
            ("patient_id", "TEXT PRIMARY KEY"),
            ("hr", "REAL"),
            ("ox", "REAL"),
            ("sys", "REAL"),
            ("dia", "REAL")
        ]



def _create_tables(conn: sqlite3.Connection) -> None:
    """
    Create all tables with proper schema and indexes.
    
    Args:
        conn: SQLite database connection
    """
    try:
        cursor = conn.cursor()
        
        # Create vitals table
        cursor.execute("""
            CREATE TABLE vitals (
                patient_id TEXT,
                timestamp TEXT,
                hr REAL,
                ox REAL,
                sys REAL,
                dia REAL
            )
        """)
        cursor.execute("CREATE INDEX idx_vitals_patient ON vitals(patient_id)")
        log("Created table: vitals")
        
        # Create labs table
        cursor.execute("""
            CREATE TABLE labs (
                patient_id TEXT,
                timestamp TEXT,
                lab_test TEXT,
                lab_value REAL
            )
        """)
        cursor.execute("CREATE INDEX idx_labs_patient ON labs(patient_id)")
        log("Created table: labs")
        
        # Create patient_master table with dynamic columns
        patient_master_columns = _detect_patient_master_columns()
        columns_sql = ", ".join([f"{col} {dtype}" for col, dtype in patient_master_columns])
        
        cursor.execute(f"""
            CREATE TABLE patient_master (
                {columns_sql}
            )
        """)
        cursor.execute("CREATE INDEX idx_patient_master_patient ON patient_master(patient_id)")
        log("Created table: patient_master")
        
        # Create anomalies table
        cursor.execute("""
            CREATE TABLE anomalies (
                patient_id TEXT,
                anomaly_type TEXT,
                value REAL,
                timestamp TEXT
            )
        """)
        cursor.execute("CREATE INDEX idx_anomalies_patient ON anomalies(patient_id)")
        log("Created table: anomalies")
        
        # Create risk_scores table
        cursor.execute("""
            CREATE TABLE risk_scores (
                patient_id TEXT,
                risk_score REAL,
                risk_level TEXT,
                anomaly_count INTEGER,
                last_anomaly_timestamp TEXT
            )
        """)
        cursor.execute("CREATE INDEX idx_risk_scores_patient ON risk_scores(patient_id)")
        log("Created table: risk_scores")
        
        # Create trend_alerts table
        cursor.execute("""
            CREATE TABLE trend_alerts (
                patient_id TEXT,
                vital TEXT,
                reading_1 REAL,
                reading_2 REAL,
                reading_3 REAL,
                direction TEXT,
                trend_label TEXT,
                timestamp_1 TEXT,
                timestamp_2 TEXT,
                timestamp_3 TEXT,
                already_critical INTEGER
            )
        """)
        cursor.execute("CREATE INDEX idx_trend_alerts_patient ON trend_alerts(patient_id)")
        log("Created table: trend_alerts")
        
        # Create pipeline_runs table (append-only audit log - never dropped)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT,
                finished_at TEXT,
                duration_seconds REAL,
                bronze_ehr_count INTEGER,
                bronze_vitals_count INTEGER,
                bronze_labs_count INTEGER,
                silver_vitals_count INTEGER,
                silver_labs_count INTEGER,
                silver_patient_master_count INTEGER,
                gold_anomalies_count INTEGER,
                gold_risk_scores_count INTEGER,
                silver_trends_count INTEGER,
                new_alerts_count INTEGER DEFAULT 0,
                status TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started ON pipeline_runs(started_at)")
        log("Created table: pipeline_runs (if not exists)")
        
        # Migrate: add new_alerts_count column if it doesn't exist yet (for existing databases)
        try:
            cursor.execute("ALTER TABLE pipeline_runs ADD COLUMN new_alerts_count INTEGER DEFAULT 0")
            log("Migrated pipeline_runs: added new_alerts_count column")
        except Exception:
            pass  # Column already exists, ignore
        
        # Create alert_log table (append-only permanent log - never dropped)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_log (
                alert_id TEXT PRIMARY KEY,
                patient_id TEXT,
                anomaly_type TEXT,
                value TEXT,
                timestamp TEXT,
                detected_at TEXT,
                run_id TEXT,
                is_new INTEGER
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_log_detected ON alert_log(detected_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_log_run ON alert_log(run_id)")
        log("Created table: alert_log (if not exists)")

        conn.commit()
        
    except Exception as e:
        log(f"Failed to create tables: {str(e)}\n{traceback.format_exc()}", level="error")
        raise



def init_database() -> None:
    """
    Initialize database with fresh schema (drop and recreate all tables).
    
    This function is idempotent - calling it multiple times produces the same result.
    """
    try:
        log("Initializing database...")
        
        conn = _get_connection()
        
        try:
            _drop_tables(conn)
            _create_tables(conn)
            log("✅ Database initialized successfully")
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Database initialization failed: {str(e)}", level="error")
        raise



def _load_vitals(conn: sqlite3.Connection) -> None:
    """
    Load clean_vitals.csv into vitals table.
    
    Args:
        conn: SQLite database connection
    """
    csv_path = BACKEND_ROOT / "silver" / "clean_vitals.csv"
    
    try:
        if not csv_path.exists():
            log(f"clean_vitals.csv not found at {csv_path}, skipping", level="warning")
            return
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Replace NaN with None (NULL in database)
        df = df.where(pd.notnull(df), None)
        
        # Load into database
        df.to_sql("vitals", conn, if_exists="append", index=False)
        
        log(f"Loaded {len(df)} rows into vitals table")
        
    except Exception as e:
        log(f"Failed to load vitals: {str(e)}", level="warning")


def _load_labs(conn: sqlite3.Connection) -> None:
    """
    Load clean_labs.csv into labs table.
    
    Args:
        conn: SQLite database connection
    """
    csv_path = BACKEND_ROOT / "silver" / "clean_labs.csv"
    
    try:
        if not csv_path.exists():
            log(f"clean_labs.csv not found at {csv_path}, skipping", level="warning")
            return
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Replace NaN with None (NULL in database)
        df = df.where(pd.notnull(df), None)
        
        # Load into database
        df.to_sql("labs", conn, if_exists="append", index=False)
        
        log(f"Loaded {len(df)} rows into labs table")
        
    except Exception as e:
        log(f"Failed to load labs: {str(e)}", level="warning")


def _load_patient_master(conn: sqlite3.Connection) -> None:
    """
    Load patient_master.csv into patient_master table.
    
    Args:
        conn: SQLite database connection
    """
    csv_path = BACKEND_ROOT / "silver" / "patient_master.csv"
    
    try:
        if not csv_path.exists():
            log(f"patient_master.csv not found at {csv_path}, skipping", level="warning")
            return
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Replace NaN with None (NULL in database)
        df = df.where(pd.notnull(df), None)
        
        # Load into database
        df.to_sql("patient_master", conn, if_exists="append", index=False)
        
        log(f"Loaded {len(df)} rows into patient_master table")
        
    except Exception as e:
        log(f"Failed to load patient_master: {str(e)}", level="warning")


def _load_anomalies(conn: sqlite3.Connection) -> None:
    """
    Load anomalies.csv into anomalies table.
    
    Args:
        conn: SQLite database connection
    """
    csv_path = BACKEND_ROOT / "gold" / "anomalies.csv"
    
    try:
        if not csv_path.exists():
            log(f"anomalies.csv not found at {csv_path}, skipping", level="warning")
            return
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Replace NaN with None (NULL in database)
        df = df.where(pd.notnull(df), None)
        
        # Load into database
        df.to_sql("anomalies", conn, if_exists="append", index=False)
        
        log(f"Loaded {len(df)} rows into anomalies table")
        
    except Exception as e:
        log(f"Failed to load anomalies: {str(e)}", level="warning")


def _load_risk_scores(conn: sqlite3.Connection) -> None:
    """
    Load risk_scores.csv into risk_scores table.
    
    Args:
        conn: SQLite database connection
    """
    csv_path = BACKEND_ROOT / "gold" / "risk_scores.csv"
    
    try:
        if not csv_path.exists():
            log(f"risk_scores.csv not found at {csv_path}, skipping", level="warning")
            return
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Replace NaN with None (NULL in database)
        df = df.where(pd.notnull(df), None)
        
        # Load into database
        df.to_sql("risk_scores", conn, if_exists="append", index=False)
        
        log(f"Loaded {len(df)} rows into risk_scores table")
        
    except Exception as e:
        log(f"Failed to load risk_scores: {str(e)}", level="warning")


def _load_trend_alerts(conn: sqlite3.Connection) -> None:
    """
    Load trend_alerts.csv into trend_alerts table.
    
    Args:
        conn: SQLite database connection
    """
    csv_path = BACKEND_ROOT / "silver" / "trend_alerts.csv"
    
    try:
        if not csv_path.exists():
            log(f"trend_alerts.csv not found at {csv_path}, skipping", level="warning")
            return
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Replace NaN with None (NULL in database)
        df = df.where(pd.notnull(df), None)
        
        # Load into database
        df.to_sql("trend_alerts", conn, if_exists="append", index=False)
        
        log(f"Loaded {len(df)} rows into trend_alerts table")
        
    except Exception as e:
        log(f"Failed to load trend_alerts: {str(e)}", level="warning")


def load_all_data() -> None:
    """
    Load all CSV data into database tables after pipeline completion.
    """
    try:
        log("Loading data into database...")
        
        conn = _get_connection()
        
        try:
            _load_vitals(conn)
            _load_labs(conn)
            _load_patient_master(conn)
            _load_anomalies(conn)
            _load_risk_scores(conn)
            _load_trend_alerts(conn)
            
            conn.commit()
            log("✅ All data loaded successfully")
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Data loading failed: {str(e)}", level="error")
        raise



def query_vitals() -> List[Dict[str, Any]]:
    """
    Query all vitals records.
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vitals")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query vitals: {str(e)}\n{traceback.format_exc()}", level="error")
        raise


def query_labs() -> List[Dict[str, Any]]:
    """
    Query all labs records.
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM labs")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query labs: {str(e)}\n{traceback.format_exc()}", level="error")
        raise


def query_patient_master() -> List[Dict[str, Any]]:
    """
    Query all patient master records.
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patient_master")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query patient_master: {str(e)}\n{traceback.format_exc()}", level="error")
        raise


def query_anomalies() -> List[Dict[str, Any]]:
    """
    Query all anomaly records.
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM anomalies")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query anomalies: {str(e)}\n{traceback.format_exc()}", level="error")
        raise


def query_risk_scores() -> List[Dict[str, Any]]:
    """
    Query all risk_scores records.
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM risk_scores")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query risk_scores: {str(e)}\n{traceback.format_exc()}", level="error")
        raise




def query_trend_alerts() -> List[Dict[str, Any]]:
    """
    Query all trend_alerts records.
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trend_alerts")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query trend_alerts: {str(e)}\n{traceback.format_exc()}", level="error")
        raise



def query_pipeline_runs() -> List[Dict[str, Any]]:
    """
    Query all pipeline run records ordered by started_at descending (most recent first).
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs ORDER BY started_at DESC")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query pipeline_runs: {str(e)}\n{traceback.format_exc()}", level="error")
        # Return empty list if table doesn't exist yet
        return []



def query_alert_log() -> List[Dict[str, Any]]:
    """
    Query all alert log records ordered by detected_at descending (most recent first).
    
    Returns:
        List of dictionaries for JSON serialization
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alert_log ORDER BY detected_at DESC")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of dicts
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert NULL to empty string for JSON compatibility
                    value = row[i]
                    row_dict[col] = "" if value is None else value
                result.append(row_dict)
            
            return result
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query alert_log: {str(e)}\n{traceback.format_exc()}", level="error")
        # Return empty list if table doesn't exist yet
        return []


def query_new_alerts_count() -> Dict[str, Any]:
    """
    Query the count of new alerts from the most recent pipeline run.
    
    Returns:
        Dictionary with count and run_id
    """
    try:
        conn = _get_connection()
        
        try:
            cursor = conn.cursor()
            
            # Get most recent run_id
            cursor.execute("SELECT run_id FROM pipeline_runs ORDER BY started_at DESC LIMIT 1")
            run_id_row = cursor.fetchone()
            
            if not run_id_row:
                return {"count": 0, "run_id": None}
            
            current_run_id = run_id_row[0]
            
            # Count alerts from this run
            cursor.execute("SELECT COUNT(*) FROM alert_log WHERE run_id = ?", (current_run_id,))
            count_row = cursor.fetchone()
            count = count_row[0] if count_row else 0
            
            return {"count": count, "run_id": current_run_id}
            
        finally:
            conn.close()
            
    except Exception as e:
        log(f"Failed to query new alerts count: {str(e)}\n{traceback.format_exc()}", level="error")
        # Return zero count if table doesn't exist yet
        return {"count": 0, "run_id": None}
