"""
Adaptador Pygame para SceneManager (composición de capacidades + overlays).

Implementa ScenePort. Compone capacidades en orden de registro,
luego overlays, con flush centralizado (pygame.display.flip()).
"""

from collections.abc import Iterable
from typing import Any

import pygame

from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.domain.ports.render.hud_render_port import HudRenderPort
from pose_app.domain.ports.render.overlay_port import OverlayPort
from pose_app.domain.ports.render.particles_render_port import ParticlesRenderPort
from pose_app.domain.ports.render.scene_port import ScenePort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_scene")


class PygameSceneManager(ScenePort):
    """SceneManager que compone capacidades y overlays sobre Pygame."""

    def __init__(
        self,
        surface: Any,
        capabilities: Iterable[object] | None = None,
        overlays: Iterable[OverlayPort] | None = None,
        target_fps: int = 60,
    ) -> None:
        """
        Inicializa el SceneManager.

        Args:
            surface: Superficie de dibujo de Pygame (pygame.Surface).
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
        """
        Registra una capacidad (color, particles, hud, ...).

        Args:
            capability: Instancia que implementa alguna capacidad de render.
        """
        self._capabilities.append(capability)

    def add_overlay(self, overlay: OverlayPort) -> None:
        """
        Registra un overlay.

        Args:
            overlay: Instancia que implementa OverlayPort.
        """
        self._overlays.append(overlay)

    def render_frame(self, landmarks: list[PoseLandmark]) -> None:
        """
        Renderiza un frame completo (capacidades + overlays).

        Las capacidades se renderizan en orden de registro, seguidas
        de los overlays. El flush se realiza de forma centralizada.

        Args:
            landmarks: Landmarks actuales de pose (puede ser lista vacía).
        """
        if self._closed:
            return

        for cap in self._capabilities:
            if isinstance(cap, ColorRenderPort):
                cap.render_color()
            elif isinstance(cap, ParticlesRenderPort):
                cap.render_particles()
            elif isinstance(cap, HudRenderPort):
                cap.render_hud()

        for ov in self._overlays:
            ov.draw(self._surface, landmarks)

        pygame.display.flip()
        self._clock.tick(self._target_fps)

    def close(self) -> None:
        """
        Cierra todas las capacidades y overlays.

        Debe ser idempotente.
        """
        if self._closed:
            return

        for cap in self._capabilities:
            if hasattr(cap, "close"):
                cap.close()
        for ov in self._overlays:
            ov.close()
        self._closed = True
