"""Tests de endpoints de autenticación."""

import pytest
from fastapi.testclient import TestClient

from pose_app.adapters.api.fastapi_adapter import FastAPIAdapter
from pose_app.app.state_registry import StateRegistry
from pose_app.config.settings import JWTSettings, Settings, reset_settings
from pose_app.infrastructure.events.async_event_bus import AsyncEventBus


@pytest.fixture
def test_settings() -> Settings:
    """Settings deterministas para tests."""
    reset_settings()
    return Settings(
        environment="testing",
        jwt=JWTSettings(
            secret_key="abcdefghijklmnopqrstuvwxyz123456",
            algorithm="HS256",
            access_token_expire_minutes=60,
        ),
        _env_file=None,
    )


@pytest.fixture
def client(test_settings) -> TestClient:
    """TestClient con auth configurada automáticamente."""
    event_bus = AsyncEventBus()
    registry = StateRegistry()
    adapter = FastAPIAdapter(
        settings=test_settings,
        event_bus=event_bus,
        registry=registry,
    )
    return TestClient(adapter.app)


@pytest.fixture
def valid_token(client) -> str:
    """Token válido obtenido via /auth/token."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestAuthEndpoints:
    def test_login_with_valid_credentials(self, client):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_invalid_password(self, client):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_login_with_unknown_user(self, client):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "unknown", "password": "whatever"},
        )
        assert response.status_code == 401

    def test_me_requires_token(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_with_valid_token(self, client, valid_token):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert "admin" in data["roles"]

    def test_me_with_invalid_token(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer garbage-token"},
        )
        assert response.status_code == 401

    def test_me_with_malformed_header(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "NotBearer xyz"},
        )
        assert response.status_code == 401


class TestProtectedRoutes:
    def test_state_requires_auth(self, client):
        response = client.get("/api/v1/state")
        assert response.status_code == 401

    def test_state_with_valid_token(self, client, valid_token):
        response = client.get(
            "/api/v1/state",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_health_is_public(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200


class TestClientIsolation:
    """
    Tests de aislamiento entre múltiples instancias de FastAPIAdapter.

    Verifican que cada app es independiente (usa app.state, no globales).
    """

    def test_two_clients_with_different_secrets(self):
        """
        Dos clientes con distinto secret deben ser independientes.

        Con el diseño anterior (globals), un token firmado por client_a
        sería válido en client_b, porque compartían el mismo JWTService.

        Con app.state, cada cliente tiene su propio JWTService y el
        token de client_a es RECHAZADO por client_b.
        """

        settings_a = Settings(
            environment="testing",
            jwt=JWTSettings(
                secret_key="a" * 32,
                algorithm="HS256",
                access_token_expire_minutes=60,
            ),
            _env_file=None,
        )
        settings_b = Settings(
            environment="testing",
            jwt=JWTSettings(
                secret_key="b" * 32,
                algorithm="HS256",
                access_token_expire_minutes=60,
            ),
            _env_file=None,
        )

        # Cada adapter configura su propio app.state (sin globals)
        adapter_a = FastAPIAdapter(
            settings=settings_a,
            event_bus=AsyncEventBus(),
            registry=StateRegistry(),
        )
        client_a = TestClient(adapter_a.app)

        adapter_b = FastAPIAdapter(
            settings=settings_b,
            event_bus=AsyncEventBus(),
            registry=StateRegistry(),
        )
        client_b = TestClient(adapter_b.app)

        # 1. Login en A → token firmado con secret "aaa..."
        resp_login = client_a.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
        )
        assert resp_login.status_code == 200
        token_from_a = resp_login.json()["access_token"]

        # 2. El mismo token usado en A → válido
        resp_a = client_a.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_from_a}"},
        )
        assert resp_a.status_code == 200
        assert resp_a.json()["username"] == "admin"

        # 3. El token de A usado en B → INVÁLIDO (secret distinto)
        resp_b = client_b.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_from_a}"},
        )
        assert resp_b.status_code == 401, (
            "El token de client_a NO debe ser válido en client_b. "
            "Si este assert falla, los clientes están compartiendo "
            "el JWTService (bug de diseño)."
        )

    def test_two_clients_can_login_independently(self):
        """
        Cada cliente puede autenticar con su propio secret sin interferir.
        """

        settings_a = Settings(
            environment="testing",
            jwt=JWTSettings(
                secret_key="a" * 32,
                algorithm="HS256",
                access_token_expire_minutes=60,
            ),
            _env_file=None,
        )
        settings_b = Settings(
            environment="testing",
            jwt=JWTSettings(
                secret_key="b" * 32,
                algorithm="HS256",
                access_token_expire_minutes=60,
            ),
            _env_file=None,
        )

        adapter_a = FastAPIAdapter(
            settings=settings_a,
            event_bus=AsyncEventBus(),
            registry=StateRegistry(),
        )
        client_a = TestClient(adapter_a.app)

        adapter_b = FastAPIAdapter(
            settings=settings_b,
            event_bus=AsyncEventBus(),
            registry=StateRegistry(),
        )
        client_b = TestClient(adapter_b.app)

        # Ambos pueden loguearse
        token_a = client_a.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
        ).json()["access_token"]

        token_b = client_b.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
        ).json()["access_token"]

        # Los tokens son distintos (secret distinto)
        assert token_a != token_b

        # Cada uno funciona en su propio cliente
        me_a = client_a.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert me_a.status_code == 200

        me_b = client_b.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert me_b.status_code == 200

        # Intercambio cruzado → 401
        cross_a_in_b = client_b.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert cross_a_in_b.status_code == 401

        cross_b_in_a = client_a.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert cross_b_in_a.status_code == 401
