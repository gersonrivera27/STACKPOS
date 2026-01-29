import psycopg2
from app.config import settings

def migrate_tables():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("Checking tables schema...")
        
        # Check if is_occupied exists
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tables' AND column_name='is_occupied';")
        if not cursor.fetchone():
            print("Adding is_occupied column...")
            cursor.execute("ALTER TABLE tables ADD COLUMN is_occupied BOOLEAN DEFAULT FALSE;")
            
            # Migrate data from status if exists
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tables' AND column_name='status';")
            if cursor.fetchone():
                print("Migrating data from status column...")
                cursor.execute("UPDATE tables SET is_occupied = TRUE WHERE status = 'occupied';")
                # Optional: Drop status column? Let's keep it for safety for now, or drop it to avoid confusion.
                # The backend router DOES NOT query 'status' column anymore, it queries 'is_occupied'.
                # So it's safe to leave it, but cleaner to drop. 
                # Let's drop 'status' and 'capacity' to match init.sql perfectly.
                print("Dropping legacy columns status and capacity...")
                cursor.execute("ALTER TABLE tables DROP COLUMN IF EXISTS status;")
                cursor.execute("ALTER TABLE tables DROP COLUMN IF EXISTS capacity;")
        
        else:
            print("is_occupied already exists.")

        conn.commit()
        print("Migration completed successfully.")
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_tables()
