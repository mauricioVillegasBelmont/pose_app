"""Puerto de autenticación."""

from abc import ABC, abstractmethod

from pose_app.domain.entities.user import User


class AuthPort(ABC):
    """Contrato para autenticar usuarios."""

    @abstractmethod
    def authenticate(self, username: str, password: str) -> User | None:
        """
        Valida credenciales.

        Returns:
            User si las credenciales son válidas, None si no.
        """

    @abstractmethod
    def get_user(self, username: str) -> User | None:
        """Obtiene un usuario por username."""
