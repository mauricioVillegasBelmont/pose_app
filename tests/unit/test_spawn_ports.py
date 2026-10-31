"""
Tests para los protocolos de estrategias de spawn de partículas.
"""

import random

import pytest
from typing_extensions import get_protocol_members

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.components import Appearance, Position
from pose_app.domain.entities.particles.spawn.ports import (
    ArchetypeSelector,
    PositionStrategy,
    SpawnStrategy,
)
from pose_app.domain.games.particles.geometry import Workspace

FIXED_X = 400.0
FIXED_Y = 300.0


class DummyArchetypeSelector:
    """Selector de prueba que siempre devuelve el primer arquetipo."""

    def select(
        self,
        archetypes: list[ParticleArchetype],
        rng: random.Random,
    ) -> ParticleArchetype:
        """Devuelve el primer arquetipo, ignorando el generador aleatorio."""
        return archetypes[0]


class DummyPositionStrategy:
    """Estrategia de prueba que siempre devuelve una posición fija."""

    def calculate_position(
        self,
        index: int,
        existing_particles: list[Particle],
        workspace: Workspace,
        screen_w: int,
        screen_h: int,
        rng: random.Random,
    ) -> tuple[float, float]:
        """Devuelve la posición fija ``(400.0, 300.0)``."""
        return (FIXED_X, FIXED_Y)


class DummySpawnStrategy:
    """Estrategia de prueba que crea partículas en una posición fija."""

    def spawn(
        self,
        count: int,
        archetypes: list[ParticleArchetype],
        workspace: Workspace,
        screen_w: int,
        screen_h: int,
        rng: random.Random,
    ) -> list[Particle]:
        """Crea ``count`` partículas en ``(400.0, 300.0)``."""
        return [
            Particle(
                position=Position(x=FIXED_X, y=FIXED_Y),
                appearance=Appearance(),
            )
            for _ in range(count)
        ]


def _required_protocol_members(protocol: type) -> frozenset[str]:
    """Obtiene los miembros requeridos por un protocolo.

    En Python 3.11 ``typing.Protocol`` no materializa ``__protocol_attrs__``;
    se usa ``get_protocol_members`` como fallback público para cubrir ambas
    versiones.
    """
    attrs = getattr(protocol, "__protocol_attrs__", None)
    if attrs is not None:
        return frozenset(attrs)
    return get_protocol_members(protocol)


class TestArchetypeSelectorProtocol:
    """Contrato para elegir el arquetipo de cada partícula."""

    def test_dummy_implements_protocol(self) -> None:
        """El dummy cumple estructuralmente con ArchetypeSelector."""
        assert isinstance(DummyArchetypeSelector(), ArchetypeSelector)

    def test_method_returns_expected_type(self) -> None:
        """select devuelve un ParticleArchetype de la lista recibida."""
        archetype = ParticleArchetype(name="spark")

        selected = DummyArchetypeSelector().select([archetype], random.Random(0))

        assert isinstance(selected, ParticleArchetype)
        assert selected is archetype


class TestPositionStrategyProtocol:
    """Contrato para calcular la posición de una partícula."""

    def test_dummy_implements_protocol(self) -> None:
        """El dummy cumple estructuralmente con PositionStrategy."""
        assert isinstance(DummyPositionStrategy(), PositionStrategy)

    def test_method_returns_expected_type(self) -> None:
        """calculate_position devuelve una tupla de dos floats."""
        position = DummyPositionStrategy().calculate_position(
            index=0,
            existing_particles=[],
            workspace=Workspace(),
            screen_w=800,
            screen_h=600,
            rng=random.Random(0),
        )

        assert isinstance(position, tuple)
        assert len(position) == 2
        assert all(isinstance(coord, float) for coord in position)
        assert position == (FIXED_X, FIXED_Y)


class TestSpawnStrategyProtocol:
    """Contrato para crear un lote completo de partículas."""

    def test_dummy_implements_protocol(self) -> None:
        """El dummy cumple estructuralmente con SpawnStrategy."""
        assert isinstance(DummySpawnStrategy(), SpawnStrategy)

    def test_method_returns_expected_type(self) -> None:
        """spawn devuelve una lista con count partículas."""
        particles = DummySpawnStrategy().spawn(
            count=3,
            archetypes=[ParticleArchetype(name="spark")],
            workspace=Workspace(),
            screen_w=800,
            screen_h=600,
            rng=random.Random(0),
        )

        assert isinstance(particles, list)
        assert len(particles) == 3
        assert all(isinstance(particle, Particle) for particle in particles)
        assert all(
            (particle.position.x, particle.position.y) == (FIXED_X, FIXED_Y)
            for particle in particles
        )


class TestRuntimeCheckableProtocols:
    """Los protocolos deben poder comprobarse estructuralmente en runtime."""

    @pytest.mark.parametrize(
        ("protocol", "expected_members"),
        [
            (ArchetypeSelector, frozenset({"select"})),
            (PositionStrategy, frozenset({"calculate_position"})),
            (SpawnStrategy, frozenset({"spawn"})),
        ],
    )
    def test_protocols_expose_required_members(
        self,
        protocol: type,
        expected_members: frozenset[str],
    ) -> None:
        """Cada protocolo declara exactamente sus miembros requeridos."""
        assert _required_protocol_members(protocol) == expected_members

    @pytest.mark.parametrize(
        "protocol",
        [ArchetypeSelector, PositionStrategy, SpawnStrategy],
    )
    def test_non_conforming_object_is_rejected(self, protocol: type) -> None:
        """Un objeto sin los métodos requeridos no cumple el protocolo."""
        assert not isinstance(object(), protocol)
