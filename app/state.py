"""
Estado compartido de la aplicación.

Es el "punto de encuentro" entre la API y el juego.
Thread-safe mediante locks.
No conoce ni partículas ni colores. Solo almacena lo que el juego publica.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from domain.entities.color import RGBColor
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.state_port import StatePort


@dataclass
class GameStats:
    """Estadísticas del juego (solo lectura desde API)."""
    frames_processed: int = 0
    last_update: datetime | None = None
    fps: float = 0.0

    def to_dict(self) -> dict:
        return {
            "frames_processed": self.frames_processed,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "fps": round(self.fps, 2),
        }


@dataclass
class Command:
    """Comando enviado desde la API al juego."""
    action: str                       # "reset_particles", "change_palette", etc.
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class AppState(StatePort):
    """
    Estado compartido entre el juego y la API.

    Almacena:
    - Pose actual (común)
    - Datos específicos del juego (dict libre por key)
    - Comandos pendientes
    """

    def __init__(self):
        self._lock = Lock()

        # === Datos escritos por el juego, leídos por la API ===
        self._last_pose: list[PoseLandmark] = []
        self._stats: GameStats = GameStats()

        # Estado específico del juego (genérico, sin saber qué es)
        # Ejemplos: {"particles": [...], "background_color": RGBColor(...)}
        self._game_data: dict[str, Any] = {}

        # === Comandos escritos por la API, leídos por el juego ===
        self._pending_commands: list[Command] = []

    # ==========================================
    # Lecturas desde la API
    # ==========================================

    def get_snapshot(self) -> dict[str, Any]:
        """
        Devuelve un snapshot del estado actual (para la API).

        Returns:
            Diccionario serializable con el estado.
        """
        with self._lock:
            return {
                "pose": self._serialize_pose(),
                "game_data": self._serialize_game_data(),
                "stats": self._stats.to_dict(),
            }

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            return self._stats.to_dict()

    def update_pose(self, landmarks: list[PoseLandmark]) -> None:
        """El juego actualiza la última pose detectada."""
        with self._lock:
            self._last_pose = landmarks

    def update_game_data(self, key: str, value: Any) -> None:
        """El juego publica cualquier dato específico."""
        with self._lock:
            self._game_data[key] = value



    def increment_frames(self) -> None:
        """El juego incrementa el contador de frames."""
        with self._lock:
            self._stats.frames_processed += 1
            self._stats.last_update = datetime.now(timezone.utc)

    def update_fps(self, fps: float) -> None:
        """El juego actualiza el FPS actual."""
        with self._lock:
            self._stats.fps = fps

    # ==========================================
    # Comandos desde la API
    # ==========================================

    def enqueue_command(self, action: str, payload: dict[str, Any]) -> None:
        """La API encola un comando para el juego."""
        with self._lock:
            self._pending_commands.append(
                Command(action=action, payload=payload)
            )

    def drain_commands(self) -> list[Command]:
        """
        El juego consume todos los comandos pendientes.

        Returns:
            Lista de comandos y limpia la cola.
        """
        with self._lock:
            commands = self._pending_commands.copy()
            self._pending_commands.clear()
            return commands

    # ==========================================
    # Helpers privados
    # ==========================================

    def _serialize_pose(self) -> dict[str, Any]:
        """Serializa la pose para JSON."""
        return {
            "landmarks_count": len(self._last_pose),
            "visible_landmarks": sum(
                1 for lm in self._last_pose if lm.is_visible()
            ),
            "landmarks": [
                {
                    "name": lm.name,
                    "x": round(lm.x, 4),
                    "y": round(lm.y, 4),
                    "z": round(lm.z, 4),
                    "visibility": round(lm.visibility, 4),
                }
                for lm in self._last_pose[:33]
            ],
        }

    def _serialize_game_data(self) -> dict[str, Any]:
        """
        Serializa los datos específicos del juego.

        Aquí está el truco: la API ve un dict genérico. Cada juego
        publica las keys que quiere, y la API las expone tal cual.
        """
        with self._lock:
            serialized = {}
            for key, value in self._game_data.items():
                serialized[key] = self._serialize_value(value)
            return serialized

    def _serialize_value(self, value: Any) -> Any:
        """Serializa un valor arbitrario del estado."""
        # Lista de partículas
        if isinstance(value, list):
            return [self._serialize_value(v) for v in value[:100]]  # Limita

        # Objetos con to_dict
        if hasattr(value, "to_dict"):
            return value.to_dict()

        # RGBColor u otros con atributos r, g, b
        if hasattr(value, "r") and hasattr(value, "g") and hasattr(value, "b"):
            return {"r": value.r, "g": value.g, "b": value.b}

        # Partículas con x, y, life, etc.
        if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "life"):
            return {
                "x": round(value.x, 2),
                "y": round(value.y, 2),
                "life": round(value.life, 3),
                "size": round(value.size, 2),
                "color": list(value.color) if hasattr(value, "color") else None,
            }

        # Tipos básicos: devolver tal cual
        if isinstance(value, (int, float, str, bool, type(None))):
            return value

        # Fallback
        return str(value)