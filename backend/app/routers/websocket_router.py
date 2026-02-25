"""
WebSocket router for real-time order updates to the Kitchen Display System (KDS)
and other clients.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Any, Optional
import json
import logging

from ..security import decodificar_token

logger = logging.getLogger(__name__)

# Límite de tamaño máximo por mensaje entrante (64 KB).
# Protege contra clientes que envíen payloads gigantes para agotar la memoria.
MAX_WS_MESSAGE_BYTES = 64 * 1024  # 64 KB

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_order_update(self, order_data: Dict[str, Any], event_type: str = "order_updated"):
        """Broadcasts an order update to all connected clients."""
        if not self.active_connections:
            return

        message = {
            "type": event_type,
            "data": order_data
        }

        # Serialize datetime and other objects appropriately
        json_msg = json.dumps(message, default=str)

        for connection in self.active_connections:
            try:
                await connection.send_text(json_msg)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                # We'll rely on the handler's WebSocketDisconnect to clean up stale connections

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint con autenticación por JWT.
    El cliente debe pasar el token como query param: /api/ws?token=<JWT>
    """
    # Validar token antes de aceptar la conexión
    if not token:
        await websocket.close(code=4001, reason="Token requerido")
        return

    try:
        payload = decodificar_token(token)
        usuario_id = payload.get("usuario_id")
        if not usuario_id:
            await websocket.close(code=4001, reason="Token inválido")
            return
    except Exception:
        await websocket.close(code=4001, reason="Token inválido o expirado")
        return

    await manager.connect(websocket)
    try:
        # Acknowledge connection
        await websocket.send_text(json.dumps({"type": "connection_established", "message": "WebSocket active"}))
        while True:
            # Drain incoming messages but ignore content for now
            # In a full flow, KDS could send "mark_ready" events via WS,
            # but currently they hit REST endpoints.
            data = await websocket.receive_text()
            if len(data.encode("utf-8")) > MAX_WS_MESSAGE_BYTES:
                logger.warning(
                    f"WebSocket message too large ({len(data.encode('utf-8'))} bytes). Closing connection."
                )
                await websocket.close(code=1009, reason="Message too large")
                manager.disconnect(websocket)
                return
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Helper functions for the REST endpoints to call
async def notify_order_change(order_data: dict, event_type: str = "order_updated"):
    await manager.broadcast_order_update(order_data, event_type)

async def notify_kitchen_update(order_data: dict):
    await manager.broadcast_order_update(order_data, "kitchen_update")
