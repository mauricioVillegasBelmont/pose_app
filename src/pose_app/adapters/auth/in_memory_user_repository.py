"""
Repositorio de usuarios en memoria.

Vive en RAM. Se puebla desde JSON al inicio.
"""

from threading import Lock

from pose_app.domain.entities.user import User
from pose_app.domain.ports.user_repository_port import UserRepositoryPort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.auth.in_memory_user")


class InMemoryUserRepository(UserRepositoryPort):
    """Repositorio de usuarios en memoria, thread-safe."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._users_by_id: dict[str, User] = {}
        self._id_by_username: dict[str, str] = {}

    def get_by_id(self, user_id: str) -> User | None:
        with self._lock:
            return self._users_by_id.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        with self._lock:
            user_id = self._id_by_username.get(username)
            if user_id is None:
                return None
            return self._users_by_id.get(user_id)

    def create(self, user: User) -> User:
        with self._lock:
            if user.username in self._id_by_username:
                raise ValueError(f"Username ya existe: {user.username}")

            self._users_by_id[user.id] = user
            self._id_by_username[user.username] = user.id

            logger.debug(f"Usuario creado: {user.username}")
            return user

    def update(self, user: User) -> User:
        with self._lock:
            if user.id not in self._users_by_id:
                raise ValueError(f"Usuario no existe: {user.id}")

            old_user = self._users_by_id[user.id]

            # Si cambió el username, actualiza el índice
            if old_user.username != user.username:
                del self._id_by_username[old_user.username]
                if user.username in self._id_by_username:
                    raise ValueError(f"Username ya existe: {user.username}")
                self._id_by_username[user.username] = user.id

            self._users_by_id[user.id] = user
            logger.debug(f"Usuario actualizado: {user.username}")
            return user

    def delete(self, user_id: str) -> None:
        with self._lock:
            user = self._users_by_id.pop(user_id, None)
            if user is not None:
                self._id_by_username.pop(user.username, None)
                logger.debug(f"Usuario eliminado: {user.username}")

    def list_all(self) -> list[User]:
        with self._lock:
            return list(self._users_by_id.values())
