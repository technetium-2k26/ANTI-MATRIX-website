"""
Non-destructive database migration for Anti-Matrix Employee Credentials System.
Creates the 'employees' table with strict unique constraints and indices.
Preserves all existing data (Users, Job Postings, Candidate Applications, Payments).
"""
import sys
import os

# Add root project path to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Employee


def run_migration():
    app = create_app(os.environ.get('FLASK_CONFIG', 'development'))
    with app.app_context():
        print("[MIGRATION] Checking database tables...")
        # db.create_all() creates any missing tables (like 'employees') without altering existing tables
        db.create_all()
        
        # Verify employees table creation
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"[MIGRATION] Current database tables: {tables}")
        
        if 'employees' in tables:
            columns = [col['name'] for col in inspector.get_columns('employees')]
            print(f"[MIGRATION] 'employees' table is active with columns: {columns}")
            print("[MIGRATION] SUCCESS: Employee model migration completed non-destructively.")
        else:
            print("[MIGRATION] ERROR: 'employees' table was not created.")
            sys.exit(1)


if __name__ == '__main__':
    run_migration()
