"""
Migration script to convert from Telegram to Email notifications
This script updates the database schema and removes telegram-related fields
"""

import sqlite3
import sys

def migrate_database():
    """Migrate the database to use email instead of telegram"""
    
    db_path = "bookmyshow_tracker.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting migration...")
        
        # Check if email column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'email' not in columns:
            print("Adding email column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        
        # Create a new users table with the correct schema
        print("Creating new users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Try to migrate existing users if they have email
        print("Migrating existing users...")
        cursor.execute("""
            INSERT OR IGNORE INTO users_new (id, email, is_active, created_at, updated_at)
            SELECT id, 
                   COALESCE(email, telegram_id || '@migrated.temp') as email,
                   is_active, 
                   created_at, 
                   updated_at 
            FROM users 
            WHERE email IS NOT NULL OR telegram_id IS NOT NULL
        """)
        
        # Get the count of migrated users
        cursor.execute("SELECT COUNT(*) FROM users_new")
        migrated_count = cursor.fetchone()[0]
        
        if migrated_count == 0:
            print("\nNo users to migrate. Starting fresh with email-based system.")
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
        else:
            print(f"\nMigrated {migrated_count} users.")
            print("\nWARNING: Some users may have temporary email addresses (@migrated.temp).")
            print("These users will need to re-subscribe with valid email addresses.")
            
            # Replace old table with new one
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        # Create index on email
        print("Creating index on email...")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Set Gmail credentials in .env or config.py")
        print("3. Restart your application")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Telegram → Email Notifications")
    print("=" * 60)
    print("\nThis will modify your database structure.")
    
    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        migrate_database()
    else:
        print("Migration cancelled.")

