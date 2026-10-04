"""
Entidad User: perfil del usuario.

NO contiene credenciales (password_hash, tokens OAuth).
Esas viven en Identity. Así separamos datos públicos de sensibles.
"""

from dataclasses import dataclass, field, replace
from uuid import uuid4


def _generate_id() -> str:
    """Genera un UUID nuevo como string."""
    return str(uuid4())


@dataclass(frozen=True)
class User:
    """
    Usuario del sistema.

    Inmutable. Cualquier cambio genera una nueva instancia
    mediante los métodos `with_*`.
    """

    username: str
    id: str = field(default_factory=_generate_id)
    email: str | None = None
    full_name: str | None = None
    roles: tuple[str, ...] = ("user",)
    disabled: bool = False

    # ==========================================
    # Consultas
    # ==========================================

    def has_role(self, role: str) -> bool:
        """Verifica si el usuario tiene un rol específico."""
        return role in self.roles

    def is_admin(self) -> bool:
        """Atajo: verifica si el usuario es admin."""
        return self.has_role("admin")

    # ==========================================
    # Actualizaciones (devuelven nueva instancia)
    # ==========================================

    def with_username(self, username: str) -> "User":
        return replace(self, username=username)

    def with_email(self, email: str | None) -> "User":
        return replace(self, email=email)

    def with_full_name(self, full_name: str | None) -> "User":
        return replace(self, full_name=full_name)

    def with_roles(self, roles: tuple[str, ...]) -> "User":
        return replace(self, roles=roles)

    def with_disabled(self, disabled: bool) -> "User":
        return replace(self, disabled=disabled)
