"""
Tests for Eircode geocoding endpoint.
Tests validation, prefix map, and response format.
"""
import pytest
from unittest.mock import patch, AsyncMock


def test_geocoding_empty_eircode(client):
    """Test that empty eircode returns 400"""
    response = client.get("/api/geocoding/eircode?code=")
    assert response.status_code == 400


def test_geocoding_missing_eircode_param(client):
    """Test that missing eircode param returns 422"""
    response = client.get("/api/geocoding/eircode")
    assert response.status_code == 422


def test_geocoding_valid_eircode_prefix_a92(client):
    """Test that A92 prefix returns Drogheda area"""
    # Mock external calls to avoid hitting real APIs
    with patch("app.routers.geocoding.call_google_geocode", new_callable=AsyncMock, return_value=None):
        with patch("app.routers.geocoding.call_nominatim_reverse", new_callable=AsyncMock, return_value=None):
            response = client.get("/api/geocoding/eircode?code=A92XXXX")

    assert response.status_code == 200
    data = response.json()
    assert data["found"] == True
    assert data["city"] == "Drogheda"
    assert data["county"] == "Louth"
    assert data["eircode"] == "A92XXXX"


def test_geocoding_valid_eircode_prefix_d02(client):
    """Test that D02 prefix returns Dublin"""
    with patch("app.routers.geocoding.call_google_geocode", new_callable=AsyncMock, return_value=None):
        with patch("app.routers.geocoding.call_nominatim_reverse", new_callable=AsyncMock, return_value=None):
            response = client.get("/api/geocoding/eircode?code=D02XXXX")

    assert response.status_code == 200
    data = response.json()
    assert data["found"] == True
    assert data["city"] == "Dublin"
    assert data["county"] == "Dublin"


def test_geocoding_unknown_prefix_returns_not_found(client):
    """Test that unknown prefix returns found=false"""
    with patch("app.routers.geocoding.call_google_geocode", new_callable=AsyncMock, return_value=None):
        response = client.get("/api/geocoding/eircode?code=Z99XXXX")

    assert response.status_code == 200
    data = response.json()
    assert data["found"] == False


def test_geocoding_response_format(client):
    """Test that response has all expected fields"""
    with patch("app.routers.geocoding.call_google_geocode", new_callable=AsyncMock, return_value=None):
        with patch("app.routers.geocoding.call_nominatim_reverse", new_callable=AsyncMock, return_value=None):
            response = client.get("/api/geocoding/eircode?code=A92D65P")

    assert response.status_code == 200
    data = response.json()

    expected_fields = ["found", "address_line1", "city", "county",
                       "eircode", "latitude", "longitude"]
    for field in expected_fields:
        assert field in data, f"Missing field: {field}"


def test_geocoding_cleans_eircode_format(client):
    """Test that eircode with spaces is cleaned properly"""
    with patch("app.routers.geocoding.call_google_geocode", new_callable=AsyncMock, return_value=None):
        with patch("app.routers.geocoding.call_nominatim_reverse", new_callable=AsyncMock, return_value=None):
            response = client.get("/api/geocoding/eircode?code=A92 D65P")

    assert response.status_code == 200
    data = response.json()
    assert data["found"] == True
    assert data["eircode"] == "A92D65P"  # Cleaned (no spaces)


def test_geocoding_lowercase_eircode(client):
    """Test that lowercase eircode is uppercased"""
    with patch("app.routers.geocoding.call_google_geocode", new_callable=AsyncMock, return_value=None):
        with patch("app.routers.geocoding.call_nominatim_reverse", new_callable=AsyncMock, return_value=None):
            response = client.get("/api/geocoding/eircode?code=a92d65p")

    assert response.status_code == 200
    data = response.json()
    assert data["eircode"] == "A92D65P"
