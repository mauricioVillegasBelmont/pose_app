"""
Tests unitarios de CredentialsAuthProvider.

Prueba la lógica de autenticación sin HTTP ni FastAPI.
"""

import pytest

from adapters.auth.credentials_auth_provider import (
    CredentialsAuthProvider,
)
from adapters.auth.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from adapters.auth.in_memory_user_repository import InMemoryUserRepository
from adapters.auth.password_hasher import hash_password
from domain.entities.identity import Identity
from domain.entities.user import User


@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def identity_repo() -> InMemoryIdentityRepository:
    return InMemoryIdentityRepository()


@pytest.fixture
def provider(
    user_repo: InMemoryUserRepository,
    identity_repo: InMemoryIdentityRepository,
) -> CredentialsAuthProvider:
    return CredentialsAuthProvider(
        user_repository=user_repo,
        identity_repository=identity_repo,
    )


@pytest.fixture
def admin_with_password(
    user_repo: InMemoryUserRepository,
    identity_repo: InMemoryIdentityRepository,
) -> User:
    """Crea un usuario admin con password."""
    user = User(
        username="admin",
        full_name="Admin",
        roles=("admin", "user"),
    )
    user_repo.create(user)
    identity_repo.create(
        Identity(
            user_id=user.id,
            provider="password",
            provider_user_id="admin",
            password_hash=hash_password("admin123"),
        )
    )
    return user


class TestCredentialsAuthProvider:
    def test_authenticate_valid_credentials(self, provider, admin_with_password):
        """Credenciales correctas → devuelve User."""
        user = provider.authenticate("admin", "admin123")
        assert user is not None
        assert user.username == "admin"
        assert user.is_admin()

    def test_authenticate_wrong_password(self, provider, admin_with_password):
        """Password incorrecto → None."""
        user = provider.authenticate("admin", "wrong")
        assert user is None

    def test_authenticate_unknown_user(self, provider):
        """Usuario desconocido → None."""
        user = provider.authenticate("unknown", "whatever")
        assert user is None

    def test_authenticate_disabled_user(self, user_repo, identity_repo):
        """Usuario deshabilitado → None (aunque credenciales OK)."""
        user = User(username="disabled", disabled=True)
        user_repo.create(user)
        identity_repo.create(
            Identity(
                user_id=user.id,
                provider="password",
                provider_user_id="disabled",
                password_hash=hash_password("pass12345"),
            )
        )
        provider = CredentialsAuthProvider(user_repo, identity_repo)
        assert provider.authenticate("disabled", "pass12345") is None

    def test_authenticate_updates_last_login(
        self, provider, admin_with_password, identity_repo
    ):
        """Tras login exitoso, last_login_at se actualiza."""
        identity_before = identity_repo.get_by_provider("password", "admin")
        assert identity_before.last_login_at is None

        provider.authenticate("admin", "admin123")

        identity_after = identity_repo.get_by_provider("password", "admin")
        assert identity_after.last_login_at is not None

    def test_get_user_returns_user(self, provider, admin_with_password):
        """get_user devuelve el User sin validar password."""
        user = provider.get_user("admin")
        assert user is not None
        assert user.username == "admin"

    def test_get_user_returns_none_for_unknown(self, provider):
        """get_user de usuario inexistente → None."""
        assert provider.get_user("unknown") is None

    def test_authenticate_user_without_identity(self, user_repo, identity_repo):
        """Usuario sin Identity de password → None."""
        user = User(username="oauth_only")
        user_repo.create(user)
        provider = CredentialsAuthProvider(user_repo, identity_repo)

        assert provider.authenticate("oauth_only", "any") is None
