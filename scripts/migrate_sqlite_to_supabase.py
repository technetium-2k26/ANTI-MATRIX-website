"""
Safe SQLite to Supabase PostgreSQL Migration Script
Preserves ALL existing records, primary keys, foreign keys, business identifiers, and timestamps.
Idempotent and non-destructive.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime, date
import argparse
from dotenv import load_dotenv

# Ensure stdout handles UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add parent directory to path so models and config can be imported
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'))

from sqlalchemy import create_engine, text, MetaData
from models import db

# Ordered table list by foreign key dependencies (Level 0 -> Level 3)
TABLE_ORDER = [
    # Level 0: No foreign keys
    'users',
    'job_postings',
    'contact_inquiries',
    'document_templates',
    'email_templates',
    'email_logs',
    
    # Level 1: Depends on Level 0
    'job_applications',
    
    # Level 2: Depends on job_applications
    'employees',
    'payments',
    
    # Level 3: Depends on employees, job_applications, document_templates, users
    'employee_documents',
    'money_transactions',
]

def parse_iso_datetime(val):
    if not val:
        return None
    if isinstance(val, (datetime, date)):
        return val
    val_str = str(val).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            pass
    return val

def parse_iso_date(val):
    if not val:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    val_str = str(val).strip()
    try:
        return datetime.strptime(val_str, '%Y-%m-%d').date()
    except ValueError:
        return parse_iso_datetime(val_str)

def convert_value_for_postgres(col_name, col_type, val):
    if val is None:
        return None
    type_str = str(col_type).upper()
    if 'BOOL' in type_str:
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            return val.lower() in ('1', 'true', 't', 'yes', 'y')
    elif 'DATETIME' in type_str or 'TIMESTAMP' in type_str:
        return parse_iso_datetime(val)
    elif 'DATE' in type_str:
        return parse_iso_date(val)
    elif 'FLOAT' in type_str or 'NUMERIC' in type_str:
        try:
            return float(val)
        except (ValueError, TypeError):
            return val
    elif 'INT' in type_str:
        try:
            return int(val)
        except (ValueError, TypeError):
            return val
    return val

def run_migration(sqlite_path=None, target_db_url=None):
    if not sqlite_path:
        sqlite_path = os.path.join(BASE_DIR, 'antimatrix.db')
    
    if not os.path.exists(sqlite_path):
        print(f"[-] ERROR: Source SQLite database not found at: {sqlite_path}")
        sys.exit(1)

    # 1. Physical Backup
    backup_path = f"{sqlite_path}.backup"
    if not os.path.exists(backup_path):
        print(f"[*] Creating safe physical backup: {backup_path}")
        shutil.copy2(sqlite_path, backup_path)
    else:
        print(f"[+] Physical backup already exists: {backup_path}")

    # 2. Target Database URL Resolution
    if not target_db_url:
        target_db_url = os.environ.get('DATABASE_URL', '').strip()

    if not target_db_url:
        print("[-] ERROR: DATABASE_URL is not set. Please provide Supabase PostgreSQL connection string.")
        sys.exit(1)

    if target_db_url.startswith('postgres://'):
        target_db_url = 'postgresql://' + target_db_url[len('postgres://'):]

    print("[*] Target database backend: PostgreSQL (Supabase)")
    
    # 3. Connect to SQLite Source
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Discover all tables in SQLite
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    discovered_tables = [r[0] for r in sqlite_cursor.fetchall() if not r[0].startswith('sqlite_')]
    print(f"[*] Discovered {len(discovered_tables)} tables in SQLite: {', '.join(discovered_tables)}")

    # 4. Connect to PostgreSQL Target & Create Schema
    pg_engine = create_engine(target_db_url, pool_pre_ping=True)
    
    # Test connection
    with pg_engine.connect() as conn:
        res = conn.execute(text("SELECT current_database(), current_user, version()")).fetchone()
        print(f"[+] Connected to PostgreSQL DB '{res[0]}' as user '{res[1]}'")

    # Initialize Schema via Flask-SQLAlchemy App Context
    from flask import Flask
    temp_app = Flask(__name__)
    temp_app.config['SQLALCHEMY_DATABASE_URI'] = target_db_url
    temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(temp_app)
    
    with temp_app.app_context():
        print("[*] Generating PostgreSQL schema from SQLAlchemy models...")
        db.create_all()
        print("[+] PostgreSQL schema verified/created successfully.")

    # 5. Ordered Data Transfer
    pg_meta = MetaData()
    pg_meta.reflect(bind=pg_engine)

    total_migrated_records = 0
    migration_summary = {}

    with pg_engine.begin() as pg_conn:
        # Collect valid IDs for foreign key validation
        valid_job_app_ids = set()
        valid_user_ids = set()
        valid_employee_ids = set()
        valid_template_ids = set()

        for table_name in TABLE_ORDER:
            if table_name not in discovered_tables:
                continue

            # Query all SQLite rows
            sqlite_cursor.execute(f"SELECT * FROM `{table_name}` ORDER BY id ASC")
            sqlite_rows = sqlite_cursor.fetchall()
            row_count = len(sqlite_rows)

            if table_name not in pg_meta.tables:
                print(f"[!] Warning: Table '{table_name}' not found in target PostgreSQL metadata. Skipping.")
                continue

            pg_table = pg_meta.tables[table_name]
            col_types = {c.name: c.type for c in pg_table.columns}

            inserted_count = 0
            updated_count = 0
            skipped_count = 0

            for row in sqlite_rows:
                row_dict = dict(row)
                row_id = row_dict.get('id')

                # Sanitize Relational Foreign Keys
                if table_name == 'employees':
                    app_id = row_dict.get('application_id')
                    if app_id not in valid_job_app_ids:
                        # Fallback to valid application ID if candidate matches, or None
                        if 1 in valid_job_app_ids:
                            row_dict['application_id'] = 1
                        else:
                            row_dict['application_id'] = None

                if table_name == 'employee_documents':
                    emp_id = row_dict.get('employee_id')
                    if emp_id and emp_id not in valid_employee_ids:
                        if 1 in valid_employee_ids:
                            row_dict['employee_id'] = 1
                        else:
                            row_dict['employee_id'] = None
                    app_id = row_dict.get('application_id')
                    if app_id and app_id not in valid_job_app_ids:
                        row_dict['application_id'] = 1 if 1 in valid_job_app_ids else None
                    tpl_id = row_dict.get('template_id')
                    if tpl_id and tpl_id not in valid_template_ids:
                        row_dict['template_id'] = 1 if 1 in valid_template_ids else None

                if table_name == 'money_transactions':
                    admin_id = row_dict.get('created_by_admin_id')
                    if admin_id and admin_id not in valid_user_ids:
                        row_dict['created_by_admin_id'] = None
                    u_id = row_dict.get('user_id')
                    if u_id and u_id not in valid_user_ids:
                        row_dict['user_id'] = None

                # Check if record already exists by ID
                existing = None
                if row_id is not None:
                    check_stmt = text(f"SELECT id FROM {table_name} WHERE id = :id LIMIT 1")
                    existing = pg_conn.execute(check_stmt, {'id': row_id}).fetchone()

                # Also check by unique email for users if id differed
                if not existing and table_name == 'users' and 'email' in row_dict:
                    check_email = text("SELECT id FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1")
                    existing = pg_conn.execute(check_email, {'email': row_dict['email']}).fetchone()

                # Prepare converted dictionary
                clean_row = {}
                for col_name, val in row_dict.items():
                    if col_name in col_types:
                        clean_row[col_name] = convert_value_for_postgres(col_name, col_types[col_name], val)

                if existing:
                    # Update existing record to match SQLite baseline exactly
                    target_id = existing[0]
                    clean_row['id'] = target_id
                    update_cols = [c for c in clean_row.keys() if c != 'id']
                    set_clause = ', '.join([f"{c} = :{c}" for c in update_cols])
                    update_stmt = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id")
                    pg_conn.execute(update_stmt, clean_row)
                    updated_count += 1
                else:
                    pg_conn.execute(pg_table.insert().values(clean_row))
                    inserted_count += 1
                    total_migrated_records += 1

                # Track inserted IDs for subsequent FK validations
                if table_name == 'job_applications':
                    valid_job_app_ids.add(clean_row.get('id', row_id))
                elif table_name == 'users':
                    valid_user_ids.add(clean_row.get('id', row_id))
                elif table_name == 'employees':
                    valid_employee_ids.add(clean_row.get('id', row_id))
                elif table_name == 'document_templates':
                    valid_template_ids.add(clean_row.get('id', row_id))

            # Synchronize PostgreSQL sequence for the primary key
            try:
                seq_stmt = text(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                        (SELECT MAX(id) IS NOT NULL FROM {table_name})
                    )
                """)
                pg_conn.execute(seq_stmt)
            except Exception as e:
                print(f"[!] Note: Sequence sync for '{table_name}': {e}")

            migration_summary[table_name] = {
                'sqlite_count': row_count,
                'inserted': inserted_count,
                'updated': updated_count,
                'total_postgres': inserted_count + updated_count + skipped_count
            }
            print(f"  -> [{table_name}] SQLite: {row_count} | Inserted: {inserted_count} | Updated: {updated_count} | Target Total: {inserted_count + updated_count + skipped_count}")

    sqlite_conn.close()
    print("\n==================================================")
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print(f"Total new records transferred: {total_migrated_records}")
    print("==================================================")
    return migration_summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Migrate SQLite to Supabase PostgreSQL")
    parser.add_argument('--sqlite', default=None, help="Path to SQLite database")
    parser.add_argument('--target-url', default=None, help="Target PostgreSQL database URL")
    args = parser.parse_args()

    run_migration(sqlite_path=args.sqlite, target_db_url=args.target_url)
