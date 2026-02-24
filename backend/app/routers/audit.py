"""
Audit router: exposes audit_logs stored by the audit consumer.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from ..database import get_db

router = APIRouter(tags=["Audit"])


@router.get("/logs")
def list_audit_logs(
    event: Optional[str] = Query(None, description="Filter by event type"),
    username: Optional[str] = Query(None, description="Filter by username"),
    limit: int = Query(50, ge=1, le=500),
    conn=Depends(get_db),
):
    """Return audit log entries, most recent first."""
    cursor = conn.cursor()

    conditions = []
    params = []

    if event:
        conditions.append("event = %s")
        params.append(event)
    if username:
        conditions.append("username ILIKE %s")
        params.append(f"%{username}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    cursor.execute(
        f"""
        SELECT id, event, username, user_id, ip_address, details, created_at
        FROM audit_logs
        {where}
        ORDER BY created_at DESC
        LIMIT %s
        """,
        params,
    )
    rows = cursor.fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}


@router.get("/health")
def audit_health():
    return {"status": "ok"}
