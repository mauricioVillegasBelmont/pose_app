"""
Interfaz base para todas las capacidades de render.
Permite que el SceneManager ejecute el renderizado sin conocer los detalles de cada capacidad.
"""

from abc import ABC, abstractmethod


class RenderCapability(ABC):
    """Contrato base para capacidades de renderizado."""

    @abstractmethod
    def render(self) -> None:
        """Ejecuta el dibujo de esta capacidad en la superficie activa."""
