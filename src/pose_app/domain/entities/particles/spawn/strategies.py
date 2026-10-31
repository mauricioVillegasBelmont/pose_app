"""
Estrategia compuesta de spawn de partículas.

Combina un selector de arquetipos con una estrategia de posicionamiento para
crear lotes completos de partículas ECS-lite.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.components import (
    Appearance,
    CollisionProfile,
    Position,
    SpriteState,
)
from pose_app.domain.entities.particles.spawn.ports import (
    ArchetypeSelector,
    PositionStrategy,
)
from pose_app.domain.games.particles.geometry import Workspace


@dataclass(frozen=True)
class ComposedSpawnStrategy:
    """Compone selección de arquetipo y cálculo de posición.

    Por cada partícula elige un arquetipo, calcula una posición y ensambla
    los componentes ECS-lite derivados de la configuración del arquetipo.

    Attributes:
        archetype_selector: Estrategia que elige el arquetipo de cada partícula.
        position_strategy: Estrategia que calcula la posición en píxeles.
    """

    archetype_selector: ArchetypeSelector
    position_strategy: PositionStrategy

    def spawn(
        self,
        count: int,
        archetypes: list[ParticleArchetype],
        workspace: Workspace,
        screen_w: int,
        screen_h: int,
        rng: random.Random,
    ) -> list[Particle]:
        """Crea ``count`` partículas usando las estrategias configuradas.

        Las partículas creadas se acumulan en ``existing_particles`` para que
        la estrategia de posición pueda evitar solapamientos en las
        iteraciones siguientes.

        Args:
            count: Número de partículas a crear.
            archetypes: Arquetipos disponibles para la selección.
            workspace: Región normalizada donde pueden aparecer partículas.
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.
            rng: Generador aleatorio inyectable para tests deterministas.

        Returns:
            Lista con las partículas creadas.
        """
        particles: list[Particle] = []
        existing_particles: list[Particle] = []

        for index in range(count):
            archetype = self.archetype_selector.select(archetypes, rng)
            x, y = self.position_strategy.calculate_position(
                index,
                existing_particles,
                workspace,
                screen_w,
                screen_h,
                rng,
            )

            position = Position(x=x, y=y, vx=0.0, vy=0.0)
            appearance = Appearance(size=archetype.size, color=archetype.color)
            collision = CollisionProfile(
                radius=archetype.size / 2.0,
                behavior="destroy",
            )
            sprite_config = archetype.sprite_config
            sprite_state = (
                SpriteState(current_frame=0, elapsed_time=0.0)
                if sprite_config is not None
                else None
            )

            particle = Particle(
                position=position,
                appearance=appearance,
                collision=collision,
                sprite_config=sprite_config,
                sprite_state=sprite_state,
            )
            particles.append(particle)
            existing_particles.append(particle)

        return particles
