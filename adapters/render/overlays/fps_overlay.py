"""
Overlay para mostrar FPS.

Implementa OverlayPort. Ignora landmarks.
"""

from time import perf_counter
from typing import Any

import pygame

from domain.entities.pose_landmark import PoseLandmark
from domain.ports.render.overlay_port import OverlayPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.overlays.fps")


class FpsOverlay(OverlayPort):
    """Overlay que muestra FPS en pantalla."""

    def __init__(
        self,
        font_size: int = 24,
        text_color: tuple[int, int, int] = (255, 255, 255),
        background_alpha: int = 128,
        position: tuple[int, int] = (10, 10),
    ) -> None:
        self._font_size = font_size
        self._text_color = text_color
        self._background_alpha = background_alpha
        self._position = position
        self._font: pygame.font.Font | None = None
        self._last_time = perf_counter()
        self._frames = 0
        self._fps = 0.0

    def draw(
        self,
        surface: Any,
        landmarks: list[PoseLandmark] | None = None,
    ) -> None:
        """
        Dibuja FPS en pantalla.

        Args:
            surface: Superficie Pygame.
            landmarks: Ignorados.
        """
        self._frames += 1
        now = perf_counter()
        if now - self._last_time >= 1.0:
            self._fps = self._frames / (now - self._last_time)
            self._frames = 0
            self._last_time = now

        font = self._ensure_font()
        text = f"FPS: {self._fps:.1f}"
        text_surface = font.render(text, True, self._text_color)
        padding = 5
        bg = pygame.Surface(
            (
                text_surface.get_width() + padding * 2,
                text_surface.get_height() + padding * 2,
            ),
            pygame.SRCALPHA,
        )
        bg.fill((0, 0, 0, self._background_alpha))
        surface.blit(bg, self._position)
        surface.blit(
            text_surface,
            (self._position[0] + padding, self._position[1] + padding),
        )

    def close(self) -> None:
        """Libera recursos."""
        self._font = None

    def _ensure_font(self) -> pygame.font.Font:
        """Inicializa pygame.font de forma perezosa."""
        if self._font is None:
            pygame.font.init()
            self._font = pygame.font.SysFont(None, self._font_size)
        return self._font
