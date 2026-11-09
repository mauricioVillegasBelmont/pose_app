"""
Puertos de render legacy, segregados por tipo de juego.

🔴 DEPRECADO: este módulo se mantiene mientras ColorGame y GesturesGame
usan la arquitectura legacy (pre-v0.5). Los juegos nuevos deben usar
`domain/ports/render/` (capacidades + SceneManager).

El ciclo de vida de pygame (init, set_mode, set_caption, quit) NO es
responsabilidad de estos puertos: lo gestiona el bootstrap del plugin
+ el SceneManager (Fase fix-pygame-single-window).

Jerarquía:
    BaseRenderPort (común: close)
        ├── ParticlesRenderPort (render_particles)
        └── ColorRenderPort     (render_background)
"""

from abc import ABC, abstractmethod
from typing import Self

from pose_app.domain.entities.color import RGBColor
from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.pose_landmark import PoseLandmark


class BaseRenderPort(ABC):
    """Puerto legacy de salida: visualización de escenas por frame."""

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
    def render_background(self, color: RGBColor, landmarks: list[PoseLandmark]) -> None:
        """Renderiza un fondo sólido + esqueleto superpuesto."""


class LandmarkAwareRenderPort(ABC):
    """
    Mixin opcional para renderers que quieren recibir landmarks
    además de su input principal.

    🔴 DEPRECADO: en la nueva arquitectura, los landmarks llegan al
    `SceneManager.render_frame(landmarks)` y este los pasa a cada
    capacidad que los necesite. Se elimina en Fase 4.
    """

    @abstractmethod
    def update_landmarks(self, landmarks: list[PoseLandmark]) -> None:
        """Actualiza los landmarks que el renderer usará en el próximo frame."""
