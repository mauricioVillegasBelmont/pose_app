"""
Adaptador Pygame legacy que renderiza un fondo sólido + esqueleto.

🔴 DEPRECADO: será reemplazado por capacidades en Fase 4 (ColorGame y
GesturesGame migrarán a la nueva arquitectura de render).
"""

import pygame

from pose_app.adapters.render.overlays.pose_overlay import PoseOverlayRenderer
from pose_app.adapters.render.pygame_base import PygameBaseAdapter
from pose_app.domain.entities.color import RGBColor
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render_port import ColorRenderPort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_color_adapter")


class PygameColorAdapter(PygameBaseAdapter, ColorRenderPort):
    """Adaptador Pygame que renderiza un fondo sólido + esqueleto."""

    def __init__(
        self,
        surface: pygame.Surface,
        target_fps: int = 60,
        title: str = "Color Game",
        pose_overlay: PoseOverlayRenderer | None = None,
    ) -> None:
        PygameBaseAdapter.__init__(
            self,
            surface=surface,
            target_fps=target_fps,
            title=title,
        )
        self._pose_overlay = pose_overlay or PoseOverlayRenderer()

    def render_background(
        self,
        color: RGBColor,
        landmarks: list[PoseLandmark],
    ) -> None:
        """Renderiza fondo sólido + esqueleto."""
        self._initialize()

        if not self.is_running:
            return

        # 1. Fondo
        self.screen.fill(color.to_rgb_tuple())

        # 2. Esqueleto
        if landmarks:
            self._pose_overlay.draw(
                surface=self.screen,
                landmarks=landmarks,
                window_size=(self.width, self.height),
            )

        # 3. Flip + FPS
        pygame.display.flip()

        # 4. Eventos
        self._handle_events()

    def close(self) -> None:
        """Cierra el adaptador. NO cierra pygame (lo hace el SceneManager)."""
        super().close()
