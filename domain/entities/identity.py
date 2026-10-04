"""
Entidad Identity: credenciales de autenticación.

Vincula un usuario con un método de autenticación específico:
- provider="password" → password_hash
- provider="google"   → provider_user_id (sub de Google)
- provider="github"   → provider_user_id (id de GitHub)

Un usuario puede tener múltiples identidades (login con password O Google).
"""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime


def _now() -> datetime:
    """Timestamp UTC actual."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class Identity:
    """
    Identidad de autenticación.

    Inmutable. Cada Identity representa UN método de auth para UN usuario.
    """

    user_id: str
    provider: str  # "password", "google", "github", etc.
    provider_user_id: str  # Identificador dentro del provider
    password_hash: str | None = None  # Solo si provider="password"
    created_at: datetime = field(default_factory=_now)
    last_login_at: datetime | None = None

    @property
    def is_password(self) -> bool:
        """Atajo: ¿es una identidad de tipo password?"""
        return self.provider == "password"

    def with_last_login(self, when: datetime | None = None) -> "Identity":
        """Devuelve una nueva Identity con el último login actualizado."""
        return replace(self, last_login_at=when or _now())
