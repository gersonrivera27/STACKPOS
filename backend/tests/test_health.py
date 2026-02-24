"""
Tests for health and root endpoints.
These are the simplest tests — they verify the API is running.
"""


def test_root_endpoint(client):
    """Test GET / returns API info"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Burger POS API"
    assert data["status"] == "running"
    assert "version" in data
    assert "endpoints" in data


def test_root_has_expected_endpoints(client):
    """Test that root endpoint lists all expected API sections"""
    response = client.get("/")
    data = response.json()
    endpoints = data["endpoints"]

    expected_keys = ["docs", "categories", "products", "orders",
                     "modifiers", "tables", "reports", "customers", "cash"]
    for key in expected_keys:
        assert key in endpoints, f"Missing endpoint: {key}"


def test_health_endpoint(client):
    """Test GET /health returns healthy status"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_nonexistent_endpoint_returns_404(client):
    """Test that unknown routes return 404"""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
