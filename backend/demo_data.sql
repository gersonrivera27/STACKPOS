-- =============================================================
-- BurgerPOS — Demo Data
-- =============================================================
-- Run with:
--   docker cp backend/demo_data.sql burger-db:/tmp/
--   docker exec burger-db psql -U postgres -d burger_pos -f /tmp/demo_data.sql
-- =============================================================

-- Clean up previous demo orders (keeps users, products, tables)
DELETE FROM order_item_modifiers;
DELETE FROM order_items;
DELETE FROM payments;
DELETE FROM orders;
DELETE FROM cash_sessions;
DELETE FROM customers WHERE phone NOT IN ('0851234567', '0879876543');

-- Reset sequences
SELECT setval('orders_id_seq', 1, false);
SELECT setval('order_items_id_seq', 1, false);
SELECT setval('payments_id_seq', 1, false);
SELECT setval('cash_sessions_id_seq', 1, false);
SELECT setval('customers_id_seq', 1, false);

-- =============================================================
-- 1. CUSTOMERS (Irish customers with Eircode)
-- =============================================================
INSERT INTO customers (phone, name, email, address_line1, city, eircode, is_active) VALUES
('0851234567', 'John Murphy',      'john.murphy@gmail.com',    '12 Main Street',       'Drogheda',   'A92X1Y2', TRUE),
('0879876543', 'Sarah O''Brien',   'sarah.obrien@gmail.com',   '45 Castle Road',       'Drogheda',   'A92T3K8', TRUE),
('0861112233', 'Liam Byrne',       'liam.byrne@hotmail.com',   '8 River View',         'Drogheda',   'A92F5P1', TRUE),
('0874445566', 'Emma Walsh',       'emma.walsh@gmail.com',     '23 Abbey Lane',        'Drogheda',   'A92H2N7', TRUE),
('0857778899', 'Patrick Kelly',    'patrick.kelly@gmail.com',  '67 St. Mary''s Road',  'Drogheda',   'A92K4Q3', TRUE),
('0862223344', 'Aoife Doyle',      'aoife.doyle@gmail.com',    '14 Bridge Street',     'Drogheda',   'A92M6R9', TRUE),
('0873334455', 'Conor Fitzpatrick','conor.fitz@outlook.com',   '31 Green Park',        'Drogheda',   'A92B8S5', TRUE),
('0856667788', 'Niamh Gallagher',  'niamh.g@gmail.com',        '5 Oak Avenue',         'Drogheda',   'A92W1T2', TRUE)
ON CONFLICT (phone) DO UPDATE SET
    name = EXCLUDED.name,
    address_line1 = EXCLUDED.address_line1;

-- =============================================================
-- 2. CASH SESSIONS (last 7 days)
-- =============================================================
INSERT INTO cash_sessions (user_id, status, opening_amount, closing_amount, expected_amount,
    difference, total_sales, total_cash_sales, total_card_sales, total_tips,
    orders_count, opened_at, closed_at)
SELECT
    u.id,
    'closed',
    150.00,
    -- Each day different totals
    day_data.closing,
    day_data.expected,
    day_data.difference,
    day_data.total_sales,
    day_data.cash_sales,
    day_data.card_sales,
    day_data.tips,
    day_data.orders,
    (CURRENT_DATE - day_data.days_ago)::TIMESTAMP + INTERVAL '9 hours',
    (CURRENT_DATE - day_data.days_ago)::TIMESTAMP + INTERVAL '22 hours'
FROM users u,
(VALUES
    (6, 462.50::decimal, 762.50::decimal, 20.00::decimal, 612.50::decimal, 280.00::decimal, 332.50::decimal, 5.00::decimal, 18),
    (5, 380.00::decimal, 680.00::decimal, 50.00::decimal, 530.00::decimal, 210.00::decimal, 320.00::decimal, 0.00::decimal, 14),
    (4, 510.00::decimal, 810.00::decimal, 0.00::decimal,  660.00::decimal, 310.00::decimal, 350.00::decimal, 8.00::decimal, 20),
    (3, 425.00::decimal, 725.00::decimal, 25.00::decimal, 575.00::decimal, 260.00::decimal, 315.00::decimal, 0.00::decimal, 16),
    (2, 490.00::decimal, 790.00::decimal, 0.00::decimal,  640.00::decimal, 300.00::decimal, 340.00::decimal, 12.00::decimal, 19),
    (1, 355.00::decimal, 655.00::decimal, 5.00::decimal,  505.00::decimal, 230.00::decimal, 275.00::decimal, 0.00::decimal, 13)
) AS day_data(days_ago, closing, expected, difference, total_sales, cash_sales, card_sales, tips, orders)
WHERE u.username = 'admin'
LIMIT 6;

