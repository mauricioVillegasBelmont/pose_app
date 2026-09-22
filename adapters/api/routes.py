"""
Definición de rutas de la API.

Cada endpoint es un "adaptador de entrada" que traduce HTTP → dominio.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from adapters.api.schemas import (
    ChangePaletteRequest,
    CommandResponse,
    HealthSchema,
    StateSnapshotSchema,
    StatsSchema,
)
from domain.ports.state_port import StatePort

# Tiempo de inicio para calcular uptime
_start_time = datetime.now(timezone.utc)
APP_VERSION = "0.4.0"


def create_router(state: StatePort) -> APIRouter:
    """
    Crea el router con los endpoints.

    Args:
        state: Puerto de estado (inyectado).

    Returns:
        Router configurado.
    """
    router = APIRouter(prefix="/api/v1", tags=["Pose AR"])

    # ==========================================
    # Health check
    # ==========================================

    @router.get(
        "/health",
        response_model=HealthSchema,
        summary="Estado de la aplicación"
    )
    def health() -> HealthSchema:
        """Verifica que la API esté viva."""
        uptime = (datetime.now(timezone.utc) - _start_time).total_seconds()
        return HealthSchema(
            status="ok",
            version=APP_VERSION,
            uptime_seconds=uptime,
            timestamp=datetime.now(timezone.utc),
        )

    # ==========================================
    # Queries (lectura)
    # ==========================================

    @router.get(
        "/state",
        response_model=StateSnapshotSchema,
        summary="Snapshot completo del estado"
    )
    def get_state() -> StateSnapshotSchema:
        """
        Devuelve el estado actual de la aplicación:
        - Landmarks detectados
        - Partículas activas
        - Estadísticas
        """
        snapshot = state.get_snapshot()
        return StateSnapshotSchema(**snapshot)

    @router.get(
        "/stats",
        response_model=StatsSchema,
        summary="Estadísticas del juego"
    )
    def get_stats() -> StatsSchema:
        """Devuelve solo las estadísticas (más ligero)."""
        stats = state.get_stats()
        return StatsSchema(**stats)

    @router.get(
        "/pose",
        summary="Última pose detectada"
    )
    def get_pose() -> dict:
        """Devuelve solo los landmarks de la última pose."""
        snapshot = state.get_snapshot()
        return snapshot["pose"]

    # ==========================================
    # Commands (escritura)
    # ==========================================

    @router.post(
        "/commands/reset-particles",
        response_model=CommandResponse,
        summary="Reinicia el sistema de partículas"
    )
    def reset_particles() -> CommandResponse:
        """Encola un comando para reiniciar las partículas."""
        command_id = str(uuid.uuid4())
        state.enqueue_command(
            action="reset_particles",
            payload={}
        )
        return CommandResponse(
            accepted=True,
            message="Comando reset_particles encolado",
            command_id=command_id,
        )

    @router.post(
        "/commands/change-palette",
        response_model=CommandResponse,
        summary="Cambia la paleta de colores"
    )
    def change_palette(
        request: ChangePaletteRequest
    ) -> CommandResponse:
        """Cambia la paleta actual (aplica al siguiente frame)."""
        command_id = str(uuid.uuid4())
        state.enqueue_command(
            action="change_palette",
            payload={"palette": request.palette}
        )
        return CommandResponse(
            accepted=True,
            message=f"Comando change_palette encolado: '{request.palette}'",
            command_id=command_id,
        )

    return router