"""
Adaptadores mock para render.

Cumplen los puertos (ParticlesRenderPort, ColorRenderPort) sin
depender de ninguna librería gráfica.

Uso principal:
- Tests unitarios de casos de uso.
- Modo "headless" (sin ventana) para CI/CD.
- Debug rápido sin abrir ventanas.

Características:
- Registran el último estado renderizado (spy).
- Registran el número de llamadas a cada método.
- No dibujan nada real.
"""

from domain.entities.color import RGBColor
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.render_port import (
    ColorRenderPort,
    LandmarkAwareRenderPort,
    ParticlesRenderPort,
)
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.mock.render")


class MockParticlesRenderAdapter(ParticlesRenderPort, LandmarkAwareRenderPort):
    """
    Mock que implementa ParticlesRenderPort.

    No dibuja nada. Solo guarda el estado para inspección en tests.
    También implementa LandmarkAwareRenderPort para permitir que el
    juego notifique landmarks (útil al probar con PoseDebugOverlay).
    """

    def __init__(self):
        # Spy: último estado recibido
        self.last_particles: list[Particle] = []
        self.last_landmarks: list[PoseLandmark] = []

        # Contadores de llamadas
        self.render_count: int = 0
        self.update_landmarks_count: int = 0
        self.show_count: int = 0
        self.close_count: int = 0

        self.is_closed: bool = False

        logger.debug("MockParticlesRenderAdapter creado")

    # ==========================================
    # ParticlesRenderPort
    # ==========================================

    def render_particles(self, particles: list[Particle]) -> None:
        """Registra las partículas para inspección. No dibuja nada."""
        self.last_particles = list(particles)  # Copia defensiva
        self.render_count += 1

    # ==========================================
    # LandmarkAwareRenderPort
    # ==========================================

    def update_landmarks(self, landmarks: list[PoseLandmark]) -> None:
        """Registra los landmarks para inspección."""
        self.last_landmarks = list(landmarks)
        self.update_landmarks_count += 1

    # ==========================================
    # BaseRenderPort
    # ==========================================

    def show(self) -> None:
        """No bloquea. Solo registra."""
        self.show_count += 1
        logger.debug("Mock show() llamado (no-op)")

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
        self.last_landmarks.clear()
        self.render_count = 0
        self.update_landmarks_count = 0
        self.show_count = 0
        self.close_count = 0
        self.is_closed = False


class MockColorRenderAdapter(ColorRenderPort, LandmarkAwareRenderPort):
    """
    Mock que implementa ColorRenderPort.

    No dibuja nada. Solo guarda el estado para inspección en tests.
    También implementa LandmarkAwareRenderPort por consistencia.
    """

    def __init__(self):
        # Spy: último estado recibido
        self.last_color: RGBColor | None = None
        self.last_landmarks: list[PoseLandmark] = []

        # Contadores
        self.render_count: int = 0
        self.update_landmarks_count: int = 0
        self.show_count: int = 0
        self.close_count: int = 0

        self.is_closed: bool = False

        logger.debug("MockColorRenderAdapter creado")

    # ==========================================
    # ColorRenderPort
    # ==========================================

    def render_background(
        self,
        color: RGBColor,
        landmarks: list[PoseLandmark],
    ) -> None:
        """Registra el color y landmarks. No dibuja nada."""
        self.last_color = color
        self.last_landmarks = list(landmarks)
        self.render_count += 1

    # ==========================================
    # LandmarkAwareRenderPort
    # ==========================================

    def update_landmarks(self, landmarks: list[PoseLandmark]) -> None:
        """Registra los landmarks para inspección."""
        self.last_landmarks = list(landmarks)
        self.update_landmarks_count += 1

    # ==========================================
    # BaseRenderPort
    # ==========================================

    def show(self) -> None:
        """No bloquea. Solo registra."""
        self.show_count += 1
        logger.debug("Mock show() llamado (no-op)")

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
        self.last_landmarks.clear()
        self.render_count = 0
        self.update_landmarks_count = 0
        self.show_count = 0
        self.close_count = 0
        self.is_closed = False
