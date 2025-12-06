"""
Script para insertar datos iniciales
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings

def seed_data():
    """Insertar categorías y productos iniciales"""
    
    print("🚀 Iniciando seed de datos...")
    
    conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    try:
        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        count = cursor.fetchone()['count']
        
        if count > 0:
            print("✅ Los datos ya existen, saltando seed.")
            return
        
        # Insertar categorías
        print("📦 Insertando categorías...")
        cursor.execute("""
            INSERT INTO categories (name, sort_order) VALUES
            ('Burgers', 1),
            ('Sides', 2),
            ('Drinks', 3),
            ('Desserts', 4)
        """)
        
        # Insertar productos
        print("🍔 Insertando productos...")
        cursor.execute("""
            INSERT INTO products (name, category_id, price, description, sort_order) VALUES
            -- Burgers
            ('Classic Burger', 1, 8.50, 'Beef patty, lettuce, tomato, onion', 1),
            ('Cheeseburger', 1, 9.50, 'Classic burger with cheddar cheese', 2),
            ('Bacon Burger', 1, 10.50, 'Beef patty with crispy bacon and cheese', 3),
            ('Double Burger', 1, 12.00, 'Two beef patties, double cheese', 4),
            ('Chicken Burger', 1, 9.00, 'Crispy chicken fillet, mayo, lettuce', 5),
            ('Veggie Burger', 1, 8.00, 'Plant-based patty, fresh vegetables', 6),
            
            -- Sides
            ('Fries', 2, 3.50, 'Crispy golden fries', 1),
            ('Onion Rings', 2, 4.00, 'Breaded and fried onion rings', 2),
            ('Chicken Nuggets', 2, 5.50, '6 pieces of chicken nuggets', 3),
            ('Mozzarella Sticks', 2, 5.00, 'Breaded mozzarella sticks', 4),
            ('Coleslaw', 2, 3.00, 'Fresh coleslaw', 5),
            
            -- Drinks
            ('Coke', 3, 2.50, '330ml can', 1),
            ('Diet Coke', 3, 2.50, '330ml can', 2),
            ('Sprite', 3, 2.50, '330ml can', 3),
            ('Fanta', 3, 2.50, '330ml can', 4),
            ('Water', 3, 1.50, '500ml bottle', 5),
            ('Milkshake', 3, 4.50, 'Chocolate, vanilla, or strawberry', 6),
            
            -- Desserts
            ('Ice Cream', 4, 3.50, 'Two scoops', 1),
            ('Brownie', 4, 4.00, 'Chocolate brownie with ice cream', 2),
            ('Apple Pie', 4, 3.50, 'Warm apple pie', 3)
        """)
        
        conn.commit()
        print("✅ Seed completado exitosamente!")
        print("   - 4 categorías insertadas")
        print("   - 20 productos insertados")
    
    except Exception as e:
        print(f"❌ Error al hacer seed: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_data()