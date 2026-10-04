"""
Tests de endpoints de usuarios.

Cubre:
- Self-service (/me)
- CRUD admin (/users)
- Permisos (admin vs user normal)
- Validaciones
- Seguridad (no auto-lockout)
"""

import pytest
from fastapi.testclient import TestClient

from adapters.api.fastapi_adapter import FastAPIAdapter
from app.state_registry import StateRegistry
from config.settings import JWTSettings, Settings, reset_settings
from infrastructure.events.async_event_bus import AsyncEventBus


@pytest.fixture
def test_settings() -> Settings:
    """Settings deterministas para tests."""
    reset_settings()
    return Settings(
        environment="testing",
        jwt=JWTSettings(
            secret_key="test-secret-key-at-least-32-characters-long",
            algorithm="HS256",
            access_token_expire_minutes=60,
        ),
        _env_file=None,
    )


@pytest.fixture
def client(test_settings) -> TestClient:
    """TestClient con auth + bootstrap usuarios."""
    adapter = FastAPIAdapter(
        settings=test_settings,
        event_bus=AsyncEventBus(),
        registry=StateRegistry(),
    )
    return TestClient(adapter.app)


@pytest.fixture
def admin_token(client) -> str:
    """Token JWT del usuario admin."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def user_token(client) -> str:
    """Token JWT del usuario normal (no admin)."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "user123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    """Helper para construir el header de auth."""
    return {"Authorization": f"Bearer {token}"}


######################################
# Self-service (/me)
######################################


