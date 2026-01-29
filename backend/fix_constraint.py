import psycopg2
from app.config import settings

def fix_constraint():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("Intentando eliminar constraint unique de order_number...")
        cursor.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_order_number_key;")
        conn.commit()
        print("Constraint eliminado exitosamente.")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_constraint()
