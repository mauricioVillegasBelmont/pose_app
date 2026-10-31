"""
Value Object que define el "ADN" de un tipo de partícula.

Un ParticleArchetype describe las propiedades inmutables compartidas por
todas las partículas de un mismo tipo: peso de spawn, tamaño, color y
configuración de sprite opcional.
"""

from __future__ import annotations

from dataclasses import dataclass

from pose_app.domain.entities.particles.components import SpriteConfig


@dataclass(frozen=True)
class ParticleArchetype:
    """Plantilla inmutable para crear partículas de un tipo concreto.

    Attributes:
        name: Identificador legible del arquetipo.
        weight: Peso relativo usado por el spawn aleatorio. Debe ser >= 0.
        size: Tamaño visual en píxeles. Debe ser > 0.
        color: Color RGB de la partícula (cada componente en 0-255).
        sprite_config: Configuración opcional de sprite; si es None se
            renderiza una forma geométrica con ``color`` y ``size``.

    Raises:
        ValueError: Si algún campo incumple sus invariantes.
    """

    name: str
    weight: float = 1.0
    size: float = 20.0
    color: tuple[int, int, int] = (255, 200, 50)
    sprite_config: SpriteConfig | None = None

    def __post_init__(self) -> None:
        """Valida los invariantes del arquetipo tras la construcción.

        Raises:
            ValueError: Si ``name`` está vacío, ``weight`` es negativo,
                ``size`` no es positivo o ``color`` no es un RGB válido.
        """
        if not self.name:
            raise ValueError("name must not be empty")
        if self.weight < 0:
            raise ValueError("weight must be non-negative")
        if self.size <= 0:
            raise ValueError("size must be positive")
        if len(self.color) != 3 or any(
            not isinstance(component, int) or not 0 <= component <= 255
            for component in self.color
        ):
            raise ValueError("color must be a tuple of 3 integers in range 0-255")
