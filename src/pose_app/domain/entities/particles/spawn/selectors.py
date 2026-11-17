"""
Selectores de arquetipos para el sistema de spawn de partículas.

Incluye una selección aleatoria ponderada y una selección secuencial
determinista. Ambos implementan el protocolo ``ArchetypeSelector``.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field

from pose_app.domain.entities.particles.archetype import ParticleArchetype


@dataclass(frozen=True)
class WeightedSelector:
    """Selecciona arquetipos de forma aleatoria según su ``weight``.

    El peso es relativo: un arquetipo con peso 9 se elige aproximadamente
    9 veces más que uno con peso 1. Los arquetipos con peso 0 nunca se eligen
    mientras exista al menos uno con peso positivo.
    """

    def select(
        self,
        archetypes: list[ParticleArchetype],
        rng: random.Random,
    ) -> ParticleArchetype:
        """Selecciona un arquetipo usando una distribución ponderada.

        Args:
            archetypes: Arquetipos candidatos; debe contener al menos uno.
            rng: Generador aleatorio inyectable para tests deterministas.

        Returns:
            El arquetipo elegido.

        Raises:
            ValueError: Si ``archetypes`` está vacío o si todos los pesos
                son cero.
        """
        if not archetypes:
            raise ValueError("WeightedSelector requires at least one archetype")

        weights = [archetype.weight for archetype in archetypes]
        if all(weight == 0 for weight in weights):
            raise ValueError(
                "WeightedSelector requires at least one archetype with positive weight"
            )

        return rng.choices(archetypes, weights=weights, k=1)[0]


@dataclass(frozen=True)
class SequentialSelector:
    """Selecciona arquetipos siguiendo una secuencia cíclica de nombres.

    La secuencia se recorre en orden y, al llegar al final, vuelve a empezar.
    La selección es determinista e ignora el generador aleatorio.

    Attributes:
        sequence: Nombres de arquetipos en el orden de selección.
    """

    sequence: list[str]
    _cycle: itertools.cycle[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Valida la secuencia e inicializa el ciclo interno.

        Raises:
            ValueError: Si ``sequence`` está vacía.
        """
        if not self.sequence:
            raise ValueError("SequentialSelector sequence must not be empty")
        object.__setattr__(self, "_cycle", itertools.cycle(self.sequence))

    def select(
        self,
        archetypes: list[ParticleArchetype],
        rng: random.Random,
    ) -> ParticleArchetype:
        """Selecciona el siguiente arquetipo de la secuencia.

        Args:
            archetypes: Arquetipos candidatos; debe contener al menos uno.
            rng: Ignorado; la selección es determinista.

        Returns:
            El arquetipo cuyo nombre coincide con el siguiente de la secuencia.

        Raises:
            ValueError: Si ``archetypes`` está vacío o si el nombre de la
                secuencia no existe en ``archetypes``.
        """
        if not archetypes:
            raise ValueError("SequentialSelector requires at least one archetype")

        name = next(self._cycle)
        for archetype in archetypes:
            if archetype.name == name:
                return archetype

        raise ValueError(
            f"SequentialSelector: archetype '{name}' not found in archetypes list"
        )
