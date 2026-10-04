"""
Estado del juego de color.

Implementa GameStatePort. Thread-safe.
"""

from threading import Lock
from typing import Any

from domain.entities.color import RGBColor
from domain.entities.pose_landmark import PoseLandmark
from domain.state.game_state_port import GameStatePort


class ColorState(GameStatePort):
    """Estado consultable del juego de color."""

    def __init__(self, palette_name: str = "fire"):
        self._lock = Lock()
        self._current_color: RGBColor = RGBColor(0, 0, 0)
        self._current_palette: str = palette_name
        self._last_pose: list[PoseLandmark] = []
        self._frame_count: int = 0

    @property
    def game_id(self) -> str:
        return "color"

    # ==========================================
    # API de escritura
    # ==========================================

    def update_color(self, color: RGBColor) -> None:
        with self._lock:
            self._current_color = color

    def update_palette(self, palette_name: str) -> None:
        with self._lock:
            self._current_palette = palette_name

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
            return {
                "background_color": self._current_color.to_hex(),
                "current_palette": self._current_palette,
                "frame_count": self._frame_count,
                "landmarks_count": len(self._last_pose),
            }

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "frames_processed": self._frame_count,
                "current_palette": self._current_palette,
            }
