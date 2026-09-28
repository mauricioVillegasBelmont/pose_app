"""
Puertos de render, segregados por tipo de juego.

Siguiendo el principio ISP (Interface Segregation Principle), cada juego
declara explícitamente QUÉ tipo de render necesita:

- ParticlesGame → ParticlesRenderPort
- ColorGame     → ColorRenderPort

Esto permite tener adaptadores especializados (Pygame, WebSocket, Null, ...)
sin obligarlos a implementar métodos que no usan.

Jerarquía:
    BaseRenderPort (común: show, close)
        ├── ParticlesRenderPort (render_particles)
        └── ColorRenderPort     (render_background)
"""

from abc import ABC, abstractmethod
from typing import Self

from domain.entities.color import RGBColor
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark


class BaseRenderPort(ABC):
    """Puerto de salida: visualización de escenas."""

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


# temporal Particles Adapter
class ParticlesRenderPort(BaseRenderPort):
    """Puerto específico para renderizar partículas."""

    @abstractmethod
    def render_particles(self, particles: list[Particle]) -> None:
        """Renderiza una lista de partículas."""


# temporal Color Adapter
class ColorRenderPort(BaseRenderPort):
    """Puerto específico para renderizar fondo de color."""

    @abstractmethod
    def render_background(
        self,
        color: RGBColor,
        landmarks: list[PoseLandmark]
    ) -> None:
        """
        Renderiza un fondo sólido + esqueleto superpuesto.
        """


class LandmarkAwareRenderPort(ABC):
    """
    Puerto opcional para renderers que quieren recibir landmarks
    además de su input principal.

    No todos los renderers lo implementan. Los juegos pueden checarlo
    con isinstance() si quieren ser explícitos.
    """

    @abstractmethod
    def update_landmarks(self, landmarks: list[PoseLandmark]) -> None:
        """Actualiza los landmarks que el renderer usará en el próximo frame."""