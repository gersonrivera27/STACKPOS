import psycopg2
from app.config import settings

def migrate_v3():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("Starting V3 Migration (Waiter Tracking)...")
        
        # Check if user_id exists in orders
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='orders' AND column_name='user_id';")
        if not cursor.fetchone():
            print("Adding user_id column to orders...")
            cursor.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id);")
            
            # Create index for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);")
        else:
            print("user_id column already exists.")

        conn.commit()
        print("V3 Migration completed successfully.")
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_v3()
