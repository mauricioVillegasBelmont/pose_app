"""
Value Object que define el "ADN" de un tipo de partícula.

Un ParticleArchetype describe las propiedades inmutables compartidas por
todas las partículas de un mismo tipo: peso de spawn, apariencia visual
(composición de ``Appearance``) y configuración de sprite opcional.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pose_app.domain.entities.particles.components import Appearance, SpriteConfig


@dataclass(frozen=True)
class ParticleArchetype:
    """Plantilla inmutable para crear partículas de un tipo concreto.

    Compone un ``Appearance`` completo (frozen, compartible entre todas las
    partículas del mismo arquetipo). Esto evita duplicar campos de apariencia
    (size, color, padding) entre el arquetipo y el componente ECS.

    Attributes:
        name: Identificador legible del arquetipo. Debe ser no vacío.
        weight: Peso relativo usado por el spawn aleatorio. Debe ser >= 0.
        appearance: Componente visual compartido. Default: ``Appearance()``.
        sprite_config: Configuración opcional de sprite; si es None se
            renderiza una forma geométrica con ``appearance``.

    Raises:
        ValueError: Si ``name`` está vacío o ``weight`` es negativo.
    """

    name: str
    weight: float = 1.0
    appearance: Appearance = field(default_factory=Appearance)
    sprite_config: SpriteConfig | None = None

    def __post_init__(self) -> None:
        """Valida los invariantes del arquetipo tras la construcción.

        Raises:
            ValueError: Si ``name`` está vacío o ``weight`` es negativo.
        """
        if not self.name:
            raise ValueError("name must not be empty")
        if self.weight < 0:
            raise ValueError("weight must be non-negative")
