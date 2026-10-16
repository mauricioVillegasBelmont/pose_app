"""
Tests unitarios de InMemoryUserRepository.
"""

import pytest

from pose_app.adapters.auth.in_memory_user_repository import InMemoryUserRepository
from pose_app.domain.entities.user import User


@pytest.fixture
def repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


class TestInMemoryUserRepository:
    def test_create_and_get_by_id(self, repo):
        user = User(username="alice", email="alice@x.com")
        repo.create(user)
        fetched = repo.get_by_id(user.id)
        assert fetched == user

    def test_get_by_username(self, repo):
        user = User(username="alice")
        repo.create(user)
        assert repo.get_by_username("alice") == user

    def test_get_by_username_nonexistent(self, repo):
        assert repo.get_by_username("nobody") is None

    def test_get_by_id_nonexistent(self, repo):
        assert repo.get_by_id("nonexistent-id") is None

    def test_create_duplicate_username_raises(self, repo):
        repo.create(User(username="alice"))
        with pytest.raises(ValueError, match="ya existe"):
            repo.create(User(username="alice"))

    def test_update_existing_user(self, repo):
        user = User(username="alice")
        repo.create(user)
        updated = user.with_email("new@x.com")
        repo.update(updated)
        assert repo.get_by_id(user.id).email == "new@x.com"

    def test_update_nonexistent_raises(self, repo):
        user = User(username="ghost")
        with pytest.raises(ValueError, match="no existe"):
            repo.update(user)

    def test_update_username_updates_index(self, repo):
        user = User(username="alice")
        repo.create(user)
        renamed = user.with_username("alicia")
        repo.update(renamed)

        assert repo.get_by_username("alice") is None
        assert repo.get_by_username("alicia") is not None

    def test_update_to_existing_username_raises(self, repo):
        alice = User(username="alice")
        bob = User(username="bob")
        repo.create(alice)
        repo.create(bob)

        with pytest.raises(ValueError, match="ya existe"):
            repo.update(bob.with_username("alice"))

    def test_delete_removes_user(self, repo):
        user = User(username="alice")
        repo.create(user)
        repo.delete(user.id)
        assert repo.get_by_id(user.id) is None
        assert repo.get_by_username("alice") is None

    def test_delete_nonexistent_is_idempotent(self, repo):
        repo.delete("nonexistent-id")  # No debe explotar

    def test_list_all(self, repo):
        repo.create(User(username="alice"))
        repo.create(User(username="bob"))
        repo.create(User(username="charlie"))
        users = repo.list_all()
        usernames = {u.username for u in users}
        assert usernames == {"alice", "bob", "charlie"}
