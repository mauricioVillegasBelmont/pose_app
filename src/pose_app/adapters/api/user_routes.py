"""
Rutas de usuarios.

Contiene:
- Endpoints self-service (/me) para cualquier usuario autenticado.
- Endpoints CRUD (/users) solo para admin.

IMPORTANTE: /me va ANTES de /{user_id} para evitar conflicto de rutas.
"""

from fastapi import APIRouter, HTTPException, status

from pose_app.adapters.api.dependencies import (
    AdminUser,
    CurrentUser,
    IdentityRepositoryDep,
    UserRepositoryDep,
)
from pose_app.adapters.api.user_schemas import (
    MessageResponse,
    PasswordChangeRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from pose_app.adapters.auth.password_hasher import hash_password, verify_password
from pose_app.domain.entities.identity import Identity
from pose_app.domain.entities.user import User
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.api.user_routes")


# ==========================================
# Helpers
# ==========================================


def _user_to_response(user: User) -> UserResponse:
    """Convierte User (dominio) a UserResponse (DTO)."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=list(user.roles),
        disabled=user.disabled,
    )


# ==========================================
# Router
# ==========================================


def create_user_router() -> APIRouter:
    """Crea el router con los endpoints de usuarios."""
    router = APIRouter(prefix="/api/v1/users", tags=["Users"])

    # ==========================================
    # SELF-SERVICE (cualquier usuario autenticado)
    # ==========================================
    # ⚠️ /me va ANTES de /{user_id}, si no se interpreta "me"
    # como un user_id.

    @router.get("/me", response_model=UserResponse)
    async def get_me(current_user: CurrentUser) -> UserResponse:
        """Devuelve el perfil del usuario autenticado."""
        return _user_to_response(current_user)

    @router.patch("/me", response_model=UserResponse)
    async def update_me(
        request: UserUpdateRequest,
        current_user: CurrentUser,
        user_repo: UserRepositoryDep,
    ) -> UserResponse:
        """
        Actualiza el propio perfil.

        Un usuario solo puede cambiar su email y full_name.
        NO puede cambiar sus roles ni su estado disabled.
        """
        updated = current_user

        if request.email is not None:
            updated = updated.with_email(request.email)
        if request.full_name is not None:
            updated = updated.with_full_name(request.full_name)

        # Nota: ignoramos silenciosamente `roles` y `disabled`
        # aunque vengan en el request. El usuario no puede
        # modificar sus propios permisos.

        user_repo.update(updated)
        logger.info(f"Perfil actualizado: {current_user.username}")
        return _user_to_response(updated)

    @router.post("/me/password", response_model=MessageResponse)
    async def change_my_password(
        request: PasswordChangeRequest,
        current_user: CurrentUser,
        identity_repo: IdentityRepositoryDep,
    ) -> MessageResponse:
        """Cambia la contraseña del usuario autenticado."""
        # Busca la identidad de tipo password del usuario
        identity = identity_repo.get_by_provider("password", current_user.username)

        if identity is None or identity.password_hash is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("El usuario no tiene método de autenticación por contraseña"),
            )

        # Verifica la contraseña actual
        if not verify_password(request.current_password, identity.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta",
            )

        # Actualiza el hash
        new_identity = Identity(
            user_id=identity.user_id,
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
            password_hash=hash_password(request.new_password),
            created_at=identity.created_at,
            last_login_at=identity.last_login_at,
        )
        identity_repo.update(new_identity)

        logger.info(f"Contraseña cambiada: {current_user.username}")
        return MessageResponse(message="Contraseña actualizada correctamente")

    # ==========================================
    # CRUD ADMIN
    # ==========================================

    @router.post(
        "",
        status_code=status.HTTP_201_CREATED,
        response_model=UserResponse,
    )
    async def create_user(
        request: UserCreateRequest,
        _admin: AdminUser,
        user_repo: UserRepositoryDep,
        identity_repo: IdentityRepositoryDep,
    ) -> UserResponse:
        """Crea un usuario (solo admin)."""
        # Verifica que el username no exista
        if user_repo.get_by_username(request.username) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El username '{request.username}' ya existe",
            )

        # Crea el User
        user = User(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            roles=tuple(request.roles),
            disabled=request.disabled,
        )
        user_repo.create(user)

        # Crea la Identity de password
        identity = Identity(
            user_id=user.id,
            provider="password",
            provider_user_id=user.username,
            password_hash=hash_password(request.password),
        )
        identity_repo.create(identity)

        logger.info(f"Usuario creado: {user.username} por admin {_admin.username}")
        return _user_to_response(user)

    @router.get("", response_model=list[UserResponse])
    async def list_users(
        _admin: AdminUser,
        user_repo: UserRepositoryDep,
    ) -> list[UserResponse]:
        """Lista todos los usuarios (solo admin)."""
        users = user_repo.list_all()
        return [_user_to_response(u) for u in users]

    @router.get("/{user_id}", response_model=UserResponse)
    async def get_user(
        user_id: str,
        _admin: AdminUser,
        user_repo: UserRepositoryDep,
    ) -> UserResponse:
        """Obtiene un usuario por id (solo admin)."""
        user = user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario no encontrado: {user_id}",
            )
        return _user_to_response(user)

    @router.patch("/{user_id}", response_model=UserResponse)
    async def update_user(
        user_id: str,
        request: UserUpdateRequest,
        admin: AdminUser,
        user_repo: UserRepositoryDep,
    ) -> UserResponse:
        """Actualiza un usuario (solo admin)."""
        user = user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario no encontrado: {user_id}",
            )

        # === Validaciones de seguridad ===
        # Un admin no puede deshabilitarse a sí mismo
        if user.id == admin.id and request.disabled is True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes deshabilitar tu propio usuario",
            )

        # Un admin no puede quitarse el rol admin a sí mismo
        if (
            user.id == admin.id
            and request.roles is not None
            and "admin" not in request.roles
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes quitarte el rol admin a ti mismo",
            )

        # Aplica cambios (solo los campos presentes)
        updated = user
        if request.email is not None:
            updated = updated.with_email(request.email)
        if request.full_name is not None:
            updated = updated.with_full_name(request.full_name)
        if request.roles is not None:
            updated = updated.with_roles(tuple(request.roles))
        if request.disabled is not None:
            updated = updated.with_disabled(request.disabled)

        user_repo.update(updated)
        logger.info(f"Usuario actualizado: {user.username} por admin {admin.username}")
        return _user_to_response(updated)

    @router.delete(
        "/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_user(
        user_id: str,
        admin: AdminUser,
        user_repo: UserRepositoryDep,
        identity_repo: IdentityRepositoryDep,
    ) -> None:
        """Elimina un usuario (solo admin)."""
        user = user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario no encontrado: {user_id}",
            )

        # Un admin no puede eliminarse a sí mismo
        if user.id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminarte a ti mismo",
            )

        # Elimina primero las identidades
        for identity in identity_repo.get_by_user_id(user_id):
            identity_repo.delete(user_id, identity.provider)

        # Luego el usuario
        user_repo.delete(user_id)

        logger.info(f"Usuario eliminado: {user.username} por admin {admin.username}")

    return router
