#!/usr/bin/env python3
"""
Database Schema Migration Script for Bibliotheca
This script adds the new security and privacy fields to the user table.
"""

import sqlite3
import os
import sys

def migrate_database_schema():
    """Add new columns to the user table if they don't exist"""
    db_path = '/app/data/books.db'
    
    # Connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Checking database schema...")
        
        # Get current table structure
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # List of new columns to add
        new_columns = [
            ('failed_login_attempts', 'INTEGER DEFAULT 0'),
            ('locked_until', 'DATETIME'),
            ('last_login', 'DATETIME'),
            ('share_current_reading', 'BOOLEAN DEFAULT 1'),
            ('share_reading_activity', 'BOOLEAN DEFAULT 1'),
            ('share_library', 'BOOLEAN DEFAULT 1')
        ]
        
        # Add missing columns
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"⚠️  Error adding {column_name}: {e}")
            else:
                print(f"✅ Column already exists: {column_name}")
        
        # Commit changes
        conn.commit()
        print("✅ Database schema migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Starting database schema migration...")
    print("=" * 50)
    
    success = migrate_database_schema()
    
    if success:
        print("=" * 50)
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("=" * 50)
        print("❌ Migration failed!")
        sys.exit(1)
