"""
Capabilities de lifespan.

Definen cuándo una partícula deja de estar "viva".

No dependen de pygame, cv2, ni de frameworks.

Contrato:
    - `is_alive(born_at, now) -> bool`: la partícula está viva.
    - `max_age -> float | None`: edad máxima (None = infinito).
    - Sin efectos secundarios (puro).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class LifespanCapability(ABC):
    """
    Especifica cuándo una partícula expira.

    La partícula guarda `born_at` (timestamp). La capability
    decide si sigue viva dado el timestamp actual.
    """

    @abstractmethod
    def is_alive(self, born_at: float, now: float) -> bool:
        """
        ¿Sigue viva la partícula?

        Args:
            born_at: timestamp (segundos, monotónico) de nacimiento.
            now: timestamp actual.

        Returns:
            True si debe seguir existiendo.
        """
        ...

    @property
    @abstractmethod
    def max_age(self) -> float | None:
        """
        Edad máxima en segundos (None = infinito).

        Útil para el juego (e.g. limpiar partículas viejas,
        calcular factor de opacidad).
        """
        ...


@dataclass(frozen=True)
class InfiniteLifespan(LifespanCapability):
    """La partícula nunca expira por sí misma."""

    def is_alive(self, born_at: float, now: float) -> bool:
        return True

    @property
    def max_age(self) -> float | None:
        return None


@dataclass(frozen=True)
class TimedLifespan(LifespanCapability):
    """
    La partícula expira tras `seconds` segundos.

    Ejemplo:
        TimedLifespan(seconds=2.0) → expira a los 2 seg.
    """

    seconds: float

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError(f"seconds debe ser > 0, recibido: {self.seconds}")

    def is_alive(self, born_at: float, now: float) -> bool:
        return (now - born_at) < self.seconds

    @property
    def max_age(self) -> float | None:
        return self.seconds
