import os
import sqlite3
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)


def migrate_sqlite():
    db_path = os.path.join(BASE_DIR, 'antimatrix.db')
    if not os.path.exists(db_path):
        print(f"[MIGRATION] Database not found at {db_path}, will be created by create_all().")
        return

    print(f"[MIGRATION] Connecting to SQLite database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. job_postings: check 'duration'
    cursor.execute("PRAGMA table_info(job_postings)")
    job_columns = [row[1] for row in cursor.fetchall()]
    if 'duration' not in job_columns:
        print("[MIGRATION] Adding 'duration' column to job_postings...")
        cursor.execute("ALTER TABLE job_postings ADD COLUMN duration VARCHAR(50) DEFAULT NULL")
        conn.commit()

    # 2. job_applications: check questionnaire and payment columns
    cursor.execute("PRAGMA table_info(job_applications)")
    app_columns = [row[1] for row in cursor.fetchall()]

    new_app_cols = [
        ('application_code', 'VARCHAR(50) DEFAULT NULL'),
        ('first_name', 'VARCHAR(80) DEFAULT NULL'),
        ('last_name', 'VARCHAR(80) DEFAULT NULL'),
        ('address', 'TEXT DEFAULT NULL'),
        ('state', 'VARCHAR(100) DEFAULT NULL'),
        ('city', 'VARCHAR(100) DEFAULT NULL'),
        ('pincode', 'VARCHAR(20) DEFAULT NULL'),
        ('education_level', 'VARCHAR(100) DEFAULT NULL'),
        ('major', 'VARCHAR(100) DEFAULT NULL'),
        ('year_of_study', 'VARCHAR(50) DEFAULT NULL'),
        ('current_cgpa', 'FLOAT DEFAULT NULL'),
        ('aadhaar_filename', 'VARCHAR(255) DEFAULT NULL'),
        ('aadhaar_path', 'VARCHAR(255) DEFAULT NULL'),
        ('pan_filename', 'VARCHAR(255) DEFAULT NULL'),
        ('pan_path', 'VARCHAR(255) DEFAULT NULL'),
        ('college_id_filename', 'VARCHAR(255) DEFAULT NULL'),
        ('college_id_path', 'VARCHAR(255) DEFAULT NULL'),
        ('duration', 'VARCHAR(50) DEFAULT NULL'),
        ('application_fee', 'INTEGER DEFAULT 0'),
        ('payment_status', "VARCHAR(30) DEFAULT 'pending'"),
        ('application_status', "VARCHAR(30) DEFAULT 'pending_payment'")
    ]

    for col_name, col_def in new_app_cols:
        if col_name not in app_columns:
            print(f"[MIGRATION] Adding '{col_name}' column to job_applications...")
            cursor.execute(f"ALTER TABLE job_applications ADD COLUMN {col_name} {col_def}")
            conn.commit()

    # Populate existing application codes if missing
    cursor.execute("SELECT id, application_code FROM job_applications WHERE application_code IS NULL OR application_code = ''")
    rows = cursor.fetchall()
    for r_id, _ in rows:
        code = f"AM-APP-{r_id:06d}"
        cursor.execute("UPDATE job_applications SET application_code = ? WHERE id = ?", (code, r_id))
    conn.commit()

    conn.close()
    print("[MIGRATION] Raw SQLite migration completed successfully.")


if __name__ == '__main__':
    migrate_sqlite()
    from app import create_app
    from models import db
    app = create_app('development')
    with app.app_context():
        db.create_all()
        print("[MIGRATION] SQLAlchemy tables verified.")

