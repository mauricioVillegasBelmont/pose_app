from abc import ABC, abstractmethod
from typing import Self

from domain.entities.color import RGBColor
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark


class RenderPort(ABC):
    """Puerto de salida: visualización de escenas."""

    @abstractmethod
    def render_particles(self, particles: list[Particle]) -> None:
        """Renderiza un sistema de partículas."""

    @abstractmethod
    def render_background(self, color: RGBColor, landmarks: list[PoseLandmark]) -> None:
        """Renderiza un fondo de color sólido + esqueleto superpuesto."""

    @abstractmethod
    def show(self) -> None:
        """Muestra la ventana/visualización (bloquea hasta cerrar)."""

    @abstractmethod
    def close(self) -> None:
        """Cierra la ventana/visualización."""

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()