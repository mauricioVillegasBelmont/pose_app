"""
Estado consultable del juego de partículas (para la API).
"""

from dataclasses import dataclass
from threading import Lock
from typing import Any

from pose_app.domain.state.game_state_port import GameStatePort


@dataclass
class _InternalState:
    """Estado interno mutable del juego."""

    score: int = 0
    round_number: int = 1
    max_score: int = 10
    time_remaining: float = 30.0
    time_per_round: float = 10.0
    particles_count: int = 0
    is_game_over: bool = False
    is_winner: bool = False


class ParticlesState(GameStatePort):
    """
    Estado consultable del juego, thread-safe.

    Mantiene:
    - Estado interno (mutable, para la lógica).
    - Exposición pública (snapshot, stats).
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._internal = _InternalState()

    @property
    def game_id(self) -> str:
        return "particles"

    # ==========================================
    # API interna (usada por el juego)
    # ==========================================

    def increment_score(self) -> None:
        with self._lock:
            self._internal.score += 1

    def decrement_score(self) -> None:
        with self._lock:
            self._internal.score = max(0, self._internal.score - 1)

    def set_particles_count(self, count: int) -> None:
        with self._lock:
            self._internal.particles_count = count

    def set_round_number(self, round_number: int) -> None:
        """Actualiza el número de ronda actual."""
        with self._lock:
            self._internal.round_number = round_number

    def set_time_remaining(self, seconds: float) -> None:
        with self._lock:
            self._internal.time_remaining = max(0.0, seconds)

    def next_round(self) -> None:
        with self._lock:
            self._internal.round_number += 1
            self._internal.time_remaining = self._internal.time_per_round

    def set_game_over(self, winner: bool) -> None:
        with self._lock:
            self._internal.is_game_over = True
            self._internal.is_winner = winner

    def get_score(self) -> int:
        with self._lock:
            return self._internal.score

    def get_time_remaining(self) -> float:
        with self._lock:
            return self._internal.time_remaining

    def is_game_over(self) -> bool:
        with self._lock:
            return self._internal.is_game_over

    def is_winner(self) -> bool:
        with self._lock:
            return self._internal.is_winner

    def get_max_score(self) -> int:
        with self._lock:
            return self._internal.max_score

    # ==========================================
    # GameStatePort
    # ==========================================

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "score": self._internal.score,
                "max_score": self._internal.max_score,
                "round_number": self._internal.round_number,
                "time_remaining": round(self._internal.time_remaining, 2),
                "particles_count": self._internal.particles_count,
                "is_game_over": self._internal.is_game_over,
                "is_winner": self._internal.is_winner,
            }

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "score": self._internal.score,
                "rounds_played": self._internal.round_number - 1,
                "game_over": self._internal.is_game_over,
            }
