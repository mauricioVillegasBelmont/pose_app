"""
Rutas de la API.

Cada endpoint es un adaptador de entrada: traduce HTTP → dominio
(publica eventos o consulta el registry).
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from adapters.api.dependencies import CurrentUser
from adapters.api.schemas import (
    ChangePaletteRequest,
    CommandResponse,
    HealthSchema,
)
from app.state_registry import StateRegistry
from domain.events.game_events import (
    GameResetRequested,
    PaletteChangeRequested,
)
from domain.ports.event_bus_port import EventBusPort

APP_VERSION = "0.5.0"
_start_time = datetime.now(UTC)


def create_router(
    event_bus: EventBusPort,
    registry: StateRegistry,
) -> APIRouter:
    """Crea el router con los endpoints."""
    router = APIRouter(prefix="/api/v1", tags=["Pose AR"])

    # ==========================================
    # Health
    # ==========================================

    @router.get("/health", response_model=HealthSchema)
    async def health() -> HealthSchema:
        uptime = (datetime.now(UTC) - _start_time).total_seconds()
        return HealthSchema(
            status="ok",
            version=APP_VERSION,
            uptime_seconds=uptime,
            timestamp=datetime.now(UTC),
        )

    # ==========================================
    # Queries
    # ==========================================

    @router.get("/state")
    async def get_state(
        current_user: CurrentUser,
    ) -> dict:
        """Snapshot agregado de todos los juegos activos."""
        return registry.snapshot_all()

    @router.get("/state/{game_id}")
    async def get_game_state(game_id: str) -> dict:
        state = registry.get(game_id)
        if state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Juego '{game_id}' no activo",
            )
        return state.snapshot()

    @router.get("/stats")
    async def get_stats() -> dict:
        return registry.stats_all()

    # ==========================================
    # Commands (publican eventos)
    # ==========================================

    @router.post("/commands/reset-particles", response_model=CommandResponse)
    async def reset_particles() -> CommandResponse:
        command_id = str(uuid.uuid4())
        await event_bus.publish(GameResetRequested())
        return CommandResponse(
            accepted=True,
            message="Evento GameResetRequested publicado",
            command_id=command_id,
        )

    @router.post("/commands/change-palette", response_model=CommandResponse)
    async def change_palette(request: ChangePaletteRequest) -> CommandResponse:
        command_id = str(uuid.uuid4())
        await event_bus.publish(PaletteChangeRequested(palette_name=request.palette))
        return CommandResponse(
            accepted=True,
            message=f"Evento PaletteChangeRequested publicado: '{request.palette}'",
            command_id=command_id,
        )

    return router
