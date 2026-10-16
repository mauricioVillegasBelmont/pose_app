"""
Decorator que superpone la pose (esqueleto) sobre cualquier adaptador
de render basado en Pygame.

Ventajas del patrón Decorator:
- El adaptador decorado NO sabe que existe el overlay.
- Se activa/desactiva por configuración.
- Funciona con cualquier adaptador Pygame (Particles, Color, futuro...).
- No contamina el puerto con métodos de debug.

Uso:
    base = PygameParticlesAdapter(width=800, height=600)
    decorated = PoseDebugOverlay(base)

    decorated.update_landmarks(landmarks)  # del puerto LandmarkAware
    decorated.render_particles(particles)  # del puerto ParticlesRender
"""

from typing import Protocol

import pygame

from pose_app.adapters.render.overlays.pose_overlay import PoseOverlayRenderer
from pose_app.domain.entities.color import RGBColor
from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render_port import (
    ColorRenderPort,
    LandmarkAwareRenderPort,
    ParticlesRenderPort,
)
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pose_debug_overlay")


class PygameRenderable(Protocol):
    """
    Protocolo que describe lo que el decorator necesita
    de un wrapped renderer.

    No es herencia: cualquier objeto que "tenga la forma" sirve.
    """

    @property
    def screen(self) -> pygame.Surface: ...
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...

    def render_particles(self, particles: list[Particle]) -> None: ...
    def render_background(
        self, color: RGBColor, landmarks: list[PoseLandmark]
    ) -> None: ...
    def show(self) -> None: ...
    def close(self) -> None: ...
    def flush(self) -> None: ...


class PoseDebugOverlay(
    ParticlesRenderPort,
    ColorRenderPort,
    LandmarkAwareRenderPort,
):
    """
    Decorator que superpone el esqueleto de pose sobre un adaptador Pygame.

    Implementa los dos puertos de render + LandmarkAwareRenderPort
    para poder decorar cualquiera de los adaptadores y recibir landmarks.

    Solo los métodos del puerto correspondiente serán invocados
    según el adaptador decorado.
    """

    def __init__(
        self,
        wrapped: PygameRenderable,
        pose_overlay: PoseOverlayRenderer | None = None,
    ):
        self._wrapped = wrapped
        self._overlay = pose_overlay or PoseOverlayRenderer()
        self._latest_landmarks: list[PoseLandmark] = []

        logger.info(f"PoseDebugOverlay activo sobre {type(wrapped).__name__}")

    # ==========================================
    # LandmarkAwareRenderPort
    # ==========================================

    def update_landmarks(self, landmarks: list[PoseLandmark]) -> None:
        """Guarda landmarks para pintarlos en el próximo render."""
        self._latest_landmarks = landmarks

    # ==========================================
    # ParticlesRenderPort
    # ==========================================

    def render_particles(self, particles: list[Particle]) -> None:
        """Delega al wrapped y luego dibuja el overlay."""
        self._wrapped.render_particles(particles)
        self._draw_overlay_if_any()

    # ==========================================
    # ColorRenderPort
    # ==========================================

    def render_background(
        self,
        color: RGBColor,
        landmarks: list[PoseLandmark],
    ) -> None:
        """Delega al wrapped y luego dibuja el overlay."""
        self._wrapped.render_background(color, landmarks)
        # En el caso de color, usamos los landmarks entrantes directamente
        self._latest_landmarks = landmarks
        self._draw_overlay_if_any()

    # ==========================================
    # BaseRenderPort (delegado)
    # ==========================================

    def show(self) -> None:
        self._wrapped.show()

    def close(self) -> None:
        self._wrapped.close()

    # ==========================================
    # Helpers privados
    # ==========================================

    def _draw_overlay_if_any(self) -> None:
        """Dibuja el overlay si hay landmarks disponibles."""
        if not self._latest_landmarks:
            return

        self._overlay.draw(
            surface=self._wrapped.screen,
            landmarks=self._latest_landmarks,
            window_size=(self._wrapped.width, self._wrapped.height),
        )
        # Re-flush para que el overlay sea visible
        self._wrapped.flush()
