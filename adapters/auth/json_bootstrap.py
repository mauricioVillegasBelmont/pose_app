"""
Bootstrap: carga usuarios desde un archivo JSON.

Uso:
    user_repo, identity_repo = bootstrap_from_json("data/users.json")
"""

import json
from pathlib import Path

from adapters.auth.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from adapters.auth.in_memory_user_repository import InMemoryUserRepository
from adapters.auth.password_hasher import hash_password
from domain.entities.identity import Identity
from domain.entities.user import User
from domain.ports.identity_repository_port import IdentityRepositoryPort
from domain.ports.user_repository_port import UserRepositoryPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.auth.json_bootstrap")


def bootstrap_from_json(
    json_path: str | Path,
) -> tuple[UserRepositoryPort, IdentityRepositoryPort]:
    """
    Carga usuarios desde JSON y puebla los repositorios.

    Returns:
        (user_repository, identity_repository)
    """
    path = Path(json_path)

    if not path.exists():
        logger.warning(f"Archivo de usuarios no encontrado: {path}")
        return InMemoryUserRepository(), InMemoryIdentityRepository()

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    users_raw = data.get("users", [])

    user_repo = InMemoryUserRepository()
    identity_repo = InMemoryIdentityRepository()

    for raw in users_raw:
        # Extrae password antes de construir User
        password = raw.pop("password", None)

        user = User(
            id=raw["id"],
            username=raw["username"],
            email=raw.get("email"),
            full_name=raw.get("full_name"),
            roles=tuple(raw.get("roles", ["user"])),
            disabled=raw.get("disabled", False),
        )
        user_repo.create(user)

        if password is not None:
            identity = Identity(
                user_id=user.id,
                provider="password",
                provider_user_id=user.username,
                password_hash=hash_password(password),
            )
            identity_repo.create(identity)

    logger.info(f"Usuarios cargados desde JSON: {len(users_raw)}")
    return user_repo, identity_repo
