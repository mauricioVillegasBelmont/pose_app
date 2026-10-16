import random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pose_app.domain.games.particles.geometry import Workspace
from pose_app.domain.games.particles.spawn import spawn_particles

# ==========================================
# spawn_particles
# ==========================================


class TestSpawnParticlesValidation:
    """Tests de validación de parámetros."""

    def test_negative_count_raises(self) -> None:
        """count negativo lanza ValueError."""
        rng = random.Random(42)
        with pytest.raises(ValueError, match="count"):
            spawn_particles(
                count=-1,
                workspace=Workspace(),
                screen_width=800,
                screen_height=600,
                rng=rng,
            )

    def test_zero_screen_width_raises(self) -> None:
        """screen_width=0 lanza ValueError."""
        rng = random.Random(42)
        with pytest.raises(ValueError, match="screen_width"):
            spawn_particles(
                count=1,
                workspace=Workspace(),
                screen_width=0,
                screen_height=600,
                rng=rng,
            )

    def test_zero_screen_height_raises(self) -> None:
        """screen_height=0 lanza ValueError."""
        rng = random.Random(42)
        with pytest.raises(ValueError, match="screen_height"):
            spawn_particles(
                count=1,
                workspace=Workspace(),
                screen_width=800,
                screen_height=0,
                rng=rng,
            )

    def test_negative_min_distance_raises(self) -> None:
        """min_distance negativo lanza ValueError."""
        rng = random.Random(42)
        with pytest.raises(ValueError, match="min_distance"):
            spawn_particles(
                count=1,
                workspace=Workspace(),
                screen_width=800,
                screen_height=600,
                rng=rng,
                min_distance=-0.1,
            )


class TestSpawnParticlesBehavior:
    """Tests del comportamiento de spawn."""

    def test_zero_count_returns_empty(self) -> None:
        """count=0 retorna lista vacía."""
        rng = random.Random(42)
        particles = spawn_particles(
            count=0,
            workspace=Workspace(),
            screen_width=800,
            screen_height=600,
            rng=rng,
        )
        assert particles == []

    def test_spawns_requested_count_when_space_allows(self) -> None:
        """Con espacio suficiente, spawn genera todas las pedidas."""
        rng = random.Random(42)
        particles = spawn_particles(
            count=3,
            workspace=Workspace(),  # workspace grande por defecto
            screen_width=800,
            screen_height=600,
            rng=rng,
            min_distance=0.15,
        )
        assert len(particles) == 3

    def test_all_particles_inside_workspace(self) -> None:
        """Todas las partículas caen dentro del workspace."""
        ws = Workspace(x_min=0.3, x_max=0.7, y_min=0.2, y_max=0.8)
        rng = random.Random(42)
        particles = spawn_particles(
            count=5,
            workspace=ws,
            screen_width=800,
            screen_height=600,
            rng=rng,
            min_distance=0.05,
        )

        for p in particles:
            nx = p.x / 800
            ny = p.y / 600
            assert ws.contains(nx, ny), f"Partícula fuera: ({nx}, {ny})"

    def test_particles_respect_min_distance(self) -> None:
        """Ninguna partícula está más cerca de min_distance de otra."""
        rng = random.Random(42)
        min_dist = 0.2
        particles = spawn_particles(
            count=5,
            workspace=Workspace(),
            screen_width=800,
            screen_height=600,
            rng=rng,
            min_distance=min_dist,
        )

        # Verificar pairwise
        for i, p1 in enumerate(particles):
            for p2 in particles[i + 1 :]:
                nx1, ny1 = p1.x / 800, p1.y / 600
                nx2, ny2 = p2.x / 800, p2.y / 600
                distance = ((nx1 - nx2) ** 2 + (ny1 - ny2) ** 2) ** 0.5
                assert (
                    distance >= min_dist
                ), f"Partículas muy cercanas: {distance} < {min_dist}"

    def test_particles_have_correct_initial_state(self) -> None:
        """Las partículas tienen vx=vy=0, life=1.0."""
        rng = random.Random(42)
        particles = spawn_particles(
            count=3,
            workspace=Workspace(),
            screen_width=800,
            screen_height=600,
            rng=rng,
        )

        for p in particles:
            assert p.vx == 0.0
            assert p.vy == 0.0
            assert p.life == 1.0
            assert p.size == 20.0
            assert p.color == (255, 200, 50)

    def test_custom_particle_params(self) -> None:
        """Se respetan los parámetros custom."""
        rng = random.Random(42)
        particles = spawn_particles(
            count=1,
            workspace=Workspace(),
            screen_width=800,
            screen_height=600,
            rng=rng,
            particle_size=50.0,
            particle_color=(255, 0, 0),
        )

        assert len(particles) == 1
        assert particles[0].size == 50.0
        assert particles[0].color == (255, 0, 0)

    def test_deterministic_with_seed(self) -> None:
        """Con la misma seed, resultado idéntico."""
        ws = Workspace()
        particles1 = spawn_particles(
            count=3,
            workspace=ws,
            screen_width=800,
            screen_height=600,
            rng=random.Random(42),
        )
        particles2 = spawn_particles(
            count=3,
            workspace=ws,
            screen_width=800,
            screen_height=600,
            rng=random.Random(42),
        )

        for p1, p2 in zip(particles1, particles2, strict=True):
            assert p1.x == p2.x
            assert p1.y == p2.y


class TestSpawnParticlesSaturation:
    """Tests del comportamiento cuando el workspace está saturado."""

    def test_small_workspace_returns_fewer(self) -> None:
        """Workspace pequeño + muchas partículas → menos de las pedidas."""
        # Workspace muy pequeño
        ws = Workspace(x_min=0.45, x_max=0.55, y_min=0.45, y_max=0.55)
        rng = random.Random(42)

        particles = spawn_particles(
            count=50,  # imposible meter 50 en tan poco espacio
            workspace=ws,
            screen_width=800,
            screen_height=600,
            rng=rng,
            min_distance=0.15,  # distancia mínima grande
        )

        # No llega a 50, pero tampoco es 0
        assert 0 < len(particles) < 50


class TestSpawnParticlesProperties:
    """Property-based tests de spawn_particles."""

    @given(
        count=st.integers(min_value=0, max_value=20),
        seed=st.integers(min_value=0, max_value=10_000),
    )
    def test_never_exceeds_count(self, count: int, seed: int) -> None:
        """Nunca se generan más partículas que `count`."""
        particles = spawn_particles(
            count=count,
            workspace=Workspace(),
            screen_width=800,
            screen_height=600,
            rng=random.Random(seed),
            min_distance=0.1,
        )
        assert len(particles) <= count

    @given(seed=st.integers(min_value=0, max_value=10_000))
    def test_all_inside_workspace(self, seed: int) -> None:
        """Todas las partículas caen dentro del workspace."""
        ws = Workspace()
        particles = spawn_particles(
            count=5,
            workspace=ws,
            screen_width=800,
            screen_height=600,
            rng=random.Random(seed),
            min_distance=0.1,
        )

        for p in particles:
            nx = p.x / 800
            ny = p.y / 600
            assert ws.contains(nx, ny)
