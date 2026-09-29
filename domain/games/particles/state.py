"""
Estado del juego de partículas.

Implementa GameStatePort. Thread-safe.
"""

from threading import Lock
from typing import Any

from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.state.game_state_port import GameStatePort


class ParticlesState(GameStatePort):
    """
    Estado consultable del juego de partículas.

    El juego (ParticlesGame) escribe; la API lee.
    """

    def __init__(self):
        self._lock = Lock()
        self._particles: list[Particle] = []
        self._last_pose: list[PoseLandmark] = []
        self._frame_count: int = 0

    @property
    def game_id(self) -> str:
        return "particles"

    # ==========================================
    # API de escritura (usada por ParticlesGame)
    # ==========================================

    def update_particles(self, particles: list[Particle]) -> None:
        with self._lock:
            self._particles = list(particles)

    def update_pose(self, landmarks: list[PoseLandmark]) -> None:
        with self._lock:
            self._last_pose = list(landmarks)

    def increment_frames(self) -> None:
        with self._lock:
            self._frame_count += 1

    # ==========================================
    # GameStatePort
    # ==========================================

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            particles_sample = [
                {
                    "x": round(p.x, 2),
                    "y": round(p.y, 2),
                    "life": round(p.life, 3),
                    "size": round(p.size, 2),
                    "color": list(p.color),
                }
                for p in self._particles[:10]
            ]
            return {
                "particles_count": len(self._particles),
                "particles_sample": particles_sample,
                "frame_count": self._frame_count,
                "landmarks_count": len(self._last_pose),
            }

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "particles_active": len(self._particles),
                "frames_processed": self._frame_count,
            }