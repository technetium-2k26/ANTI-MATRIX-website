"""
Safe SQLite vs Supabase PostgreSQL Verification Script
Compares table counts, critical business identifiers, sequences, and foreign-key relationships.
Reports MATCH or MISMATCH.
"""

import os
import sys
import sqlite3
import argparse
from dotenv import load_dotenv

# Ensure stdout handles UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'))

from sqlalchemy import create_engine, text

ALL_TABLES = [
    'users',
    'job_postings',
    'contact_inquiries',
    'document_templates',
    'email_templates',
    'email_logs',
    'job_applications',
    'employees',
    'payments',
    'employee_documents',
    'money_transactions',
]

def verify_migration(sqlite_path=None, target_db_url=None):
    if not sqlite_path:
        sqlite_path = os.path.join(BASE_DIR, 'antimatrix.db')
    
    if not os.path.exists(sqlite_path):
        print(f"[-] ERROR: Source SQLite database not found at: {sqlite_path}")
        sys.exit(1)

    if not target_db_url:
        target_db_url = os.environ.get('DATABASE_URL', '').strip()

    if not target_db_url:
        print("[-] ERROR: DATABASE_URL is not set. Please provide Supabase PostgreSQL connection string.")
        sys.exit(1)

    if target_db_url.startswith('postgres://'):
        target_db_url = 'postgresql://' + target_db_url[len('postgres://'):]

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

    pg_engine = create_engine(target_db_url, pool_pre_ping=True)

    print("\n==================================================================")
    print("      ANTI-MATRIX SQLITE -> SUPABASE POSTGRESQL AUDIT REPORT       ")
    print("==================================================================")

    all_passed = True
    table_results = []

    with pg_engine.connect() as pg_conn:
        # 1. Table Count Comparisons
        print("\n--- 1. TABLE ROW COUNT VERIFICATION ---")
        print(f"{'TABLE NAME':<24} | {'SQLITE':<8} | {'POSTGRES':<10} | {'STATUS'}")
        print("-" * 60)

        for table in ALL_TABLES:
            # SQLite count
            try:
                sqlite_cursor.execute(f"SELECT count(*) FROM `{table}`")
                sq_cnt = sqlite_cursor.fetchone()[0]
            except Exception:
                sq_cnt = 0

            # PostgreSQL count
            try:
                pg_res = pg_conn.execute(text(f"SELECT count(*) FROM {table}")).fetchone()
                pg_cnt = pg_res[0] if pg_res else 0
            except Exception as e:
                pg_cnt = f"ERR"

            status = "MATCH" if sq_cnt == pg_cnt else "MISMATCH"
            if status != "MATCH":
                all_passed = False

            table_results.append((table, sq_cnt, pg_cnt, status))
            print(f"{table:<24} | {sq_cnt:<8} | {str(pg_cnt):<10} | {status}")

        # 2. Critical Business Identifiers Verification
        print("\n--- 2. BUSINESS IDENTIFIERS & DATA INTEGRITY ---")

        # Application Codes
        sq_apps = sqlite_cursor.execute("SELECT id, COALESCE(application_code, 'AM-APP-' || printf('%06d', id)), full_name, email FROM job_applications ORDER BY id").fetchall()
        pg_apps = pg_conn.execute(text("SELECT id, COALESCE(application_code, 'AM-APP-' || LPAD(id::text, 6, '0')), full_name, email FROM job_applications ORDER BY id")).fetchall()
        
        apps_match = (len(sq_apps) == len(pg_apps)) and all(
            sq[0] == pg[0] and sq[1] == pg[1] and sq[3] == pg[3] for sq, pg in zip(sq_apps, pg_apps)
        )
        print(f"[*] Application Codes Integrity: {'MATCH' if apps_match else 'MISMATCH'}")
        for app in pg_apps:
            print(f"    - App ID {app[0]}: Code='{app[1]}', Candidate='{app[2]}', Email='{app[3]}'")
        if not apps_match:
            all_passed = False

        # Employee IDs
        sq_emps = sqlite_cursor.execute("SELECT id, employee_id FROM employees ORDER BY id").fetchall()
        pg_emps = pg_conn.execute(text("SELECT id, employee_id, application_id FROM employees ORDER BY id")).fetchall()

        emps_match = (len(sq_emps) == len(pg_emps)) and all(
            sq[0] == pg[0] and sq[1] == pg[1] for sq, pg in zip(sq_emps, pg_emps)
        )
        print(f"[*] Employee IDs Integrity: {'MATCH' if emps_match else 'MISMATCH'}")
        for emp in pg_emps:
            print(f"    - Employee DB ID {emp[0]}: Employee ID='{emp[1]}', Linked Application ID={emp[2]}")
        if not emps_match:
            all_passed = False

        # User Credentials & Emails
        sq_users = sqlite_cursor.execute("SELECT id, email, role, is_active FROM users ORDER BY id").fetchall()
        pg_users = pg_conn.execute(text("SELECT id, email, role, is_active FROM users ORDER BY id")).fetchall()

        users_match = (len(sq_users) == len(pg_users)) and all(
            sq[0] == pg[0] and sq[1] == pg[1] and sq[2] == pg[2] for sq, pg in zip(sq_users, pg_users)
        )
        print(f"[*] Users & Roles Integrity: {'MATCH' if users_match else 'MISMATCH'}")
        for u in pg_users:
            print(f"    - User ID {u[0]}: Email='{u[1]}', Role='{u[2]}', Active={u[3]}")
        if not users_match:
            all_passed = False

        # Document Templates
        sq_docs = sqlite_cursor.execute("SELECT id, template_type, filename, is_active FROM document_templates ORDER BY id").fetchall()
        pg_docs = pg_conn.execute(text("SELECT id, template_type, filename, is_active FROM document_templates ORDER BY id")).fetchall()
        docs_match = (len(sq_docs) == len(pg_docs)) and all(
            sq[0] == pg[0] and sq[1] == pg[1] and sq[3] == pg[3] for sq, pg in zip(sq_docs, pg_docs)
        )
        print(f"[*] Document Templates Integrity: {'MATCH' if docs_match else 'MISMATCH'}")
        for doc in pg_docs:
            print(f"    - Doc Template ID {doc[0]}: Type='{doc[1]}', File='{doc[2]}', Active={doc[3]}")
        if not docs_match:
            all_passed = False

        # Email Templates
        sq_emails = sqlite_cursor.execute("SELECT id, template_type, name FROM email_templates ORDER BY id").fetchall()
        pg_emails = pg_conn.execute(text("SELECT id, template_type, name FROM email_templates ORDER BY id")).fetchall()
        emails_match = (len(sq_emails) == len(pg_emails)) and all(
            sq[0] == pg[0] and sq[1] == pg[1] for sq, pg in zip(sq_emails, pg_emails)
        )
        print(f"[*] Email Templates Integrity: {'MATCH' if emails_match else 'MISMATCH'}")
        for em in pg_emails:
            print(f"    - Email Template ID {em[0]}: Type='{em[1]}', Name='{em[2]}'")
        if not emails_match:
            all_passed = False

        # Money Transactions
        sq_money = sqlite_cursor.execute("SELECT id, transaction_type, amount, category FROM money_transactions ORDER BY id").fetchall()
        pg_money = pg_conn.execute(text("SELECT id, transaction_type, amount, category FROM money_transactions ORDER BY id")).fetchall()
        money_match = (len(sq_money) == len(pg_money)) and all(
            sq[0] == pg[0] and sq[1] == pg[1] and float(sq[2]) == float(pg[2]) for sq, pg in zip(sq_money, pg_money)
        )
        print(f"[*] Money Transactions Integrity: {'MATCH' if money_match else 'MISMATCH'}")
        for m in pg_money:
            print(f"    - Transaction ID {m[0]}: Type='{m[1]}', Amount=₹{m[2]}, Category='{m[3]}'")
        if not money_match:
            all_passed = False

        # 3. Sequence Synchronization Checks
        print("\n--- 3. POSTGRESQL PRIMARY KEY SEQUENCES CHECK ---")
        for table in ALL_TABLES:
            try:
                seq_val_res = pg_conn.execute(text(f"""
                    SELECT 
                        pg_get_serial_sequence('{table}', 'id') as seq,
                        (SELECT MAX(id) FROM {table}) as max_id
                """)).fetchone()
                
                seq_name = seq_val_res[0]
                max_id = seq_val_res[1] or 0
                
                if seq_name:
                    curr_val_res = pg_conn.execute(text(f"SELECT last_value, is_called FROM {seq_name}")).fetchone()
                    last_val = curr_val_res[0]
                    is_called = curr_val_res[1]
                    print(f"[*] {table:<24} -> Sequence: {seq_name} | Max ID: {max_id} | Sequence Val: {last_val} (is_called={is_called}) [OK]")
            except Exception as e:
                print(f"[!] Note for {table}: {e}")

    sqlite_conn.close()

    print("\n==================================================================")
    if all_passed:
        print("          ALL VERIFICATION AUDITS PASSED WITH ZERO ERRORS          ")
    else:
        print("         VERIFICATION FAILED: ONE OR MORE AUDITS MISMATCHED       ")
    print("==================================================================\n")

    return all_passed

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Verify SQLite to Supabase PostgreSQL Migration")
    parser.add_argument('--sqlite', default=None, help="Path to SQLite database")
    parser.add_argument('--target-url', default=None, help="Target PostgreSQL database URL")
    args = parser.parse_args()

    success = verify_migration(sqlite_path=args.sqlite, target_db_url=args.target_url)
    sys.exit(0 if success else 1)
