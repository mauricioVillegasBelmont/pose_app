"""
Adaptador Pygame para capacidad de color (fondo sólido).

Implementa ColorRenderPort con patrón set_* + render_*.
Reutiliza lógica base de PygameBaseAdapter. No dibuja esqueleto
(el esqueleto se gestiona como OverlayPort).
"""

from pose_app.adapters.render.pygame_base import PygameBaseAdapter
from pose_app.domain.entities.color import RGBColor
from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_color")


class PygameColorRenderer(PygameBaseAdapter, ColorRenderPort):
    """Renderizador de color con patrón set_* + render_*."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Color Game",
        target_fps: int = 60,
    ) -> None:
        PygameBaseAdapter.__init__(
            self,
            width=width,
            height=height,
            title=title,
            target_fps=target_fps,
        )
        self._color: RGBColor | None = None

    def set_color(self, color: RGBColor) -> None:
        """
        Declara el color actual.

        Args:
            color: Color RGB a establecer para el próximo render.
        """
        self._color = color

    def render_color(self) -> None:
        """Dibuja el color declarado."""
        self._initialize()

        if not self.is_running:
            return

        color = self._color if self._color is not None else RGBColor(0, 0, 0)
        self.screen.fill(color.to_rgb_tuple())
