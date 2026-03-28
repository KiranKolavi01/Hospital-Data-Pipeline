import sqlite3
import pandas as pd
import os

# Database configuration
DB_NAME = "hospital.db"

def get_connection():
    """Returns a connection to the SQLite database with foreign keys enabled."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Drops and recreates all tables for an idempotent pipeline."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Drop existing tables
    tables = ["vitals", "labs", "patient_master", "anomalies"]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Create Table: vitals
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
    
    # Create Table: labs
    cursor.execute("""
        CREATE TABLE labs (
            patient_id TEXT,
            timestamp TEXT,
            lab_test TEXT,
            lab_value REAL
        )
    """)
    
    # Table: patient_master
    # Note: patient_id is PRIMARY KEY here
    # Dynamic columns will be handled during to_sql by pandas if needed, 
    # but we'll define a base schema.
    cursor.execute("""
        CREATE TABLE patient_master (
            patient_id TEXT PRIMARY KEY,
            hr REAL,
            ox REAL,
            sys REAL,
            dia REAL
        )
    """)
    
    # Create Table: anomalies
    cursor.execute("""
        CREATE TABLE anomalies (
            patient_id TEXT,
            anomaly_type TEXT,
            value REAL,
            timestamp TEXT
        )
    """)
    
    # Add indexes for performance (Bonus)
    cursor.execute("CREATE INDEX idx_vitals_patient_id ON vitals(patient_id)")
    cursor.execute("CREATE INDEX idx_labs_patient_id ON labs(patient_id)")
    cursor.execute("CREATE INDEX idx_anomalies_patient_id ON anomalies(patient_id)")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def load_vitals(conn, file_path):
    """Loads clean vitals data from CSV to SQLite."""
    try:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found.")
            return
        
        df = pd.read_csv(file_path)
        df.to_sql("vitals", conn, if_exists="append", index=False)
        print("Vitals loaded successfully")
    except Exception as e:
        print(f"Error loading vitals: {e}")

def load_labs(conn, file_path):
    """Loads clean labs data from CSV to SQLite."""
    try:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found.")
            return
        
        df = pd.read_csv(file_path)
        df.to_sql("labs", conn, if_exists="append", index=False)
        print("Labs loaded successfully")
    except Exception as e:
        print(f"Error loading labs: {e}")

def load_patient_master(conn, file_path):
    """Loads patient master data with dynamic columns from CSV to SQLite."""
    try:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found.")
            return
        
        df = pd.read_csv(file_path)
        # Using if_exists="replace" here or handling it carefully because 
        # patient_master is defined with PK, but pandas might overwrite schema.
        # Since init_db already created it, 'append' is safer, 
        # but the request mentions "Include all EHR fields dynamically".
        # pandas to_sql handles dynamic columns best with 'replace' or 'append' if schema is pre-defined.
        # To strictly follow "include all EHR fields dynamically", we'll let pandas manage the schema for this table.
        df.to_sql("patient_master", conn, if_exists="replace", index=False)
        
        # Re-add PK constraint if we replaced the table (SQLite to_sql doesn't support PK directly)
        # Or better: create the table with PK first, then append. 
        # However, "dynamically include" suggests we don't know the columns beforehand.
        print("Patient Master loaded successfully (with dynamic columns)")
    except Exception as e:
        print(f"Error loading patient master: {e}")

def load_anomalies(conn, file_path):
    """Loads anomaly data from CSV to SQLite."""
    try:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found.")
            return
        
        df = pd.read_csv(file_path)
        df.to_sql("anomalies", conn, if_exists="append", index=False)
        print("Anomalies loaded successfully")
    except Exception as e:
        print(f"Error loading anomalies: {e}")

def main_loader():
    """Main orchestration function to initialize DB and load all data."""
    try:
        init_db()
        
        conn = get_connection()
        
        # Load Silver layer data
        load_vitals(conn, "silver/clean_vitals.csv")
        load_labs(conn, "silver/clean_labs.csv")
        load_patient_master(conn, "silver/patient_master.csv")
        
        # Load Gold layer data
        load_anomalies(conn, "gold/anomalies.csv")
        
        conn.close()
        print("Full pipeline data loading completed.")
        
    except Exception as e:
        print(f"Critical error in main_loader: {e}")

if __name__ == "__main__":
    main_loader()
    
    # Sample SQL queries (Bonus)
    conn = get_connection()
    print("\n--- Summary: Anomalies per Patient ---")
    query = """
    SELECT patient_id, COUNT(*) as report_count 
    FROM anomalies 
    GROUP BY patient_id
    """
    try:
        summary = pd.read_sql(query, conn)
        print(summary)
    except Exception as e:
        print(f"Error running sample query: {e}")
    finally:
        conn.close()
