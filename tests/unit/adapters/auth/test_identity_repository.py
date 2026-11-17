"""
Tests unitarios de InMemoryIdentityRepository.
"""

import pytest

from pose_app.adapters.auth.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from pose_app.domain.entities.identity import Identity


@pytest.fixture
def repo() -> InMemoryIdentityRepository:
    return InMemoryIdentityRepository()


class TestInMemoryIdentityRepository:
    def test_create_and_get(self, repo):
        identity = Identity(
            user_id="user-1",
            provider="password",
            provider_user_id="admin",
            password_hash="hash123",
        )
        repo.create(identity)
        fetched = repo.get_by_provider("password", "admin")
        assert fetched == identity

    def test_get_nonexistent(self, repo):
        assert repo.get_by_provider("password", "nobody") is None

    def test_create_duplicate_raises(self, repo):
        i1 = Identity(
            user_id="user-1",
            provider="password",
            provider_user_id="admin",
        )
        repo.create(i1)

        i2 = Identity(
            user_id="user-2",
            provider="password",
            provider_user_id="admin",
        )
        with pytest.raises(ValueError, match="ya existe"):
            repo.create(i2)

    def test_get_by_user_id_returns_all_identities(self, repo):
        repo.create(
            Identity(
                user_id="user-1",
                provider="password",
                provider_user_id="alice",
            )
        )
        repo.create(
            Identity(
                user_id="user-1",
                provider="google",
                provider_user_id="google-sub-123",
            )
        )
        repo.create(
            Identity(
                user_id="user-2",
                provider="password",
                provider_user_id="bob",
            )
        )

        alice_identities = repo.get_by_user_id("user-1")
        assert len(alice_identities) == 2
        providers = {i.provider for i in alice_identities}
        assert providers == {"password", "google"}

    def test_get_by_user_id_empty(self, repo):
        assert repo.get_by_user_id("unknown") == []

    def test_update_existing(self, repo):
        identity = Identity(
            user_id="user-1",
            provider="password",
            provider_user_id="admin",
            password_hash="old",
        )
        repo.create(identity)

        updated = Identity(
            user_id="user-1",
            provider="password",
            provider_user_id="admin",
            password_hash="new",
        )
        repo.update(updated)

        fetched = repo.get_by_provider("password", "admin")
        assert fetched.password_hash == "new"

    def test_update_nonexistent_raises(self, repo):
        identity = Identity(
            user_id="user-1",
            provider="password",
            provider_user_id="ghost",
        )
        with pytest.raises(ValueError, match="no existe"):
            repo.update(identity)

    def test_delete_removes_identity(self, repo):
        repo.create(
            Identity(
                user_id="user-1",
                provider="password",
                provider_user_id="alice",
            )
        )
        repo.create(
            Identity(
                user_id="user-1",
                provider="google",
                provider_user_id="google-123",
            )
        )

        repo.delete("user-1", "password")

        assert repo.get_by_provider("password", "alice") is None
        assert repo.get_by_provider("google", "google-123") is not None

    def test_delete_nonexistent_is_idempotent(self, repo):
        repo.delete("nonexistent", "password")  # No debe explotar
