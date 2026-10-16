"""Dependencias de FastAPI."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from pose_app.config.settings import Settings
from pose_app.domain.entities.user import User
from pose_app.domain.ports.auth_port import AuthPort
from pose_app.domain.ports.identity_repository_port import IdentityRepositoryPort
from pose_app.domain.ports.user_repository_port import UserRepositoryPort
from pose_app.infrastructure.auth.jwt_service import JWTService, TokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ---------- Dependencias base ----------


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_auth_adapter_dep(request: Request) -> AuthPort:
    return request.app.state.auth_adapter


def get_jwt_service_dep(request: Request) -> JWTService:
    return request.app.state.jwt_service


def get_user_repository_dep(request: Request) -> UserRepositoryPort:
    return request.app.state.user_repository


def get_identity_repository_dep(request: Request) -> IdentityRepositoryPort:
    return request.app.state.identity_repository


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    jwt_service: JWTService = request.app.state.jwt_service
    auth_adapter: AuthPort = request.app.state.auth_adapter

    try:
        payload = jwt_service.decode_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except TokenError:
        raise credentials_exception

    user = auth_adapter.get_user(username)
    if user is None:
        raise credentials_exception

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario deshabilitado",
        )

    return user


# ---------- Alias Annotated (ANTES de usarlos) ----------

CurrentUser = Annotated[User, Depends(get_current_user)]
AuthDep = Annotated[AuthPort, Depends(get_auth_adapter_dep)]
JWTServiceDep = Annotated[JWTService, Depends(get_jwt_service_dep)]
UserRepositoryDep = Annotated[UserRepositoryPort, Depends(get_user_repository_dep)]
IdentityRepositoryDep = Annotated[
    IdentityRepositoryPort, Depends(get_identity_repository_dep)
]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


# ==========================================
# Dependencia: AdminUser (exige rol admin)
# ==========================================


def require_admin(user: CurrentUser) -> User:
    """
    Dependencia que exige rol admin.

    Raises:
        HTTPException 403 si el usuario no es admin.
    """
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere rol admin",
        )
    return user


# Tipo anotado para inyectar en rutas
AdminUser = Annotated[User, Depends(require_admin)]