-- Today's open session
INSERT INTO cash_sessions (user_id, status, opening_amount, total_sales,
    total_cash_sales, total_card_sales, total_tips, orders_count, opened_at)
SELECT id, 'open', 200.00, 0.00, 0.00, 0.00, 0.00, 0,
    CURRENT_DATE::TIMESTAMP + INTERVAL '9 hours'
FROM users WHERE username = 'admin';

-- =============================================================
-- 3. COMPLETED ORDERS — Last 7 days (for Dashboard stats)
-- =============================================================

-- Helper: we'll insert orders for each of the last 6 days
-- Day -6: 18 orders, Day -5: 14 orders... etc.
-- For brevity, we insert a representative sample per day

DO $$
DECLARE
    v_admin_id      INTEGER;
    v_session_id    INTEGER;
    v_customer_id   INTEGER;
    v_order_id      INTEGER;
    v_order_item_id INTEGER;
    v_day           INTEGER;
    v_hour          INTEGER;
    v_order_ts      TIMESTAMP;
BEGIN
    SELECT id INTO v_admin_id FROM users WHERE username = 'admin';

    -- Loop through last 6 days
    FOR v_day IN 1..6 LOOP
        SELECT id INTO v_session_id
        FROM cash_sessions
        WHERE status = 'closed'
        ORDER BY opened_at
        LIMIT 1 OFFSET (v_day - 1);

        -- Insert 8 sample orders per day (mix of types)
        FOR v_hour IN 1..8 LOOP
            v_order_ts := (CURRENT_DATE - v_day)::TIMESTAMP + (v_hour * 1.5 || ' hours')::INTERVAL + INTERVAL '10 hours';

            -- Pick a customer
            SELECT id INTO v_customer_id FROM customers ORDER BY RANDOM() LIMIT 1;

            -- Order type cycles: takeout, takeout, delivery, takeout, collection, takeout, delivery, takeout
            INSERT INTO orders (
                order_number, customer_name, order_type, status,
                subtotal, tax, delivery_fee, discount, total,
                payment_method, cash_session_id, user_id, phone_line,
                created_at, completed_at
            )
            SELECT
                '#' || LPAD((v_day * 10 + v_hour)::TEXT, 3, '0'),
                c.name,
                CASE (v_hour % 4)
                    WHEN 0 THEN 'delivery'
                    WHEN 1 THEN 'takeout'
                    WHEN 2 THEN 'takeout'
                    ELSE 'collection'
                END,
                'completed',
                ROUND((18.50 + (v_hour * 3.25))::numeric, 2),
                ROUND((18.50 + (v_hour * 3.25)) * 0.23 / 1.23, 2),
                CASE WHEN (v_hour % 4) = 0 THEN 3.00 ELSE 0.00 END,
                0.00,
                ROUND((18.50 + (v_hour * 3.25))::numeric + CASE WHEN (v_hour % 4) = 0 THEN 3.00 ELSE 0.00 END, 2),
                CASE WHEN v_hour % 2 = 0 THEN 'cash' ELSE 'card' END,
                v_session_id,
                v_admin_id,
                NULL,
                v_order_ts,
                v_order_ts + INTERVAL '12 minutes'
            FROM customers c WHERE c.id = v_customer_id
            RETURNING id INTO v_order_id;

            -- Add 2-3 items per order
            -- Item 1: a burger
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal, special_instructions)
            SELECT v_order_id, p.id, 1, p.price, p.price, NULL
            FROM products p
            WHERE p.category_id = 1
            ORDER BY RANDOM() LIMIT 1;

            -- Item 2: a side
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal, special_instructions)
            SELECT v_order_id, p.id, 1, p.price, p.price, NULL
            FROM products p
            WHERE p.category_id = 2
            ORDER BY RANDOM() LIMIT 1;

            -- Item 3: a drink (every other order)
            IF v_hour % 2 = 0 THEN
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal, special_instructions)
                SELECT v_order_id, p.id, 1, p.price, p.price, NULL
                FROM products p
                WHERE p.category_id = 3
                ORDER BY RANDOM() LIMIT 1;
            END IF;

            -- Add a payment record
            INSERT INTO payments (
                order_id, cash_session_id, payment_type,
                total_amount, cash_amount, card_amount, tip_amount, change_amount
            )
            SELECT
                v_order_id,
                v_session_id,
                CASE WHEN v_hour % 2 = 0 THEN 'cash' ELSE 'card' END,
                o.total,
                CASE WHEN v_hour % 2 = 0 THEN o.total ELSE 0 END,
                CASE WHEN v_hour % 2 != 0 THEN o.total ELSE 0 END,
                0.00,
                0.00
            FROM orders o WHERE o.id = v_order_id;

        END LOOP;
    END LOOP;
