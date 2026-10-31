"""
Protocolos (contratos) para las estrategias de spawn de partículas.

Estos puertos definen cómo se elige un arquetipo, cómo se calcula una
posición y cómo se compone el spawn completo. Las implementaciones concretas
viven en fases posteriores.
"""

from __future__ import annotations

import random
from typing import Protocol, runtime_checkable

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.games.particles.geometry import Workspace


@runtime_checkable
class ArchetypeSelector(Protocol):
    """Elige qué arquetipo usar para una partícula.

    Implementaciones previstas:
        - ``WeightedSelector``: selección aleatoria ponderada por ``weight``.
        - ``SequentialSelector``: recorre los arquetipos en orden.
    """

    def select(
        self,
        archetypes: list[ParticleArchetype],
        rng: random.Random,
    ) -> ParticleArchetype:
        """Selecciona un arquetipo de la lista.

        Args:
            archetypes: Arquetipos disponibles; debe contener al menos uno.
            rng: Generador aleatorio inyectable para tests deterministas.

        Returns:
            El arquetipo elegido.

        Raises:
            ValueError: Si ``archetypes`` está vacío (según implementación).
        """
        ...


@runtime_checkable
class PositionStrategy(Protocol):
    """Calcula la posición de una partícula en píxeles.

    Implementaciones previstas:
        - ``RandomPositionStrategy``: punto aleatorio dentro del workspace.
        - ``GridPositionStrategy``: posiciones deterministas en una grilla.
    """

    def calculate_position(
        self,
        index: int,
        existing_particles: list[Particle],
        workspace: Workspace,
        screen_w: int,
        screen_h: int,
        rng: random.Random,
    ) -> tuple[float, float]:
        """Calcula la posición (x, y) de la partícula ``index``.

        Args:
            index: Índice de la partícula dentro del lote de spawn.
            existing_particles: Partículas ya creadas, para evitar solapamientos.
            workspace: Región normalizada donde pueden aparecer partículas.
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.
            rng: Generador aleatorio inyectable para tests deterministas.

        Returns:
            Coordenadas ``(x, y)`` en píxeles.
        """
        ...


@runtime_checkable
class SpawnStrategy(Protocol):
    """Estrategia completa de creación de partículas.

    Puede ser una composición de ``ArchetypeSelector`` +
    ``PositionStrategy`` o una implementación especializada.
    """

    def spawn(
        self,
        count: int,
        archetypes: list[ParticleArchetype],
        workspace: Workspace,
        screen_w: int,
        screen_h: int,
        rng: random.Random,
    ) -> list[Particle]:
        """Crea ``count`` partículas.

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
        ...
