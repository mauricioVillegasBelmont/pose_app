"""Tests del servicio JWT."""

from datetime import timedelta

import pytest

from pose_app.config.settings import JWTSettings
from pose_app.domain.entities.user import User
from pose_app.infrastructure.auth.jwt_service import JWTService, TokenError


@pytest.fixture
def jwt_settings() -> JWTSettings:
    return JWTSettings(
        secret_key="test-secret-key-at-least-32-characters-long",
        algorithm="HS256",
        access_token_expire_minutes=60,
    )


@pytest.fixture
def jwt_service(jwt_settings: JWTSettings) -> JWTService:
    return JWTService(jwt_settings)


@pytest.fixture
def user() -> User:
    return User(username="test", full_name="Test User", roles=("user",))


class TestJWTService:
    def test_create_and_decode_token(self, jwt_service, user):
        """Un token recién creado se decodifica correctamente."""
        token = jwt_service.create_access_token(user)
        payload = jwt_service.decode_token(token)

        assert payload["sub"] == "test"
        assert "user" in payload["roles"]
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_token_raises(self, jwt_service, user):
        """Un token expirado lanza TokenError."""
        token = jwt_service.create_access_token(
            user, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(TokenError):
            jwt_service.decode_token(token)

    def test_invalid_token_raises(self, jwt_service):
        """Un token malformado lanza TokenError."""
        with pytest.raises(TokenError):
            jwt_service.decode_token("not-a-valid-token")

    def test_token_with_wrong_secret_raises(self, user):
        """Un token firmado con otro secret no se valida."""
        service1 = JWTService(JWTSettings(secret_key="a" * 32, algorithm="HS256"))
        service2 = JWTService(JWTSettings(secret_key="b" * 32, algorithm="HS256"))

        token = service1.create_access_token(user)
        with pytest.raises(TokenError):
            service2.decode_token(token)
