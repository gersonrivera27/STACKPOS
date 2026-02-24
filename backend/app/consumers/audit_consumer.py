"""
Audit consumer: reads messages from the three audit queues and
persists them to the audit_logs table in PostgreSQL.
"""
import asyncio
import json
import logging
import os

import aio_pika
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
DATABASE_URL = os.getenv("DATABASE_URL", "")

QUEUES = ["audit.auth", "audit.orders", "audit.security"]


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def save_audit_log(conn, message: dict):
    """Persist one audit event to audit_logs."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_logs (event, username, user_id, ip_address, details)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                message.get("event", "unknown"),
                message.get("username"),
                message.get("user_id"),
                message.get("ip_address"),
                json.dumps(message),
            ),
        )
    conn.commit()


async def process_message(message: aio_pika.IncomingMessage, db_conn):
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            logger.info("Audit event received: %s", payload.get("event"))
            save_audit_log(db_conn, payload)
        except Exception as exc:
            logger.error("Error processing audit message: %s", exc)
            try:
                db_conn.rollback()
            except Exception:
                pass


async def main():
    # Wait for RabbitMQ to be ready (useful on first docker-compose up)
    await asyncio.sleep(5)

    db_conn = None
    connection = None

    try:
        db_conn = get_db_connection()
        logger.info("✅ Audit consumer connected to database.")

        connection = await aio_pika.connect_robust(
            RABBITMQ_URL,
            reconnect_interval=5,
        )
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=5)

        for queue_name in QUEUES:
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.consume(lambda msg, q=queue_name: process_message(msg, db_conn))
            logger.info("✅ Consuming from queue: %s", queue_name)

        logger.info("🟢 Audit consumer running. Waiting for messages...")

        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            logger.info("Audit consumer stopping.")

    except Exception as exc:
        logger.error("Audit consumer fatal error: %s", exc)
        raise
    finally:
        if connection and not connection.is_closed:
            await connection.close()
        if db_conn:
            db_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
