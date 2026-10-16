"""Rutas de autenticación."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from pose_app.adapters.api.dependencies import AuthDep, CurrentUser, JWTServiceDep


def create_auth_router() -> APIRouter:
    """Crea el router de autenticación."""
    router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

    @router.post("/token")
    async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth: AuthDep,
        jwt_service: JWTServiceDep,
    ) -> dict:
        """Login con username/password → devuelve token JWT."""
        user = auth.authenticate(form_data.username, form_data.password)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = jwt_service.create_access_token(user)
        return {
            "access_token": token,
            "token_type": "bearer",
        }

    @router.get("/me")
    async def read_current_user(current_user: CurrentUser) -> dict:
        """Devuelve info del usuario autenticado."""
        return {
            "username": current_user.username,
            "full_name": current_user.full_name,
            "roles": list(current_user.roles),
        }

    return router
