
from adapters.render.overlays.pose_overlay import PoseOverlayRenderer
from adapters.render.pygame_base import PygameBaseAdapter
from domain.entities.color import RGBColor
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.render_port import ColorRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_color")


class PygameColorAdapter(PygameBaseAdapter, ColorRenderPort):
    """
    Adaptador Pygame que renderiza un fondo sólido + esqueleto.

    Características:
    - Fondo dinámico (color calculado por el juego).
    - Esqueleto superpuesto usando PoseOverlayRenderer.

    NOTA: El esqueleto es parte de la FEATURE del juego (no es debug).
    Usa composición con PoseOverlayRenderer para evitar duplicación.
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Color Game",
        target_fps: int = 60,
        pose_overlay: PoseOverlayRenderer | None = None,
    ):
        PygameBaseAdapter.__init__(
            self,
            width=width,
            height=height,
            title=title,
            target_fps=target_fps,
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

        # 3. Actualiza pantalla + FPS
        self.flush()

        # 4. Eventos
        self._handle_events()