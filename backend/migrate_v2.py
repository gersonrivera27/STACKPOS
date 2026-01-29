import psycopg2
from app.config import settings

def migrate_v2():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("Starting V2 Migration...")
        
        # 1. Add coordinates to tables
        print("Checking tables schema for coordinates...")
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tables' AND column_name='x';")
        if not cursor.fetchone():
            print("Adding x, y columns to tables...")
            cursor.execute("ALTER TABLE tables ADD COLUMN x INTEGER DEFAULT 0;")
            cursor.execute("ALTER TABLE tables ADD COLUMN y INTEGER DEFAULT 0;")
            
            # Initialize with grid positions for existing tables (simple layout)
            cursor.execute("SELECT id, table_number FROM tables ORDER BY table_number")
            tables = cursor.fetchall()
            row = 0
            col = 0
            for table in tables:
                x = col * 150 + 20
                y = row * 150 + 20
                cursor.execute("UPDATE tables SET x = %s, y = %s WHERE id = %s", (x, y, table[0]))
                col += 1
                if col > 4:
                    col = 0
                    row += 1
        else:
            print("Coordinates already exist.")

        # 2. Add PIN to users
        print("Checking users schema for PIN...")
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='pin';")
        if not cursor.fetchone():
            print("Adding pin column to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN pin VARCHAR(10);")
            # Set default pin for existing users (e.g. '1234')
            cursor.execute("UPDATE users SET pin = '1234' WHERE pin IS NULL;")
        else:
            print("PIN column already exists.")

        conn.commit()
        print("V2 Migration completed successfully.")
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_v2()
