"""
Schemas (DTOs) para los endpoints de usuarios.

Traducen entre JSON (HTTP) y entidades del dominio.
NUNCA exponen el password_hash.
"""

from pydantic import BaseModel, EmailStr, Field

# ==========================================
# Requests
# ==========================================


class UserCreateRequest(BaseModel):
    """Payload para crear un usuario (admin)."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Solo minúsculas, números y guión bajo. Empieza con letra.",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Mínimo 8 caracteres.",
    )
    email: EmailStr | None = Field(default=None)
    full_name: str | None = Field(default=None, max_length=100)
    roles: list[str] = Field(
        default_factory=lambda: ["user"],
        description="Roles del usuario. Ej: ['user'], ['admin', 'user'].",
    )
    disabled: bool = Field(default=False)


class UserUpdateRequest(BaseModel):
    """
    Payload para actualizar (parcialmente) un usuario.

    Todos los campos son opcionales. Solo los presentes se actualizan.
    """

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=100)
    roles: list[str] | None = None
    disabled: bool | None = None


class PasswordChangeRequest(BaseModel):
    """Payload para cambiar la contraseña."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


# ==========================================
# Responses
# ==========================================


class UserResponse(BaseModel):
    """
    Datos públicos de un usuario.

    NUNCA incluye password_hash ni datos sensibles.
    """

    id: str
    username: str
    email: str | None
    full_name: str | None
    roles: list[str]
    disabled: bool


class MessageResponse(BaseModel):
    """Respuesta genérica con mensaje."""

    message: str
