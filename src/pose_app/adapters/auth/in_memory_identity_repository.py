"""
Repositorio de identidades en memoria.

Thread-safe.
"""

from threading import Lock

from pose_app.domain.entities.identity import Identity
from pose_app.domain.ports.identity_repository_port import IdentityRepositoryPort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.auth.in_memory_identity")


class InMemoryIdentityRepository(IdentityRepositoryPort):
    """Repositorio de identidades en memoria, thread-safe."""

    def __init__(self) -> None:
        self._lock = Lock()
        # Clave: (provider, provider_user_id) → Identity
        self._by_provider: dict[tuple[str, str], Identity] = {}
        # Clave: user_id → lista de identidades
        self._by_user_id: dict[str, list[Identity]] = {}

    def get_by_provider(self, provider: str, provider_user_id: str) -> Identity | None:
        with self._lock:
            return self._by_provider.get((provider, provider_user_id))

    def get_by_user_id(self, user_id: str) -> list[Identity]:
        with self._lock:
            return list(self._by_user_id.get(user_id, []))

    def create(self, identity: Identity) -> Identity:
        with self._lock:
            key = (identity.provider, identity.provider_user_id)
            if key in self._by_provider:
                raise ValueError(
                    f"Identidad ya existe: {identity.provider}"
                    f"/{identity.provider_user_id}"
                )

            self._by_provider[key] = identity
            self._by_user_id.setdefault(identity.user_id, []).append(identity)

            logger.debug(
                f"Identidad creada: {identity.provider} → user_id={identity.user_id}"
            )
            return identity

    def update(self, identity: Identity) -> Identity:
        with self._lock:
            key = (identity.provider, identity.provider_user_id)
            if key not in self._by_provider:
                raise ValueError(
                    f"Identidad no existe: {identity.provider}"
                    f"/{identity.provider_user_id}"
                )

            self._by_provider[key] = identity

            # Actualiza la lista del usuario
            user_identities = self._by_user_id.get(identity.user_id, [])
            self._by_user_id[identity.user_id] = [
                identity
                if (
                    i.provider == identity.provider
                    and i.provider_user_id == identity.provider_user_id
                )
                else i
                for i in user_identities
            ]

            return identity

    def delete(self, user_id: str, provider: str) -> None:
        with self._lock:
            user_identities = self._by_user_id.get(user_id, [])
            to_remove = [i for i in user_identities if i.provider == provider]

            for identity in to_remove:
                key = (identity.provider, identity.provider_user_id)
                self._by_provider.pop(key, None)

            self._by_user_id[user_id] = [
                i for i in user_identities if i.provider != provider
            ]

            logger.debug(f"Identidad eliminada: user_id={user_id}, provider={provider}")
