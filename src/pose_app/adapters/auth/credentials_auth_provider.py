"""
Proveedor de autenticación por credenciales (username + password).

Colabora con:
- UserRepositoryPort: obtiene perfiles
- IdentityRepositoryPort: obtiene hashes de password
"""

from pose_app.adapters.auth.password_hasher import (
    verify_dummy_password,
    verify_password,
)
from pose_app.domain.entities.user import User
from pose_app.domain.ports.auth_port import AuthPort
from pose_app.domain.ports.identity_repository_port import IdentityRepositoryPort
from pose_app.domain.ports.user_repository_port import UserRepositoryPort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.auth.credentials")


class CredentialsAuthProvider(AuthPort):
    """Autenticación con usuario + contraseña."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        identity_repository: IdentityRepositoryPort,
    ):
        self._users = user_repository
        self._identities = identity_repository

    def authenticate(self, username: str, password: str) -> User | None:
        """
        Valida credenciales.

        Flujo:
            1. Busca usuario por username.
            2. Si no existe → dummy hash (mitiga timing) → None.
            3. Busca identidad "password" del usuario.
            4. Verifica password con bcrypt.
            5. Actualiza last_login.
            6. Devuelve User (o None si password incorrecto).
        """
        user = self._users.get_by_username(username)

        if user is None:
            # Mitigación de timing attack: siempre hashea
            verify_dummy_password(password)
            logger.debug(f"Login fallido (usuario no existe): {username}")
            return None

        if user.disabled:
            # También mitigamos timing aquí
            verify_dummy_password(password)
            logger.warning(f"Login fallido (usuario deshabilitado): {username}")
            return None

        identity = self._identities.get_by_provider("password", username)

        if identity is None or identity.password_hash is None:
            verify_dummy_password(password)
            logger.debug(f"Login fallido (sin identidad password): {username}")
            return None

        if not verify_password(password, identity.password_hash):
            logger.debug(f"Login fallido (password incorrecto): {username}")
            return None

        # Actualiza last_login
        self._identities.update(identity.with_last_login())

        logger.info(f"Login exitoso: {username}")
        return user

    def get_user(self, username: str) -> User | None:
        """Obtiene un usuario por username (sin validar password)."""
        return self._users.get_by_username(username)
