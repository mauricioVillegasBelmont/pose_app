"""
Puerto del SceneManager (composición de capacidades + overlays).

El SceneManager compone varias capacidades sobre una misma ventana
y dibuja overlays superpuestos. Sigue el flujo: capacidades (en orden
de registro) → overlays → flush centralizado.
"""

from abc import ABC, abstractmethod

from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render.overlay_port import OverlayPort


class ScenePort(ABC):
    """Contrato del SceneManager para componer capacidades y overlays."""

    @abstractmethod
    def add_capability(self, capability: object) -> None:
        """
        Registra una capacidad (color, particles, hud, ...).

        Args:
            capability: Instancia que implementa alguna capacidad de render.
        """

    @abstractmethod
    def add_overlay(self, overlay: OverlayPort) -> None:
        """
        Registra un overlay.

        Args:
            overlay: Instancia que implementa OverlayPort.
        """

    @abstractmethod
    def render_frame(self, landmarks: list[PoseLandmark]) -> None:
        """
        Renderiza un frame completo (capacidades + overlays).

        Las capacidades se renderizan en orden de registro, seguidas
        de los overlays. El flush se realiza de forma centralizada.

        Args:
            landmarks: Landmarks actuales de pose (puede ser lista vacía).
        """

    @abstractmethod
    def close(self) -> None:
        """
        Cierra todas las capacidades y overlays.

        Debe ser idempotente.
        """
