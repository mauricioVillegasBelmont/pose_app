"""
Registro de estados de juegos activos.

La API consulta este registro para saber qué juegos están activos
y obtener sus snapshots.

Thread-safe.
"""

from threading import Lock
from typing import Any

from domain.state.game_state_port import GameStatePort
from infrastructure.logging.logger import get_logger

logger = get_logger("app.state_registry")


class StateRegistry:
    """Registro thread-safe de estados por juego."""

    def __init__(self):
        self._lock = Lock()
        self._states: dict[str, GameStatePort] = {}

    def register(self, state: GameStatePort) -> None:
        with self._lock:
            self._states[state.game_id] = state
            logger.info(f"Estado registrado: {state.game_id}")

    def unregister(self, game_id: str) -> None:
        with self._lock:
            removed = self._states.pop(game_id, None)
            if removed is not None:
                logger.info(f"Estado desregistrado: {game_id}")

    def get(self, game_id: str) -> GameStatePort | None:
        with self._lock:
            return self._states.get(game_id)

    def all(self) -> dict[str, GameStatePort]:
        with self._lock:
            return dict(self._states)

    def snapshot_all(self) -> dict[str, Any]:
        """
        Snapshot agregado de todos los juegos activos.
        """
        with self._lock:
            states = dict(self._states)

        return {
            "games": {
                game_id: state.snapshot()
                for game_id, state in states.items()
            },
            "active_games": list(states.keys()),
        }

    def stats_all(self) -> dict[str, Any]:
        """Estadísticas agregadas de todos los juegos."""
        with self._lock:
            states = dict(self._states)

        return {
            game_id: state.stats()
            for game_id, state in states.items()
        }

    def clear(self) -> None:
        """Limpia el registro (útil en tests)."""
        with self._lock:
            self._states.clear()