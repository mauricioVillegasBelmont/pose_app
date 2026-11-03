"""
Puerto de render para cursores de interacción.

Define el contrato para renderizar cursores de usuario (manos, pies, etc.).
Es una capacidad de render (como ParticlesRenderPort), no un overlay,
porque los cursores son parte fundamental de la jugabilidad.
"""

from __future__ import annotations

from abc import abstractmethod

from pose_app.domain.entities.input_cursor import InputCursor
from pose_app.domain.ports.render.render_capability import RenderCapability


class InputCursorRenderPort(RenderCapability):
    """
    Contrato para renderizar cursores de interacción.

    Sigue el patrón set_* + render_* para separar declaración de ejecución.
    """

    @abstractmethod
    def set_cursors(self, cursors: list[InputCursor]) -> None:
        """
        Declara los cursores a renderizar.

        Args:
            cursors: Lista de cursores activos (puede incluir no visibles).
        """

    @abstractmethod
    def render_cursors(self) -> None:
        """
        Renderiza los cursores declarados.

        Solo dibuja cursores con is_visible=True.
        """

    @abstractmethod
    def close(self) -> None:
        """Libera recursos del renderer (sprites cacheados, etc.)."""
