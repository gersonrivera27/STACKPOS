"""
Router para reportes y analytics
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from ..security import verificar_rol
from typing import Optional
from datetime import date

from ..database import get_db

router = APIRouter()

@router.get("/daily-sales")
def get_daily_sales(report_date: Optional[date] = None, conn = Depends(get_db), usuario = Depends(verificar_rol("admin", "manager"))):
    """Reporte de ventas diarias. Requiere rol admin o manager."""
    cursor = conn.cursor()

    if not report_date:
        report_date = date.today()

    cursor.execute(
        """SELECT
            COUNT(CASE WHEN status <> 'cancelled' THEN 1 END) as total_orders,
            COALESCE(SUM(CASE WHEN status <> 'cancelled' THEN total ELSE 0 END), 0) as total_sales,
            COALESCE(AVG(CASE WHEN status <> 'cancelled' THEN total ELSE NULL END), 0) as average_ticket,
            COALESCE(SUM(CASE WHEN status <> 'cancelled' THEN tax ELSE 0 END), 0) as total_tax,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders
           FROM orders
           WHERE DATE(created_at) = %s""",
        (report_date,)
    )
    result = cursor.fetchone()

    # Obtener ventas por tipo de orden
    cursor.execute(
        """SELECT order_type, COUNT(*) as count, COALESCE(SUM(total), 0) as total
           FROM orders
           WHERE DATE(created_at) = %s AND status <> 'cancelled'
           GROUP BY order_type""",
        (report_date,)
    )
    by_type = cursor.fetchall()

    return {
        "date": report_date,
        "summary": dict(result),
        "by_order_type": [dict(row) for row in by_type]
    }

@router.get("/top-products")
def get_top_products(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(default=10, ge=1, le=100),
    conn = Depends(get_db),
    usuario = Depends(verificar_rol("admin", "manager"))
):
    """Reporte de productos mas vendidos. Requiere rol admin o manager."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from no puede ser posterior a date_to")
    cursor = conn.cursor()

    query = """
        SELECT
            p.id,
            p.name,
            c.name as category,
            COUNT(oi.id) as times_ordered,
            SUM(oi.quantity) as total_quantity,
            SUM(oi.subtotal) as total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status <> 'cancelled'
    """
    params = []

    if date_from:
        query += " AND DATE(o.created_at) >= %s"
        params.append(date_from)

    if date_to:
        query += " AND DATE(o.created_at) <= %s"
        params.append(date_to)

    query += """
        GROUP BY p.id, p.name, c.name
        ORDER BY total_quantity DESC
        LIMIT %s
    """
    params.append(limit)

    cursor.execute(query, params)
    products = cursor.fetchall()

    return {
        "date_from": date_from,
        "date_to": date_to,
        "top_products": [dict(row) for row in products]
    }

@router.get("/revenue-by-period")
def get_revenue_by_period(
    date_from: date,
    date_to: date,
    group_by: str = "day",  # 'day', 'week', 'month'
    conn = Depends(get_db),
    usuario = Depends(verificar_rol("admin", "manager"))
):
    """Reporte de ingresos por periodo. Requiere rol admin o manager."""
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from no puede ser posterior a date_to")

    cursor = conn.cursor()

    GROUP_BY_EXPRESSIONS = {
        "day":   "DATE(created_at)",
        "week":  "DATE_TRUNC('week', created_at)",
        "month": "DATE_TRUNC('month', created_at)",
    }

    if group_by not in GROUP_BY_EXPRESSIONS:
        raise HTTPException(status_code=400, detail="group_by debe ser: day, week, o month")

    date_expr = GROUP_BY_EXPRESSIONS[group_by]

    query = """
        SELECT
            {date_expr} as period,
            COUNT(*) as orders_count,
            SUM(total) as total_revenue,
            AVG(total) as average_ticket
        FROM orders
        WHERE status = 'completed'
        AND DATE(created_at) BETWEEN %s AND %s
        GROUP BY period
        ORDER BY period
    """.replace("{date_expr}", date_expr)

    cursor.execute(query, (date_from, date_to))
    results = cursor.fetchall()

    return {
        "date_from": date_from,
        "date_to": date_to,
        "group_by": group_by,
        "data": [dict(row) for row in results]
    }
