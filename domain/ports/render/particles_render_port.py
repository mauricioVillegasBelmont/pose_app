"""
Puerto de render para capacidad de partículas.

Sigue el patrón set_* + render_* para separar la declaración
de qué dibujar de la ejecución del dibujo.
"""

from abc import ABC, abstractmethod

from domain.entities.particle import Particle


class ParticlesRenderPort(ABC):
    """Capacidad de render: dibujar un sistema de partículas."""

    @abstractmethod
    def set_particles(self, particles: list[Particle]) -> None:
        """
        Declara las partículas a dibujar.

        Args:
            particles: Lista de partículas a renderizar en el próximo frame.
        """

    @abstractmethod
    def render_particles(self) -> None:
        """Dibuja las partículas declaradas."""

    @abstractmethod
    def close(self) -> None:
        """
        Cierra y libera recursos.

        Debe ser idempotente.
        """
