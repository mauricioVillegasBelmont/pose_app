"""
Tests para las estrategias de posicionamiento del sistema de spawn.
"""

import math
import random

import pytest

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.components import Appearance, Position
from pose_app.domain.entities.particles.spawn.positions import (
    GridPositionStrategy,
    RandomPositionStrategy,
)
from pose_app.domain.games.particles.geometry import Workspace


def _particle_at(x: float, y: float) -> Particle:
    """Crea una partícula de prueba en la posición indicada."""
    return Particle(
        position=Position(x=x, y=y),
        appearance=Appearance(),
    )


class TestRandomPositionStrategy:
    """RandomPositionStrategy genera posiciones aleatorias sin solapamientos."""

    def test_returns_position_within_workspace(self) -> None:
        """La posición generada está dentro de los límites del workspace."""
        workspace = Workspace()
        screen_w = 800
        screen_h = 600
        strategy = RandomPositionStrategy()

        x, y = strategy.calculate_position(
            index=0,
            existing_particles=[],
            workspace=workspace,
            screen_w=screen_w,
            screen_h=screen_h,
            rng=random.Random(42),
        )

        assert workspace.x_min * screen_w <= x <= workspace.x_max * screen_w
        assert workspace.y_min * screen_h <= y <= workspace.y_max * screen_h

    def test_respects_min_distance(self) -> None:
        """Las partículas nuevas mantienen la separación mínima exigida."""
        workspace = Workspace(x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0)
        screen_w = 200
        screen_h = 200
        strategy = RandomPositionStrategy(min_distance=0.1, max_attempts=500)
        rng = random.Random(42)
        particles: list[Particle] = []
        min_distance_px = strategy.min_distance * min(screen_w, screen_h)

        for index in range(5):
            x, y = strategy.calculate_position(
                index=index,
                existing_particles=particles,
                workspace=workspace,
                screen_w=screen_w,
                screen_h=screen_h,
                rng=rng,
            )
            particles.append(_particle_at(x, y))

        for i, first in enumerate(particles):
            for second in particles[i + 1 :]:
                distance = math.hypot(
                    first.position.x - second.position.x,
                    first.position.y - second.position.y,
                )
                assert distance >= min_distance_px

    def test_raises_after_max_attempts(self) -> None:
        """Si no hay espacio suficiente, se agotan los intentos y falla."""
        workspace = Workspace(x_min=0.49, x_max=0.51, y_min=0.49, y_max=0.51)
        existing = [_particle_at(50.0, 50.0)]
        strategy = RandomPositionStrategy(min_distance=0.5, max_attempts=10)

        with pytest.raises(
            ValueError,
            match="Could not find valid position after 10 attempts",
        ):
            strategy.calculate_position(
                index=0,
                existing_particles=existing,
                workspace=workspace,
                screen_w=100,
                screen_h=100,
                rng=random.Random(42),
            )

    def test_zero_min_distance_allows_any_position(self) -> None:
        """Con min_distance 0, cualquier posición del workspace es válida."""
        workspace = Workspace()
        strategy = RandomPositionStrategy(min_distance=0.0, max_attempts=1)

        position = strategy.calculate_position(
            index=0,
            existing_particles=[_particle_at(400.0, 300.0)],
            workspace=workspace,
            screen_w=800,
            screen_h=600,
            rng=random.Random(42),
        )

        assert isinstance(position, tuple)
        assert len(position) == 2


class TestGridPositionStrategy:
    """GridPositionStrategy coloca partículas de forma determinista."""

    def test_calculates_grid_positions_correctly(self) -> None:
        """Cada índice se coloca en el centro de su celda."""
        workspace = Workspace(x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0)
        strategy = GridPositionStrategy(rows=2, cols=2)
        rng = random.Random(42)

        positions = [
            strategy.calculate_position(
                index=index,
                existing_particles=[],
                workspace=workspace,
                screen_w=100,
                screen_h=100,
                rng=rng,
            )
            for index in range(4)
        ]

        assert positions == [
            (25.0, 25.0),
            (75.0, 25.0),
            (25.0, 75.0),
            (75.0, 75.0),
        ]

    def test_respects_workspace_bounds(self) -> None:
        """Todas las celdas de la grilla caen dentro del workspace."""
        workspace = Workspace()
        screen_w = 800
        screen_h = 600
        strategy = GridPositionStrategy(rows=3, cols=4)
        rng = random.Random(42)

        for index in range(12):
            x, y = strategy.calculate_position(
                index=index,
                existing_particles=[],
                workspace=workspace,
                screen_w=screen_w,
                screen_h=screen_h,
                rng=rng,
            )
            assert workspace.x_min * screen_w <= x <= workspace.x_max * screen_w
            assert workspace.y_min * screen_h <= y <= workspace.y_max * screen_h

    def test_raises_when_count_exceeds_grid_capacity(self) -> None:
        """Un índice fuera de la grilla no tiene celda asignada."""
        strategy = GridPositionStrategy(rows=2, cols=2)

        with pytest.raises(ValueError, match="index 4 exceeds grid capacity"):
            strategy.calculate_position(
                index=4,
                existing_particles=[],
                workspace=Workspace(),
                screen_w=800,
                screen_h=600,
                rng=random.Random(42),
            )

    def test_rng_parameter_is_ignored(self) -> None:
        """La posición es la misma independientemente del rng."""
        workspace = Workspace()
        strategy = GridPositionStrategy(rows=2, cols=2)

        first = strategy.calculate_position(
            index=1,
            existing_particles=[],
            workspace=workspace,
            screen_w=800,
            screen_h=600,
            rng=random.Random(1),
        )
        second = strategy.calculate_position(
            index=1,
            existing_particles=[],
            workspace=workspace,
            screen_w=800,
            screen_h=600,
            rng=random.Random(999),
        )

        assert first == second
