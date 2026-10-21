"""
Entidad Particle refactorizada bajo el patrón ECS-lite.
Actúa como un contenedor de componentes, delegando la lógica a los sistemas.
"""

import uuid
from dataclasses import dataclass, field

from pose_app.domain.capabilities.particles.components import (
    Appearance,
    CollisionProfile,
    Lifespan,
    Position,
    SpriteConfig,
    SpriteState,
)


@dataclass
class Particle:
    """
    Entidad ECS-lite.
    La presencia o ausencia de un componente define su comportamiento.
    """

    # 1. Componentes obligatorios (sin valor por defecto)
    position: Position
    appearance: Appearance

    # 2. Componentes con valor por defecto o generados (deben ir después)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lifespan: Lifespan | None = None
    collision: CollisionProfile | None = None

    sprite_config: SpriteConfig | None = None
    sprite_state: SpriteState | None = None

    def is_alive(self) -> bool:
        """
        Determina si la partícula debe seguir siendo procesada.
        Si no tiene componente Lifespan, se considera infinita (viva).
        """
        if self.lifespan is None:
            return True
        return self.lifespan.current_life >= 0.01
