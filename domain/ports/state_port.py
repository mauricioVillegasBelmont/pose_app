"""
Puerto de acceso al estado compartido.

La API (o cualquier otro consumidor) usa este puerto para leer/escribir
sin conocer la implementación concreta (AppState con lock, Redis, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any


class StatePort(ABC):
    """
    Puerto genérico de estado compartido.

    NO conoce comandos específicos de juegos. Solo sabe:
    - Publicar estado (updates desde el juego)
    - Leer estado (snapshots para la API)
    - Encolar/consumir comandos genéricos
    """

    # === Lecturas (API) ===

    @abstractmethod
    def get_snapshot(self) -> dict[str, Any]:
        """Snapshot completo del estado."""

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Estadísticas del juego."""

    # === Publicaciones (Juego) ===

    @abstractmethod
    def update_pose(self, landmarks: list) -> None:
        """El juego publica la última pose detectada."""

    @abstractmethod
    def update_game_data(self, key: str, value: Any) -> None:
        """
        El juego publica cualquier dato específico (partículas, color, etc.).
        Uso:
            state.update_game_data("particles", particles)
            state.update_game_data("background_color", color)
        """

    @abstractmethod
    def increment_frames(self) -> None:
        """Incrementa el contador de frames."""

    # === Comandos (API → Juego) ===

    @abstractmethod
    def enqueue_command(self, action: str, payload: dict[str, Any]) -> None:
        """
        Encola un comando genérico (dict con action + payload).
        El juego decide qué comandos entiende.
        """

    @abstractmethod
    def drain_commands(self) -> list:
        """El juego consume todos los comandos pendientes."""
