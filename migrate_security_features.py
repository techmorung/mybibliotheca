#!/usr/bin/env python3
"""
Database migration script to add security and privacy fields to User model
Run this script to add the new fields for account lockout and privacy settings
"""

import os
import sys
import sqlite3
from datetime import datetime, timezone

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Add new fields to the user table"""
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'books.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting database migration...")
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current user table columns: {columns}")
        
        # Add new columns if they don't exist
        new_columns = [
            ('failed_login_attempts', 'INTEGER DEFAULT 0'),
            ('locked_until', 'DATETIME'),
            ('last_login', 'DATETIME'),
            ('share_current_reading', 'BOOLEAN DEFAULT 1'),
            ('share_reading_activity', 'BOOLEAN DEFAULT 1'),
            ('share_library', 'BOOLEAN DEFAULT 1')
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE user ADD COLUMN {column_name} {column_def}"
                    print(f"Adding column: {column_name}")
                    cursor.execute(sql)
                    print(f"✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"❌ Error adding column {column_name}: {e}")
            else:
                print(f"✅ Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(user)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"Updated user table columns: {new_columns}")
        
        print("✅ Database migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Bibliotheca - Security & Privacy Features Migration")
    print("=" * 60)
    
    if migrate_database():
        print("\n🎉 Migration completed successfully!")
        print("New features available:")
        print("  • Account lockout after 5 failed login attempts")
        print("  • Admin password reset functionality")
        print("  • User privacy settings for sharing preferences")
        print("  • Enhanced user activity tracking")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
