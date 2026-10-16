"""
Puerto de repositorio de usuarios.

Solo gestiona perfiles. NO maneja credenciales (eso es IdentityRepositoryPort).
"""

from abc import ABC, abstractmethod

from pose_app.domain.entities.user import User


class UserRepositoryPort(ABC):
    """CRUD de usuarios (perfiles)."""

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        """Obtiene un usuario por su id."""

    @abstractmethod
    def get_by_username(self, username: str) -> User | None:
        """Obtiene un usuario por su username."""

    @abstractmethod
    def create(self, user: User) -> User:
        """
        Crea un usuario.

        Raises:
            ValueError: si el username ya existe.
        """

    @abstractmethod
    def update(self, user: User) -> User:
        """
        Actualiza un usuario existente.

        Raises:
            ValueError: si el usuario no existe.
        """

    @abstractmethod
    def delete(self, user_id: str) -> None:
        """Elimina un usuario por su id. Idempotente."""

    @abstractmethod
    def list_all(self) -> list[User]:
        """Lista todos los usuarios."""