END $$;

-- =============================================================
-- 4. TODAY's ACTIVE ORDERS (for live demo)
-- =============================================================
DO $$
DECLARE
    v_admin_id   INTEGER;
    v_session_id INTEGER;
    v_order_id   INTEGER;
    v_item_id    INTEGER;
BEGIN
    SELECT id INTO v_admin_id   FROM users        WHERE username = 'admin';
    SELECT id INTO v_session_id FROM cash_sessions WHERE status  = 'open' LIMIT 1;

    -- Order 1: Para Llevar - PREPARING (visible en Cocina)
    INSERT INTO orders (order_number, customer_name, order_type, status,
        subtotal, tax, delivery_fee, discount, total,
        payment_method, cash_session_id, user_id, created_at)
    VALUES ('#001', 'John Murphy', 'takeout', 'preparing',
        19.11, 4.39, 0.00, 0.00, 23.50,
        NULL, v_session_id, v_admin_id, NOW() - INTERVAL '8 minutes')
    RETURNING id INTO v_order_id;

    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Double Burger';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Fries';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Coke';

    -- Order 2: Domicilio - PENDING
    INSERT INTO orders (order_number, customer_name, order_type, status,
        subtotal, tax, delivery_fee, discount, total,
        payment_method, cash_session_id, user_id, phone_line, created_at)
    VALUES ('#002', 'Sarah O''Brien', 'delivery', 'pending',
        17.48, 4.02, 3.00, 0.00, 24.50,
        NULL, v_session_id, v_admin_id, 2, NOW() - INTERVAL '3 minutes')
    RETURNING id INTO v_order_id;

    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 2, price, price * 2 FROM products WHERE name = 'Cheeseburger';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Onion Rings';

    -- Order 3: Mesa 3 - READY (listo para entregar)
    INSERT INTO orders (order_number, customer_name, order_type, status,
        subtotal, tax, delivery_fee, discount, total,
        payment_method, cash_session_id, user_id, table_id, created_at, completed_at)
    VALUES ('#003', 'Table 3', 'collection', 'ready',
        24.39, 5.61, 0.00, 0.00, 30.00,
        NULL, v_session_id, v_admin_id,
        (SELECT id FROM tables WHERE table_number = 3),
        NOW() - INTERVAL '15 minutes',
        NOW() - INTERVAL '2 minutes')
    RETURNING id INTO v_order_id;

    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Bacon Burger';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Chicken Burger';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 2, price, price * 2 FROM products WHERE name = 'Fries';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 2, price, price * 2 FROM products WHERE name = 'Coke';

    -- Mark table 3 as occupied
    UPDATE tables SET is_occupied = TRUE WHERE table_number = 3;

    -- Order 4: Para Llevar - CONFIRMED
    INSERT INTO orders (order_number, customer_name, order_type, status,
        subtotal, tax, delivery_fee, discount, total,
        payment_method, cash_session_id, user_id, created_at)
    VALUES ('#004', 'Liam Byrne', 'takeout', 'confirmed',
        14.23, 3.27, 0.00, 0.00, 17.50,
        NULL, v_session_id, v_admin_id, NOW() - INTERVAL '1 minute')
    RETURNING id INTO v_order_id;

    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Classic Burger';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Fries';
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    SELECT v_order_id, id, 1, price, price FROM products WHERE name = 'Milkshake';

END $$;

-- =============================================================
-- Summary
-- =============================================================
SELECT 'customers'    AS table_name, COUNT(*) AS rows FROM customers
UNION ALL
SELECT 'cash_sessions',               COUNT(*)        FROM cash_sessions
UNION ALL
SELECT 'orders (total)',               COUNT(*)        FROM orders
UNION ALL
SELECT 'orders (today active)',        COUNT(*)        FROM orders  WHERE created_at >= CURRENT_DATE
UNION ALL
SELECT 'order_items',                  COUNT(*)        FROM order_items
UNION ALL
SELECT 'payments',                     COUNT(*)        FROM payments;

\echo '✅ Demo data loaded successfully!'
