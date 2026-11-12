# tests/test_db.py

import sqlite3
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models import db

def test_db_exists():
    DB_PATH = "instance/finance.db"
    # Create the database if it doesn't exist
    with app.app_context():
        if not os.path.exists(DB_PATH):
            db.create_all()
    assert os.path.exists(DB_PATH)

def test_tables_exist(app):
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    # Create the tables in the in-memory database for testing
    with app.app_context():
        db.create_all()
        
    # Connect to the app's database
    engine = db.engine
    inspector = db.inspect(engine)
    tables = inspector.get_table_names()

    required_tables = ["transactions", "accounts", "categories", "user"]
    
    for table in required_tables:
        assert table in tables, f"Table {table} not found"

    conn.close()
