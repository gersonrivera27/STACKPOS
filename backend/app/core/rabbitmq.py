"""
RabbitMQ client using aio-pika.
Falls back gracefully (logs warning) if the broker is unreachable.
"""
import json
import logging
from datetime import datetime

import aio_pika
from ..config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Async RabbitMQ client wrapping aio-pika."""

    def __init__(self):
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractRobustChannel | None = None
        self.connected = False

    async def connect(self):
        """Establish a robust (auto-reconnecting) connection to RabbitMQ."""
        self.connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL,
            reconnect_interval=5,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        # Declare durable queues so they survive broker restarts
        await self.channel.declare_queue("audit.auth", durable=True)
        await self.channel.declare_queue("audit.orders", durable=True)
        await self.channel.declare_queue("audit.security", durable=True)

        self.connected = True
        logger.info("✅ RabbitMQ connected to %s", settings.RABBITMQ_URL)

    async def close(self):
        """Close channel and connection cleanly."""
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        self.connected = False
        logger.info("🔌 RabbitMQ connection closed.")

    async def _publish(self, queue_name: str, payload: dict):
        """Serialize payload and publish to a named queue."""
        if not self.connected or self.channel is None:
            logger.warning(
                "RabbitMQ not connected – dropping message to %s: %s",
                queue_name,
                payload,
            )
            return
        try:
            payload.setdefault("timestamp", datetime.utcnow().isoformat())
            body = json.dumps(payload, default=str).encode()
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type="application/json",
                ),
                routing_key=queue_name,
            )
            logger.debug("Published to %s: %s", queue_name, payload)
        except Exception as exc:
            logger.error("Failed to publish to %s: %s", queue_name, exc)

    # -----------------------------------------------------------------------
    # Public helpers — same interface the auth router already uses
    # -----------------------------------------------------------------------

    async def publish_security_event(self, **payload):
        """Publish a security event to audit.security queue."""
        await self._publish("audit.security", dict(payload))

    async def publish_auth_event(self, **payload):
        """Publish an auth event to audit.auth queue."""
        await self._publish("audit.auth", dict(payload))

    async def publish_order_event(self, **payload):
        """Publish an order lifecycle event to audit.orders queue."""
        await self._publish("audit.orders", dict(payload))


def get_client_ip(request) -> str:
    """Extract real client IP, respecting X-Forwarded-For."""
    if not request:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Singleton used across the app
mq = RabbitMQClient()

RABBITMQ_ENABLED = settings.RABBITMQ_ENABLED
