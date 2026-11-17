"""
Adaptador Pygame para SceneManager (composición de capacidades + overlays).

Implementa ScenePort. Compone capacidades en orden de registro,
luego overlays, con flush centralizado (pygame.display.flip()).

Es el ÚNICO dueño del ciclo de vida de pygame:
- Crea el Clock.
- Hace flip() en cada frame.
- Llama pygame.quit() en close().
"""

from collections.abc import Iterable

import pygame

from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render.overlay_port import OverlayPort
from pose_app.domain.ports.render.render_capability import RenderCapability
from pose_app.domain.ports.render.scene_port import ScenePort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_scene")


class PygameSceneManager(ScenePort):
    """SceneManager que compone capacidades y overlays sobre Pygame."""

    def __init__(
        self,
        surface: pygame.Surface,
        capabilities: Iterable[object] | None = None,
        overlays: Iterable[OverlayPort] | None = None,
        target_fps: int = 60,
    ) -> None:
        """
        Inicializa el SceneManager.

        Args:
            surface: Superficie de dibujo compartida (creada por el bootstrap).
            capabilities: Iterable de capacidades a registrar (orden preservado).
            overlays: Iterable de overlays a registrar (orden preservado).
            target_fps: FPS objetivo para clock.tick().
        """
        self._surface = surface
        self._capabilities: list[object] = []
        self._overlays: list[OverlayPort] = []
        self._target_fps = target_fps
        self._clock: pygame.time.Clock = pygame.time.Clock()
        self._closed = False

        if capabilities is not None:
            for cap in capabilities:
                self.add_capability(cap)

        if overlays is not None:
            for ov in overlays:
                self.add_overlay(ov)

    def add_capability(self, capability: object) -> None:
        """Registra una capacidad (color, particles, hud, ...)."""
        self._capabilities.append(capability)

    def add_overlay(self, overlay: OverlayPort) -> None:
        """Registra un overlay."""
        self._overlays.append(overlay)

    def render_frame(self, landmarks: list[PoseLandmark]) -> None:
        """
        Renderiza un frame completo (capacidades + overlays).

        Las capacidades se renderizan en orden de registro, seguidas
        de los overlays. El flush se realiza de forma centralizada.
        """
        if self._closed:
            return

        for cap in self._capabilities:
            if isinstance(cap, RenderCapability):
                cap.render()

        for ov in self._overlays:
            ov.draw(self._surface, landmarks)

        pygame.display.flip()
        self._clock.tick(self._target_fps)

    def close(self) -> None:
        """
        Cierra todas las capacidades, overlays y pygame.

        Es el ÚNICO punto del proceso que llama pygame.quit(). Idempotente.
        """
        if self._closed:
            return

        for cap in self._capabilities:
            if hasattr(cap, "close"):
                cap.close()
        for ov in self._overlays:
            ov.close()

        pygame.quit()
        self._closed = True
        logger.info("Pygame cerrado por SceneManager")
