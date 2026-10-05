"""
Adaptador Pygame para capacidad de HUD.

Implementa HudRenderPort con patrón set_* + render_*.
Usa pygame.font con inicialización perezosa.
"""

import pygame

from adapters.render.pygame_base import PygameBaseAdapter
from domain.ports.render.hud_render_port import HudRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_hud")


class PygameHudRenderer(PygameBaseAdapter, HudRenderPort):
    """Renderizador de HUD con patrón set_* + render_*."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "HUD",
        target_fps: int = 60,
        font_size: int = 24,
        text_color: tuple[int, int, int] = (255, 255, 255),
        background_alpha: int = 128,
    ) -> None:
        PygameBaseAdapter.__init__(
            self,
            width=width,
            height=height,
            title=title,
            target_fps=target_fps,
        )
        self._font_size = font_size
        self._text_color = text_color
        self._background_alpha = background_alpha
        self._font: pygame.font.Font | None = None
        self._score: int = 0
        self._rounds: int = 0
        self._timer: float = 0.0
        self._extra: dict[str, str] | None = None

    def set_hud(
        self,
        score: int,
        rounds: int,
        timer: float,
        extra: dict[str, str] | None = None,
    ) -> None:
        """
        Declara los valores actuales del HUD.

        Args:
            score: Puntuación actual.
            rounds: Número de rondas.
            timer: Tiempo transcurrido/restante (segundos).
            extra: Campos adicionales específicos del juego.
        """
        self._score = score
        self._rounds = rounds
        self._timer = timer
        self._extra = extra

    def render_hud(self) -> None:
        """Dibuja el HUD declarado."""
        self._initialize()

        if not self.is_running:
            return

        font = self._ensure_font()

        lines: list[str] = [
            f"Score: {self._score}",
            f"Rounds: {self._rounds}",
            f"Timer: {self._timer:.2f}",
        ]

        if self._extra:
            for key, value in self._extra.items():
                lines.append(f"{key}: {value}")

        padding = 10
        line_height = font.get_height()
        max_width = 0
        for line in lines:
            text_surface = font.render(line, True, self._text_color)
            max_width = max(max_width, text_surface.get_width())

        bg_height = len(lines) * line_height + padding * 2
        bg_rect = pygame.Surface((max_width + padding * 2, bg_height), pygame.SRCALPHA)
        bg_rect.fill((0, 0, 0, self._background_alpha))
        self.screen.blit(bg_rect, (padding, padding))

        for i, line in enumerate(lines):
            text_surface = font.render(line, True, self._text_color)
            self.screen.blit(text_surface, (padding * 2, padding + i * line_height))

    def close(self) -> None:
        """Limpia recursos del HUD."""
        self._font = None
        super().close()

    def _ensure_font(self) -> pygame.font.Font:
        """Inicializa pygame.font de forma perezosa."""
        if self._font is None:
            pygame.font.init()
            self._font = pygame.font.SysFont(None, self._font_size)
        return self._font
