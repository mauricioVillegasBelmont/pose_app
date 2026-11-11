"""
Adaptadores mock para render.

Cumplen los puertos nuevos (ParticlesRenderPort, ColorRenderPort, ScenePort)
sin depender de ninguna librería gráfica.

Uso principal:
- Tests unitarios de casos de uso.
- Modo "headless" (sin ventana) para CI/CD.
- Debug rápido sin abrir ventanas.

Características:
- Registran el último estado renderizado (spy).
- Registran el número de llamadas a cada método.
- No dibujan nada real.
"""

from collections.abc import Iterable

from pose_app.domain.entities.color import RGBColor
from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.domain.ports.render.overlay_port import OverlayPort
from pose_app.domain.ports.render.particles_render_port import ParticlesRenderPort
from pose_app.domain.ports.render.render_capability import RenderCapability
from pose_app.domain.ports.render.scene_port import ScenePort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.mock.render")


class MockParticlesRenderAdapter(ParticlesRenderPort):
    """
    Mock que implementa ParticlesRenderPort.

    No dibuja nada. Solo guarda el estado para inspección en tests.
    """

    def __init__(self) -> None:
        # Spy: último estado recibido
        self.last_particles: list[Particle] = []
        self._particles: list[Particle] = []

        # Contadores de llamadas
        self.render_count: int = 0
        self.close_count: int = 0

        self.is_closed: bool = False

        logger.debug("MockParticlesRenderAdapter creado")

    # ==========================================
    # ParticlesRenderPort
    # ==========================================

    def set_particles(self, particles: list[Particle]) -> None:
        """Declara las partículas a dibujar (sin dibujar)."""
        self._particles = list(particles)

    def render_particles(self) -> None:
        """Registra las partículas para inspección. No dibuja nada."""
        self.last_particles = list(self._particles)  # Copia defensiva
        self.render_count += 1

    def render(self) -> None:
        """Método unificado de RenderCapability."""
        self.render_particles()

    # ==========================================
    # Ciclo de vida
    # ==========================================

    def close(self) -> None:
        """Marca como cerrado. Idempotente."""
        self.close_count += 1
        self.is_closed = True
        logger.debug("Mock close() llamado")

    # ==========================================
    # Helpers para tests
    # ==========================================

    def reset(self) -> None:
        """Limpia el estado del mock (útil entre tests)."""
        self.last_particles.clear()
        self._particles.clear()
        self.render_count = 0
        self.close_count = 0
        self.is_closed = False


class MockColorRenderAdapter(ColorRenderPort):
    """
    Mock que implementa ColorRenderPort.

    No dibuja nada. Solo guarda el estado para inspección en tests.
    """

    def __init__(self) -> None:
        # Spy: último estado recibido
        self.last_color: RGBColor | None = None
        self._color: RGBColor | None = None

        # Contadores
        self.render_count: int = 0
        self.close_count: int = 0

        self.is_closed: bool = False

        logger.debug("MockColorRenderAdapter creado")

    # ==========================================
    # ColorRenderPort
    # ==========================================

    def set_color(self, color: RGBColor) -> None:
        """Declara el color actual (sin dibujar)."""
        self._color = color
        self.last_color = color

    def render_color(self) -> None:
        """Registra el render. No dibuja nada."""
        self.render_count += 1

    def render(self) -> None:
        """Método unificado de RenderCapability."""
        self.render_color()

    # ==========================================
    # Ciclo de vida
    # ==========================================

    def close(self) -> None:
        """Marca como cerrado. Idempotente."""
        self.close_count += 1
        self.is_closed = True
        logger.debug("Mock close() llamado")

    # ==========================================
    # Helpers para tests
    # ==========================================

    def reset(self) -> None:
        """Limpia el estado del mock (útil entre tests)."""
        self.last_color = None
        self._color = None
        self.render_count = 0
        self.close_count = 0
        self.is_closed = False


class MockSceneManager(ScenePort):
    """
    SceneManager headless para el proveedor de render 'mock'.

    Compone capacidades y overlays sin pygame. No dibuja nada real:
    delega en las capacidades (que también son mocks o spies) y cuenta
    los frames renderizados.
    """

    def __init__(
        self,
        capabilities: Iterable[object] | None = None,
        overlays: Iterable[OverlayPort] | None = None,
    ) -> None:
        """
        Inicializa el SceneManager mock.

        Args:
            capabilities: Capacidades a registrar (orden preservado).
            overlays: Overlays a registrar (orden preservado).
        """
        self._capabilities: list[object] = []
        self._overlays: list[OverlayPort] = []
        self.render_count: int = 0
        self.is_closed: bool = False

        for capability in capabilities or []:
            self.add_capability(capability)
        for overlay in overlays or []:
            self.add_overlay(overlay)

    def add_capability(self, capability: object) -> None:
        """Registra una capacidad (color, particles, hud, ...)."""
        self._capabilities.append(capability)

    def add_overlay(self, overlay: OverlayPort) -> None:
        """Registra un overlay."""
        self._overlays.append(overlay)

    def render_frame(self, landmarks: list[PoseLandmark]) -> None:
        """Ejecuta las capacidades y overlays registrados."""
        if self.is_closed:
            return

        for capability in self._capabilities:
            if isinstance(capability, RenderCapability):
                capability.render()

        for overlay in self._overlays:
            overlay.draw(None, landmarks)

        self.render_count += 1

    def close(self) -> None:
        """Cierra capacidades y overlays. Idempotente."""
        if self.is_closed:
            return

        for capability in self._capabilities:
            if hasattr(capability, "close"):
                capability.close()
        for overlay in self._overlays:
            overlay.close()

        self.is_closed = True
        logger.debug("MockSceneManager cerrado")
