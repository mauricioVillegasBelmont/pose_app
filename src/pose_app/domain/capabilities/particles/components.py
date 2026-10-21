"""
Componentes ECS-lite para el sistema de partículas.

Representan datos puros. La inmutabilidad (frozen) se usa siempre que sea
posible para prevenir efectos secundarios accidentales.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Position:
    """Componente mutable de estado espacial.

    Es el único componente diseñado para ser modificado in-place por los
    sistemas de movimiento (MovementSystem) por razones de rendimiento.
    """

    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0


@dataclass(frozen=True)
class Appearance:
    """Componente inmutable de representación visual."""

    size: float = 5.0
    color: tuple[int, int, int] = (255, 255, 255)


@dataclass(frozen=True)
class Lifespan:
    """Componente inmutable de ciclo de vida.

    Invariantes:
        max_life > 0
        0 <= current_life <= max_life

    Los sistemas actualizan la vida con dataclasses.replace(),
    que produce una nueva instancia sin modificar la original.
    """

    max_life: float
    current_life: float

    def __post_init__(self) -> None:
        if self.max_life <= 0.0:
            raise ValueError("max_life must be greater than 0")
        if not 0.0 <= self.current_life <= self.max_life:
            raise ValueError(
                f"current_life ({self.current_life}) must be in [0, {self.max_life}]"
            )

    @classmethod
    def fresh(cls, max_life: float) -> Lifespan:
        """Crea una vida recién nacida: current_life == max_life."""
        return cls(max_life=max_life, current_life=max_life)


@dataclass(frozen=True)
class CollisionProfile:
    """Componente inmutable que define cómo interactúa la partícula con el entorno."""

    radius: float
    behavior: Literal["destroy", "bounce"] = "destroy"


@dataclass(frozen=True)
class SpriteConfig:
    """
    Configuración inmutable del sprite (qué dibujar y cómo animar).

    Este componente define la "receta" del sprite. Múltiples partículas
    pueden compartir la misma instancia de SpriteConfig (ej: todas las
    partículas de un mismo tipo).

    Attributes:
        path: Ruta relativa al archivo de imagen (sprite sheet o estático).
        frame_width: Ancho de cada frame en píxeles.
        frame_height: Alto de cada frame en píxeles.
        frame_count: Total de frames (1 para estático, 16 para sprite sheet 4x4).
        fps: Velocidad de animación (0.0 para estático).
        animation_mode: 'loop' (infinito) o 'one_shot' (se detiene al final).
    """

    path: str
    frame_width: float
    frame_height: float
    frame_count: int = 1
    fps: float = 0.0
    animation_mode: Literal["loop", "one_shot"] = "loop"

    def __post_init__(self) -> None:
        if self.frame_count < 1:
            raise ValueError(f"frame_count must be >= 1, got {self.frame_count}")
        if self.fps < 0.0:
            raise ValueError(f"fps must be >= 0.0, got {self.fps}")
        if self.animation_mode not in ("loop", "one_shot"):
            raise ValueError(
                f"animation_mode must be 'loop' or 'one_shot', "
                f"got {self.animation_mode}"
            )


@dataclass
class SpriteState:
    """
    Estado mutable del sprite (qué frame dibujar ahora).

    A diferencia de otros componentes frozen, este es mutable para permitir
    actualizaciones in-place por el AnimationSystem, evitando la sobrecarga
    de crear nuevos objetos en cada frame (rendimiento en tiempo real).

    Attributes:
        current_frame: Índice del frame actual (0 a frame_count-1).
        elapsed_time: Tiempo acumulado desde el último cambio de frame.
    """

    current_frame: int = 0
    elapsed_time: float = 0.0
