BEGIN;

-- Categorias nuevas (idempotente por nombre)
INSERT INTO categories (name, description)
SELECT 'Pollo Crujiente', 'Combos y piezas de pollo frito'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE LOWER(name) = LOWER('Pollo Crujiente'));

INSERT INTO categories (name, description)
SELECT 'Wraps', 'Wraps calientes y frios para llevar'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE LOWER(name) = LOWER('Wraps'));

INSERT INTO categories (name, description)
SELECT 'Ensaladas', 'Opciones ligeras y frescas'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE LOWER(name) = LOWER('Ensaladas'));

INSERT INTO categories (name, description)
SELECT 'Menu Infantil', 'Opciones para ninos con porciones pequenas'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE LOWER(name) = LOWER('Menu Infantil'));

INSERT INTO categories (name, description)
SELECT 'Salsas', 'Salsas y dips extra'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE LOWER(name) = LOWER('Salsas'));

-- Productos mock de takeaway (idempotente por nombre + categoria)
WITH cat AS (
  SELECT id, name FROM categories
)
INSERT INTO products (category_id, name, description, price, image_url, is_available, sort_order, stock_quantity)
SELECT c.id, v.name, v.description, v.price, NULL, TRUE, v.sort_order, v.stock
FROM (
  VALUES
  -- Hamburguesas
  ('Hamburguesas','Hamburguesa Cheese Deluxe','Doble queso cheddar, pepinillos y salsa especial',10.90,20,100),
  ('Hamburguesas','Hamburguesa Bacon Smash','Carne smash, bacon crujiente y cebolla caramelizada',12.90,21,100),
  ('Hamburguesas','Hamburguesa Pollo BBQ','Pechuga crispy con salsa BBQ ahumada',10.50,22,100),
  ('Hamburguesas','Hamburguesa Veggie Green','Medallon vegetal, aguacate y tomate',9.80,23,100),
  ('Hamburguesas','Hamburguesa Picante Chipotle','Jalapenos, chipotle mayo y pepper jack',11.70,24,100),

  -- Pollo Crujiente
  ('Pollo Crujiente','Tiras de Pollo 4pz','Tiras de pollo rebozado con dip a elegir',7.90,10,100),
  ('Pollo Crujiente','Tiras de Pollo 8pz','Porcion grande para compartir',13.90,11,100),
  ('Pollo Crujiente','Alitas BBQ 6pz','Alitas glaseadas en BBQ dulce',8.90,12,100),
  ('Pollo Crujiente','Alitas Picantes 6pz','Alitas con salsa picante estilo buffalo',8.90,13,100),
  ('Pollo Crujiente','Combo Pollo Crujiente','4 tiras + papas medianas + bebida',11.90,14,100),

  -- Extras
  ('Extras','Papas Gajo','Papas estilo gajo con especias',4.20,30,120),
  ('Extras','Papas con Queso','Papas fritas con cheddar fundido',5.50,31,120),
  ('Extras','Papas con Bacon','Papas fritas con cheddar y bacon bits',6.30,32,100),
  ('Extras','Nuggets 6pz','Nuggets crujientes de pollo',5.20,33,120),
  ('Extras','Nuggets 10pz','Nuggets crujientes de pollo',7.80,34,120),
  ('Extras','Mozzarella Sticks 6pz','Palitos de mozzarella con salsa marinara',6.90,35,80),
  ('Extras','Aros de Cebolla XL','Porcion grande de aros crujientes',5.90,36,100),

  -- Wraps
  ('Wraps','Wrap Caesar Crispy','Pollo crispy, lechuga y aderezo caesar',8.70,40,90),
  ('Wraps','Wrap Spicy Chicken','Pollo picante, col y chipotle mayo',8.90,41,90),
  ('Wraps','Wrap Veggie Hummus','Vegetales grillados y hummus',8.20,42,90),
  ('Wraps','Wrap BBQ Bacon','Pollo, bacon, cheddar y salsa BBQ',9.30,43,90),

  -- Ensaladas
  ('Ensaladas','Ensalada Caesar','Lechuga romana, queso, crutones y caesar',7.50,50,80),
  ('Ensaladas','Ensalada Cesar con Pollo','Version con pollo grillado',9.40,51,80),
  ('Ensaladas','Ensalada Mediterranea','Mix verde, aceitunas y queso feta',8.70,52,80),

  -- Menu Infantil
  ('Menu Infantil','Kids Burger','Mini burger, papas pequenas y jugo',7.40,60,100),
  ('Menu Infantil','Kids Nuggets','4 nuggets, papas pequenas y jugo',7.20,61,100),
  ('Menu Infantil','Kids Cheese Wrap','Wrap pequeno de queso y pollo',7.30,62,100),

  -- Bebidas
  ('Bebidas','Coca Cola Zero','Lata 330ml sin azucar',2.50,70,150),
  ('Bebidas','Sprite Zero','Lata 330ml sin azucar',2.50,71,150),
  ('Bebidas','Fanta Naranja','Lata 330ml',2.50,72,150),
  ('Bebidas','Nestea Limon','Botella 500ml',2.90,73,120),
  ('Bebidas','Agua con Gas','Botella 500ml',1.90,74,140),
  ('Bebidas','Limonada Casera','Vaso 450ml',3.20,75,80),
  ('Bebidas','Batido Vainilla','Vaso 450ml',4.90,76,70),
  ('Bebidas','Batido Chocolate','Vaso 450ml',4.90,77,70),
  ('Bebidas','Batido Fresa','Vaso 450ml',4.90,78,70),

  -- Postres
  ('Postres','Brownie con Helado','Brownie tibio con bola de vainilla',5.50,80,60),
  ('Postres','Cheesecake de Frutos Rojos','Porcion individual',5.20,81,60),
  ('Postres','Cookie Choco XL','Galleta grande con chips de chocolate',3.40,82,80),
  ('Postres','Sundae Caramelo','Helado soft con topping caramelo',3.90,83,80),

  -- Salsas
  ('Salsas','Salsa BBQ','Porcion extra de salsa BBQ',0.80,90,300),
  ('Salsas','Salsa Chipotle','Porcion extra de salsa chipotle',0.80,91,300),
  ('Salsas','Salsa Ajo','Porcion extra de salsa de ajo',0.80,92,300),
  ('Salsas','Mayonesa Trufa','Porcion extra premium',1.20,93,200),
  ('Salsas','Ketchup','Porcion individual',0.40,94,400)
) AS v(category_name, name, description, price, sort_order, stock)
JOIN cat c ON c.name = v.category_name
WHERE NOT EXISTS (
  SELECT 1
  FROM products p
  WHERE p.category_id = c.id
    AND LOWER(p.name) = LOWER(v.name)
);

COMMIT;
