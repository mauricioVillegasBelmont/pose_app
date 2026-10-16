"""Servicio de generación y validación de tokens JWT."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from pose_app.config.settings import JWTSettings
from pose_app.domain.entities.user import User
from pose_app.infrastructure.errors.exceptions import AppError


class TokenError(AppError):
    """Error al validar un token JWT."""


class JWTService:
    """Genera y valida tokens JWT."""

    def __init__(self, settings: JWTSettings):
        self._settings = settings

    def create_access_token(
        self,
        user: User,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Crea un token JWT para el usuario."""
        now = datetime.now(UTC)

        if expires_delta is None:
            expires_delta = timedelta(
                minutes=self._settings.access_token_expire_minutes
            )

        payload = {
            "sub": user.username,
            "roles": list(user.roles),
            "full_name": user.full_name,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
        }

        return jwt.encode(
            payload,
            self._settings.secret_key,
            algorithm=self._settings.algorithm,
        )

    def decode_token(self, token: str) -> dict:
        """
        Decodifica y valida un token.

        Raises:
            TokenError: si el token es inválido, expirado o malformado.
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.secret_key,
                algorithms=[self._settings.algorithm],
            )
            return payload
        except JWTError as e:
            raise TokenError(
                f"Token inválido: {e}",
                context={"error": str(e)},
            ) from e
