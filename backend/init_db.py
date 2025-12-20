"""
Database initialization script.
Run this script to create all database tables.
"""

from database import init_database, drop_all_tables
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        print("⚠️  WARNING: This will drop all tables!")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            drop_all_tables()
    
    print("Initializing database...")
    init_database()
    print("✅ Database initialized successfully")
