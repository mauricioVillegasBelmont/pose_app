"""
Estado del juego de gestures.

Thread-safe. Expone:
- Qué gestos están activos AHORA.
- Cuántas veces se ha activado cada gesto (contador acumulado).
- Cuántos frames se procesaron.
"""

from threading import Lock
from typing import Any

from domain.entities.gesture import Gesture
from domain.state.game_state_port import GameStatePort
from infrastructure.logging.logger import get_logger

logger = get_logger("games.gestures.state")


class GesturesState(GameStatePort):
    """Estado consultable del juego de gestures."""

    def __init__(self):
        self._lock = Lock()

        # Gestos activos en el frame actual
        self._active_gestures: set[Gesture] = set()

        # Contador acumulado por gesto (cuántas veces se activó)
        self._activation_counts: dict[Gesture, int] = {
            g: 0 for g in Gesture
        }

        # Frames procesados
        self._frame_count: int = 0

    @property
    def game_id(self) -> str:
        return "gestures"

    # ==========================================
    # API de escritura (usada por GesturesGame)
    # ==========================================

    def update_active_gestures(
        self, newly_activated: set[Gesture], currently_active: set[Gesture]
    ) -> None:
        """
        Actualiza el estado con los gestos activos actuales y los que
        se acaban de activar (para incrementar contadores).
        """
        with self._lock:
            self._active_gestures = set(currently_active)
            for gesture in newly_activated:
                self._activation_counts[gesture] += 1

    def increment_frames(self) -> None:
        with self._lock:
            self._frame_count += 1

    # ==========================================
    # GameStatePort
    # ==========================================

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "active_gestures": sorted(
                    g.value for g in self._active_gestures
                ),
                "activation_counts": {
                    g.value: count
                    for g, count in self._activation_counts.items()
                },
                "frame_count": self._frame_count,
            }

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "active_count": len(self._active_gestures),
                "total_activations": sum(self._activation_counts.values()),
                "frames_processed": self._frame_count,
            }