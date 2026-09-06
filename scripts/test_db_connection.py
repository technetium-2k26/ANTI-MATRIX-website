"""
Safe Database Connectivity Test Script
Tests DATABASE_URL connection without exposing credentials or secrets.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'))

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from config import get_database_uri

def test_connection():
    print("\n========================================================")
    print("      ANTI-MATRIX DATABASE CONNECTIVITY DIAGNOSTIC      ")
    print("========================================================")
    
    raw_url = os.environ.get('DATABASE_URL', '').strip()
    if not raw_url:
        print("[!] DATABASE_URL is not set in environment. Using default config.")
    
    normalized_url = get_database_uri(force_production_check=False)
    
    try:
        url_obj = make_url(normalized_url)
        print("\n--- 1. PARSED CONNECTION METADATA (SAFE) ---")
        print(f"  Dialect:      {url_obj.get_backend_name()}")
        print(f"  Driver:       {url_obj.get_driver_name()}")
        print(f"  Username:     {url_obj.username}")
        print(f"  Host:         {url_obj.host}")
        print(f"  Port:         {url_obj.port}")
        print(f"  Database:     {url_obj.database}")
        print(f"  Password:     [REDACTED - {len(url_obj.password or '')} characters]")
    except Exception as e:
        print(f"[-] Malformed URL Error: Failed to parse connection string: {e}")
        return False

    print("\n--- 2. CONNECTIVITY TEST (SELECT 1) ---")
    try:
        engine = create_engine(normalized_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1, current_database(), current_user, version()")).fetchone()
            print(f"[+] SUCCESS: Connected to '{result[1]}' as '{result[2]}'")
            print(f"[+] PostgreSQL Version: {result[3][:50]}...")
            print(f"[+] Query Test (SELECT 1): {result[0]} -> OK")
        engine.dispose()
        print("\n========================================================")
        print("          ALL CONNECTIVITY TESTS PASSED (OK)           ")
        print("========================================================\n")
        return True
    except Exception as e:
        err_msg = str(e)
        print(f"[-] Connection Failed: {err_msg}")
        print("\n--- DIAGNOSTIC CLUES ---")
        if "could not translate host name" in err_msg:
            print("  -> DNS / Hostname issue: Check if hostname is formatted correctly and IPv4 reachable.")
        elif "password authentication failed" in err_msg:
            print("  -> Authentication issue: Incorrect database password or username.")
        elif "connection refused" in err_msg:
            print("  -> Network issue: Port is closed or server is unreachable.")
        elif "SSL" in err_msg:
            print("  -> SSL issue: Supabase requires SSL enabled.")
        else:
            print("  -> Other connection or driver error.")
        print("========================================================\n")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
