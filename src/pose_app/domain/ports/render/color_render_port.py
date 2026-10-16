"""
Puerto de render para capacidad de color (fondo sólido).

Sigue el patrón set_* + render_* para separar la declaración
de qué dibujar de la ejecución del dibujo.
"""

from abc import ABC, abstractmethod

from pose_app.domain.entities.color import RGBColor


class ColorRenderPort(ABC):
    """Capacidad de render: pintar un fondo de color sólido."""

    @abstractmethod
    def set_color(self, color: RGBColor) -> None:
        """
        Declara el color actual.

        Args:
            color: Color RGB a establecer para el próximo render.
        """

    @abstractmethod
    def render_color(self) -> None:
        """Dibuja el color declarado."""

    @abstractmethod
    def close(self) -> None:
        """
        Cierra y libera recursos.

        Debe ser idempotente.
        """
