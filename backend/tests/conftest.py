"""
Pytest configuration and fixtures for StackPOS backend tests.

Mocks external dependencies (RabbitMQ, database) so tests run
without Docker or real services — perfect for CI.
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock

# =====================================================
# Set test environment BEFORE importing anything
# =====================================================
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci-cd-pipeline"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-ci-cd-pipeline"
os.environ["RABBITMQ_ENABLED"] = "false"
os.environ["GOOGLE_MAPS_API_KEY"] = ""

# =====================================================
# Mock external modules that are only in Docker
# =====================================================
mock_aio_pika = MagicMock()
mock_aio_pika.RobustConnection = MagicMock()
mock_aio_pika.abc = MagicMock()
mock_aio_pika.abc.AbstractRobustChannel = MagicMock()
mock_aio_pika.connect_robust = AsyncMock()
mock_aio_pika.Message = MagicMock()
mock_aio_pika.DeliveryMode = MagicMock()
mock_aio_pika.DeliveryMode.PERSISTENT = 2
sys.modules["aio_pika"] = mock_aio_pika
sys.modules["pika"] = MagicMock()

# =====================================================
# Now safe to import the app
# =====================================================
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db


def mock_get_db():
    """Mock database dependency — returns a MagicMock connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = []
    try:
        yield mock_conn
    finally:
        pass


# Override the DB dependency globally for all tests
app.dependency_overrides[get_db] = mock_get_db

from app.security import obtener_usuario_actual

def override_obtener_usuario_actual():
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@burgerpos.com",
        "role": "admin",
        "is_active": True,
        "created_at": "2023-01-01T00:00:00Z"
    }

app.dependency_overrides[obtener_usuario_actual] = override_obtener_usuario_actual


@pytest.fixture(scope="session")
def client():
    """Create a test client — no real DB or RabbitMQ needed"""
    with TestClient(app) as c:
        yield c
