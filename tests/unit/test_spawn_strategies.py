"""
Tests para la estrategia compuesta de spawn de partículas.
"""

import random

import pytest

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.components import (
    Appearance,
    CollisionProfile,
    Position,
    SpriteConfig,
    SpriteState,
)
from pose_app.domain.entities.particles.spawn.ports import SpawnStrategy
from pose_app.domain.entities.particles.spawn.positions import (
    GridPositionStrategy,
    RandomPositionStrategy,
)
from pose_app.domain.entities.particles.spawn.selectors import WeightedSelector
from pose_app.domain.entities.particles.spawn.strategies import ComposedSpawnStrategy
from pose_app.domain.games.particles.geometry import Workspace


class TestComposedSpawnStrategy:
    """ComposedSpawnStrategy compone selector y estrategia de posición."""

    def test_implements_spawn_strategy_protocol(self) -> None:
        """La estrategia compuesta cumple el protocolo SpawnStrategy."""
        strategy = ComposedSpawnStrategy(
            archetype_selector=WeightedSelector(),
            position_strategy=GridPositionStrategy(rows=1, cols=1),
        )

        assert isinstance(strategy, SpawnStrategy)

    def test_spawns_correct_count_of_particles(self) -> None:
        """spawn devuelve exactamente count partículas."""
        strategy = ComposedSpawnStrategy(
            archetype_selector=WeightedSelector(),
            position_strategy=GridPositionStrategy(rows=2, cols=3),
        )

        particles = strategy.spawn(
            count=5,
            archetypes=[ParticleArchetype(name="spark")],
            workspace=Workspace(),
            screen_w=800,
            screen_h=600,
            rng=random.Random(42),
        )

        assert len(particles) == 5
        assert all(isinstance(particle, Particle) for particle in particles)

    def test_assembles_ecs_components_correctly(self) -> None:
        """Los componentes ECS se derivan de los valores del arquetipo."""
        sprite_config = SpriteConfig(
            path="spark.png",
            frame_width=32.0,
            frame_height=32.0,
            frame_count=4,
            fps=8.0,
        )
        archetype = ParticleArchetype(
            name="spark",
            size=40.0,
            color=(10, 20, 30),
            sprite_config=sprite_config,
        )
        strategy = ComposedSpawnStrategy(
            archetype_selector=WeightedSelector(),
            position_strategy=GridPositionStrategy(rows=1, cols=1),
        )

        particles = strategy.spawn(
            count=1,
            archetypes=[archetype],
            workspace=Workspace(),
            screen_w=800,
            screen_h=600,
            rng=random.Random(42),
        )

        particle = particles[0]
        assert isinstance(particle.position, Position)
        assert particle.position.vx == 0.0
        assert particle.position.vy == 0.0
        assert isinstance(particle.appearance, Appearance)
        assert particle.appearance.size == 40.0
        assert particle.appearance.color == (10, 20, 30)
        assert isinstance(particle.collision, CollisionProfile)
        assert particle.collision.radius == 20.0
        assert particle.collision.behavior == "destroy"
        assert particle.sprite_config is sprite_config
        assert isinstance(particle.sprite_state, SpriteState)
        assert particle.sprite_state.current_frame == 0
        assert particle.sprite_state.elapsed_time == 0.0

    def test_passes_existing_particles_to_position_strategy(self) -> None:
        """La estrategia compuesta acumula las partículas ya creadas."""
        strategy = ComposedSpawnStrategy(
            archetype_selector=WeightedSelector(),
            position_strategy=RandomPositionStrategy(
                min_distance=0.5,
                max_attempts=10,
            ),
        )

        with pytest.raises(
            ValueError,
            match="Could not find valid position after 10 attempts",
        ):
            strategy.spawn(
                count=5,
                archetypes=[ParticleArchetype(name="spark")],
                workspace=Workspace(
                    x_min=0.0,
                    x_max=0.1,
                    y_min=0.0,
                    y_max=0.1,
                ),
                screen_w=100,
                screen_h=100,
                rng=random.Random(42),
            )

    def test_uses_weighted_selector_distribution(self) -> None:
        """La distribución de arquetipos respeta los pesos configurados."""
        common = ParticleArchetype(
            name="common",
            weight=90.0,
            color=(255, 0, 0),
        )
        rare = ParticleArchetype(
            name="rare",
            weight=10.0,
            color=(0, 0, 255),
        )
        strategy = ComposedSpawnStrategy(
            archetype_selector=WeightedSelector(),
            position_strategy=GridPositionStrategy(rows=40, cols=25),
        )

        particles = strategy.spawn(
            count=1000,
            archetypes=[common, rare],
            workspace=Workspace(),
            screen_w=800,
            screen_h=600,
            rng=random.Random(42),
        )

        common_count = sum(
            1 for particle in particles if particle.appearance.color == (255, 0, 0)
        )
        common_ratio = common_count / len(particles)

        assert common_ratio == pytest.approx(0.9, abs=0.05)
