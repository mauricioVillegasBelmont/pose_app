"""
Puerto de repositorio de identidades.

Maneja credenciales (password_hash, tokens OAuth).
"""

from abc import ABC, abstractmethod

from domain.entities.identity import Identity


class IdentityRepositoryPort(ABC):
    """CRUD de identidades."""

    @abstractmethod
    def get_by_provider(self, provider: str, provider_user_id: str) -> Identity | None:
        """
        Obtiene una identidad por (provider, provider_user_id).

        Ejemplo: get_by_provider("password", "admin")
        """

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> list[Identity]:
        """Lista todas las identidades de un usuario."""

    @abstractmethod
    def create(self, identity: Identity) -> Identity:
        """
        Crea una identidad.

        Raises:
            ValueError: si ya existe una identidad para ese
                       (provider, provider_user_id).
        """

    @abstractmethod
    def update(self, identity: Identity) -> Identity:
        """Actualiza una identidad existente."""

    @abstractmethod
    def delete(self, user_id: str, provider: str) -> None:
        """Elimina una identidad. Idempotente."""
