
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings

def run_migration():
    print("🚀 Starting migration: Add cash_session_id to orders table...")
    
    try:
        # Connect to database using DATABASE_URL
        print(f"Connecting to database...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 1. Add column if not exists
        print("1. Adding cash_session_id column...")
        cursor.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='orders' AND column_name='cash_session_id') THEN
                    ALTER TABLE orders ADD COLUMN cash_session_id INTEGER REFERENCES cash_sessions(id);
                END IF;
            END $$;
        """)
        
        # 2. Add index
        print("2. Adding index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_session ON orders(cash_session_id);
        """)
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()
