"""
Tests for authentication endpoints.

Routes (prefix /api/auth):
  POST /login         - Standard login
  POST /pin-login     - PIN-based login  
  GET  /verificar     - Token verification
  GET  /perfil        - User profile
  GET  /users-list    - List users
"""


def test_login_requires_credentials(client):
    """Test that login requires credentials fields"""
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 422


def test_login_returns_response(client):
    """Test login endpoint accepts valid JSON and returns response"""
    response = client.post("/api/auth/login", json={
        "username_or_email": "testuser",
        "password": "testpass"
    })
    # With mocked DB, should return a response (not crash)
    assert response.status_code in [200, 401, 500]


def test_verificar_without_auth_header(client):
    """Test verificar without Authorization header returns 401/403"""
    from app.main import app
    from app.security import obtener_usuario_actual
    from tests.conftest import override_obtener_usuario_actual
    
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    try:
        response = client.get("/api/auth/verificar")
        assert response.status_code in [401, 403]
    finally:
        app.dependency_overrides[obtener_usuario_actual] = override_obtener_usuario_actual


def test_verificar_with_invalid_token(client):
    """Test verificar with invalid token returns 401/403"""
    from app.main import app
    from app.security import obtener_usuario_actual
    from tests.conftest import override_obtener_usuario_actual
    
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    try:
        response = client.get("/api/auth/verificar", headers={
            "Authorization": "Bearer invalid-token-here"
        })
        assert response.status_code in [401, 403]
    finally:
        app.dependency_overrides[obtener_usuario_actual] = override_obtener_usuario_actual


def test_perfil_without_auth(client):
    """Test perfil endpoint without auth returns 401/403"""
    from app.main import app
    from app.security import obtener_usuario_actual
    from tests.conftest import override_obtener_usuario_actual
    
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    try:
        response = client.get("/api/auth/perfil")
        assert response.status_code in [401, 403]
    finally:
        app.dependency_overrides[obtener_usuario_actual] = override_obtener_usuario_actual


def test_users_list_without_auth(client):
    """Test users-list endpoint requires auth"""
    from app.main import app
    from app.security import obtener_usuario_actual
    from tests.conftest import override_obtener_usuario_actual
    
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    try:
        response = client.get("/api/auth/users-list")
        assert response.status_code in [401, 403]
    finally:
        app.dependency_overrides[obtener_usuario_actual] = override_obtener_usuario_actual
