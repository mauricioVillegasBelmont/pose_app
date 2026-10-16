# domain/events/game_events.py

from dataclasses import dataclass, field
from typing import Any

from pose_app.domain.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class GameCommand(DomainEvent):
    """Comando genérico enviado por la API."""

    action: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class GameResetRequested(DomainEvent):
    """Solicitud de reset del juego de partículas."""


@dataclass(frozen=True, kw_only=True)
class PaletteChangeRequested(DomainEvent):
    """Solicitud de cambio de paleta."""

    palette_name: str