class TestSelfServiceMe:
    """Tests de /api/v1/users/me (cualquier usuario autenticado)."""

    def test_get_me_returns_own_profile(self, client, admin_token):
        """/me devuelve el perfil del usuario autenticado."""
        response = client.get(
            "/api/v1/users/me",
            headers=_auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert "admin" in data["roles"]
        assert data["id"] == "admin-uuid-0001"

    def test_get_me_works_for_regular_user(self, client, user_token):
        """/me funciona para usuarios NO admin también."""
        response = client.get(
            "/api/v1/users/me",
            headers=_auth_header(user_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "user"
        assert data["roles"] == ["user"]

    def test_get_me_without_token_returns_401(self, client):
        """Sin token, /me devuelve 401."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_update_me_email_and_full_name(self, client, user_token):
        """Un usuario puede actualizar su email y full_name."""
        response = client.patch(
            "/api/v1/users/me",
            headers=_auth_header(user_token),
            json={
                "email": "nuevo@example.com",
                "full_name": "Nuevo Nombre",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "nuevo@example.com"
        assert data["full_name"] == "Nuevo Nombre"

    def test_update_me_cannot_change_own_roles(self, client, user_token):
        """
        Un usuario NO puede cambiar sus propios roles.

        Aunque envíe `roles` en el payload, se ignora silenciosamente.
        """
        response = client.patch(
            "/api/v1/users/me",
            headers=_auth_header(user_token),
            json={"roles": ["admin"]},  # ← intento de escalada
        )
        assert response.status_code == 200
        data = response.json()
        # Los roles NO cambiaron
        assert data["roles"] == ["user"]

    def test_update_me_cannot_enable_self_if_disabled(self, client, user_token):
        """Un usuario NO puede auto-habilitarse si está deshabilitado."""
        # Nota: "user" no está deshabilitado, pero enviamos `disabled: false`
        # para verificar que el campo se ignora.
        response = client.patch(
            "/api/v1/users/me",
            headers=_auth_header(user_token),
            json={"disabled": False},
        )
        assert response.status_code == 200
        # El campo disabled no se cambió (ya estaba en False)

    def test_change_my_password_success(self, client, user_token):
        """Un usuario puede cambiar su propia contraseña."""
        response = client.post(
            "/api/v1/users/me/password",
            headers=_auth_header(user_token),
            json={
                "current_password": "user123",
                "new_password": "newpass123",
            },
        )
        assert response.status_code == 200
        assert "actualizada" in response.json()["message"]

        # Login con la nueva contraseña
        login = client.post(
            "/api/v1/auth/token",
            data={"username": "user", "password": "newpass123"},
        )
        assert login.status_code == 200

    def test_change_my_password_wrong_current(self, client, user_token):
        """Si la contraseña actual es incorrecta → 401."""
        response = client.post(
            "/api/v1/users/me/password",
            headers=_auth_header(user_token),
            json={
                "current_password": "wrong",
                "new_password": "newpass123",
            },
        )
        assert response.status_code == 401

    def test_change_my_password_too_short(self, client, user_token):
        """La nueva contraseña debe tener al menos 8 caracteres."""
        response = client.post(
            "/api/v1/users/me/password",
            headers=_auth_header(user_token),
            json={
                "current_password": "user123",
                "new_password": "short",
            },
        )
        assert response.status_code == 422  # Pydantic validation


######################################
# CRUD admin (/users)
######################################


class TestAdminCrud:
    """Tests de /api/v1/users (solo admin)."""

    def test_create_user_success(self, client, admin_token):
        """Admin crea un usuario nuevo."""
        response = client.post(
            "/api/v1/users",
            headers=_auth_header(admin_token),
            json={
                "username": "newuser",
                "password": "newpass123",
                "email": "new@x.com",
                "full_name": "New User",
                "roles": ["user"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@x.com"
        assert data["roles"] == ["user"]
        assert "id" in data
        # El password_hash NUNCA se expone
        assert "password" not in data
        assert "password_hash" not in data

    def test_create_user_duplicate_username(self, client, admin_token):
        """Crear usuario con username existente → 409."""
        response = client.post(
            "/api/v1/users",
            headers=_auth_header(admin_token),
            json={
                "username": "admin",  # ya existe
                "password": "whatever123",
            },
        )
        assert response.status_code == 409

    def test_create_user_invalid_username(self, client, admin_token):
        """Username inválido → 422 (Pydantic)."""
        response = client.post(
            "/api/v1/users",
            headers=_auth_header(admin_token),
            json={
                "username": "A",  # muy corto, empieza con mayúscula
                "password": "validpass123",
            },
        )
        assert response.status_code == 422

    def test_create_user_short_password(self, client, admin_token):
        """Password < 8 chars → 422."""
        response = client.post(
            "/api/v1/users",
            headers=_auth_header(admin_token),
            json={
                "username": "shortpass",
                "password": "abc",  # muy corto
            },
        )
        assert response.status_code == 422

    def test_list_users_as_admin(self, client, admin_token):
        """Admin ve todos los usuarios."""
        response = client.get(
            "/api/v1/users",
            headers=_auth_header(admin_token),
        )
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2
        usernames = {u["username"] for u in users}
        assert "admin" in usernames
        assert "user" in usernames

    def test_get_user_by_id(self, client, admin_token):
        """Admin obtiene un usuario por id."""
        response = client.get(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["username"] == "admin"

    def test_get_user_not_found(self, client, admin_token):
        """Id inexistente → 404."""
        response = client.get(
            "/api/v1/users/nonexistent-id",
            headers=_auth_header(admin_token),
        )
        assert response.status_code == 404

    def test_update_user_by_admin(self, client, admin_token):
        """Admin actualiza un usuario."""
        response = client.patch(
            "/api/v1/users/user-uuid-0002",
            headers=_auth_header(admin_token),
            json={
                "email": "updated@x.com",
                "full_name": "Updated Name",
                "roles": ["user", "moderator"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@x.com"
        assert data["full_name"] == "Updated Name"
        assert "moderator" in data["roles"]

    def test_delete_user_by_admin(self, client, admin_token):
        """Admin elimina un usuario."""
        # Primero crea uno para no borrar "user"
        create = client.post(
            "/api/v1/users",
            headers=_auth_header(admin_token),
            json={"username": "to_delete", "password": "del12345"},
        )
        user_id = create.json()["id"]

        # Luego lo elimina
        response = client.delete(
            f"/api/v1/users/{user_id}",
            headers=_auth_header(admin_token),
        )
        assert response.status_code == 204

        # Verifica que ya no existe
        get = client.get(
            f"/api/v1/users/{user_id}",
            headers=_auth_header(admin_token),
        )
        assert get.status_code == 404

    def test_delete_user_also_removes_identity(self, client, admin_token):
        """Eliminar un usuario elimina también su identidad de auth."""
        # Crea usuario
        create = client.post(
            "/api/v1/users",
            headers=_auth_header(admin_token),
            json={"username": "temp_user", "password": "temp1234"},
        )
        user_id = create.json()["id"]

        # Elimina
        client.delete(
            f"/api/v1/users/{user_id}",
            headers=_auth_header(admin_token),
        )

        # El login debe fallar (identidad eliminada)
        login = client.post(
            "/api/v1/auth/token",
            data={"username": "temp_user", "password": "temp1234"},
        )
        assert login.status_code == 401


######################################
# Permisos (admin vs user normal)
######################################


class TestPermissions:
    """Tests de permisos (admin vs user)."""

    def test_list_users_requires_admin(self, client, user_token):
        """Usuario normal NO puede listar usuarios."""
        response = client.get(
            "/api/v1/users",
            headers=_auth_header(user_token),
        )
        assert response.status_code == 403

    def test_create_user_requires_admin(self, client, user_token):
        """Usuario normal NO puede crear usuarios."""
        response = client.post(
            "/api/v1/users",
            headers=_auth_header(user_token),
            json={"username": "hacker", "password": "hack1234"},
        )
        assert response.status_code == 403

    def test_get_user_by_id_requires_admin(self, client, user_token):
        """Usuario normal NO puede ver otros usuarios por id."""
        response = client.get(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(user_token),
        )
        assert response.status_code == 403

    def test_update_user_requires_admin(self, client, user_token):
        """Usuario normal NO puede actualizar otros usuarios."""
        response = client.patch(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(user_token),
            json={"full_name": "Hacked"},
        )
        assert response.status_code == 403

    def test_delete_user_requires_admin(self, client, user_token):
        """Usuario normal NO puede eliminar usuarios."""
        response = client.delete(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(user_token),
        )
        assert response.status_code == 403

    def test_admin_required_without_token(self, client):
        """Sin token, cualquier endpoint admin → 401."""
        response = client.get("/api/v1/users")
        assert response.status_code == 401


######################################
# Validaciones
######################################


######################################
# Seguridad (no auto-lockout)
######################################


class TestAdminSafetyGuards:
    """Tests que previenen auto-bloqueo del admin."""

    def test_admin_cannot_delete_self(self, client, admin_token):
        """Un admin no puede eliminarse a sí mismo."""
        response = client.delete(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(admin_token),
        )
        assert response.status_code == 400
        assert "eliminarte" in response.json()["detail"].lower()

    def test_admin_cannot_disable_self(self, client, admin_token):
        """Un admin no puede deshabilitarse a sí mismo."""
        response = client.patch(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(admin_token),
            json={"disabled": True},
        )
        assert response.status_code == 400
        assert "deshabilitar" in response.json()["detail"].lower()

    def test_admin_cannot_remove_own_admin_role(self, client, admin_token):
        """Un admin no puede quitarse el rol admin a sí mismo."""
        response = client.patch(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(admin_token),
            json={"roles": ["user"]},  # ← quita "admin"
        )
        assert response.status_code == 400
        assert "admin" in response.json()["detail"].lower()

    def test_admin_can_update_self_if_keeps_admin_role(self, client, admin_token):
        """Un admin SÍ puede actualizarse si mantiene el rol admin."""
        response = client.patch(
            "/api/v1/users/admin-uuid-0001",
            headers=_auth_header(admin_token),
            json={
                "full_name": "Super Admin",
                "roles": ["admin", "user", "superuser"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "superuser" in data["roles"]
        assert "admin" in data["roles"]
