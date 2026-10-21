"""
Tests TDD para spawn_particles con componentes ECS-lite.
Valida que las partículas generadas tengan la estructura correcta.
"""

import random

import pytest

from pose_app.domain.games.particles.geometry import Workspace
from pose_app.domain.games.particles.spawn import spawn_particles


class TestSpawnParticlesECS:
    """El spawn debe crear partículas con componentes ECS-lite."""

    def test_spawn_creates_particles_with_position_component(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act
        particles = spawn_particles(
            count=3,
            workspace=workspace,
            screen_width=800,
            screen_height=600,
            rng=rng,
        )

        # Assert
        assert len(particles) == 3
        for p in particles:
            assert hasattr(p, "position")
            assert hasattr(p.position, "x")
            assert hasattr(p.position, "y")
            assert hasattr(p.position, "vx")
            assert hasattr(p.position, "vy")
            # Partículas estáticas en este juego
            assert p.position.vx == 0.0
            assert p.position.vy == 0.0

    def test_spawn_creates_particles_with_appearance_component(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act
        particles = spawn_particles(
            count=2,
            workspace=workspace,
            screen_width=800,
            screen_height=600,
            rng=rng,
            particle_size=25.0,
            particle_color=(100, 150, 200),
        )

        # Assert
        for p in particles:
            assert hasattr(p, "appearance")
            assert p.appearance.size == 25.0
            assert p.appearance.color == (100, 150, 200)

    def test_spawn_creates_particles_with_collision_component(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act
        particles = spawn_particles(
            count=2,
            workspace=workspace,
            screen_width=800,
            screen_height=600,
            rng=rng,
            particle_size=30.0,
        )

        # Assert
        for p in particles:
            assert hasattr(p, "collision")
            assert p.collision is not None
            # Radio = size / 2
            assert p.collision.radius == 15.0
            # Comportamiento por defecto: destroy
            assert p.collision.behavior == "destroy"

    def test_spawn_particles_are_infinite(self) -> None:
        """El juego actual no usa decaimiento de vida."""
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act
        particles = spawn_particles(
            count=5,
            workspace=workspace,
            screen_width=800,
            screen_height=600,
            rng=rng,
        )

        # Assert
        for p in particles:
            assert p.lifespan is None  # Infinitas
            assert p.is_alive() is True

    def test_spawn_positions_are_in_pixels(self) -> None:
        # Arrange
        workspace = Workspace(x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0)
        rng = random.Random(42)

        # Act
        particles = spawn_particles(
            count=10,
            workspace=workspace,
            screen_width=800,
            screen_height=600,
            rng=rng,
        )

        # Assert
        for p in particles:
            assert 0.0 <= p.position.x <= 800.0
            assert 0.0 <= p.position.y <= 600.0

    def test_spawn_respects_min_distance(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act
        particles = spawn_particles(
            count=5,
            workspace=workspace,
            screen_width=800,
            screen_height=600,
            rng=rng,
            min_distance=0.2,  # 20% de la pantalla
        )

        # Assert: verificar que ninguna partícula está demasiado cerca de otra
        for i, p1 in enumerate(particles):
            for j, p2 in enumerate(particles):
                if i >= j:
                    continue
                dx = (p1.position.x - p2.position.x) / 800.0
                dy = (p1.position.y - p2.position.y) / 600.0
                distance = (dx**2 + dy**2) ** 0.5
                assert distance >= 0.2 - 0.01  # Tolerancia por redondeo

    def test_spawn_returns_empty_list_for_count_zero(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act
        particles = spawn_particles(
            count=0,
            workspace=workspace,
            screen_width=800,
            screen_height=600,
            rng=rng,
        )

        # Assert
        assert particles == []

    def test_spawn_validates_negative_count(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act & Assert
        with pytest.raises(ValueError, match="count debe ser >= 0"):
            spawn_particles(
                count=-1,
                workspace=workspace,
                screen_width=800,
                screen_height=600,
                rng=rng,
            )

    def test_spawn_validates_invalid_screen_dimensions(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act & Assert
        with pytest.raises(ValueError, match="screen_width debe ser > 0"):
            spawn_particles(
                count=1,
                workspace=workspace,
                screen_width=0,
                screen_height=600,
                rng=rng,
            )

        with pytest.raises(ValueError, match="screen_height debe ser > 0"):
            spawn_particles(
                count=1,
                workspace=workspace,
                screen_width=800,
                screen_height=0,
                rng=rng,
            )

    def test_spawn_validates_negative_min_distance(self) -> None:
        # Arrange
        workspace = Workspace()
        rng = random.Random(42)

        # Act & Assert
        with pytest.raises(ValueError, match="min_distance debe ser >= 0"):
            spawn_particles(
                count=1,
                workspace=workspace,
                screen_width=800,
                screen_height=600,
                rng=rng,
                min_distance=-0.1,
            )
