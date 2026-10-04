"""
Schemas de la API (DTOs).

Traducen entre JSON (HTTP) y estructuras del dominio.
Son independientes del dominio: si cambia el dominio, ajustas el schema.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ==========================================
# Response Models
# ==========================================


class LandmarkSchema(BaseModel):
    """Landmark en respuesta JSON."""

    name: str | None = None
    x: float
    y: float
    z: float
    visibility: float


class ParticleSchema(BaseModel):
    """Partícula en respuesta JSON."""

    x: float
    y: float
    life: float
    size: float
    color: tuple[int, int, int]


class StatsSchema(BaseModel):
    """Estadísticas del juego."""

    frames_processed: int
    particles_active: int
    last_update: str | None = None
    fps: float


class PoseSchema(BaseModel):
    """Pose actual."""

    landmarks_count: int
    visible_landmarks: int
    landmarks: list[LandmarkSchema]


class ParticlesSchema(BaseModel):
    """Estado de partículas."""

    count: int
    sample: list[ParticleSchema]


class StateSnapshotSchema(BaseModel):
    """Snapshot completo del estado."""

    pose: PoseSchema
    particles: ParticlesSchema
    background_color: str
    current_palette: str
    stats: StatsSchema


class HealthSchema(BaseModel):
    """Respuesta de health check."""

    status: Literal["ok", "degraded", "error"]
    version: str
    uptime_seconds: float
    timestamp: datetime


# ==========================================
# Request Models
# ==========================================


class ChangePaletteRequest(BaseModel):
    """Request para cambiar paleta."""

    palette: Literal["fire", "ocean", "forest", "neon"] = Field(
        ..., description="Nombre de la paleta"
    )


class CommandResponse(BaseModel):
    """Respuesta al enviar un comando."""

    accepted: bool
    message: str
    command_id: str
