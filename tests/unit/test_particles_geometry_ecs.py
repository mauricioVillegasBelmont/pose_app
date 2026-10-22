"""
Tests TDD para detect_collisions con componentes ECS-lite.
Valida que la detección de colisiones funcione con la nueva estructura.
"""

import pytest

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.components import (
    Appearance,
    CollisionProfile,
    Position,
)
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.games.particles.geometry import (
    detect_collisions,
)


def make_particle(x: float, y: float, radius: float = 10.0) -> Particle:
    """Factory de tests para partículas ECS-lite."""
    return Particle(
        position=Position(x=x, y=y),
        appearance=Appearance(),
        collision=CollisionProfile(radius=radius, behavior="destroy"),
    )


def make_landmark(
    x: float, y: float, name: str = "right_wrist", visibility: float = 1.0
) -> PoseLandmark:
    """Factory de tests para landmarks."""
    return PoseLandmark(x=x, y=y, z=0.0, visibility=visibility, name=name)


class TestDetectCollisionsECS:
    """detect_collisions debe funcionar con partículas ECS-lite."""

    def test_no_collision_when_far_away(self) -> None:
        # Arrange
        particle = make_particle(x=100.0, y=100.0)
        landmark = make_landmark(x=0.9, y=0.9)  # Lejos en coordenadas normalizadas
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[particle],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == [particle]
        assert hits == 0

    def test_collision_when_close(self) -> None:
        # Arrange
        particle = make_particle(x=400.0, y=300.0)
        # Landmark en (0.5, 0.5) normalizado → (400, 300) en píxeles
        landmark = make_landmark(x=0.5, y=0.5)
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[particle],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == []
        assert hits == 1

    def test_collision_at_boundary(self) -> None:
        # Arrange: partícula en (400, 300), landmark a 29 píxeles (dentro de 30)
        particle = make_particle(x=400.0, y=300.0)
        landmark = make_landmark(
            x=(400 + 29) / 800, y=300 / 600
        )  # 29 píxeles de distancia
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[particle],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == []
        assert hits == 1

    def test_no_collision_just_outside_boundary(self) -> None:
        # Arrange: partícula en (400, 300), landmark a 31 píxeles (fuera de 30)
        particle = make_particle(x=400.0, y=300.0)
        landmark = make_landmark(
            x=(400 + 31) / 800, y=300 / 600
        )  # 31 píxeles de distancia
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[particle],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == [particle]
        assert hits == 0

    def test_multiple_particles_multiple_hits(self) -> None:
        # Arrange
        p1 = make_particle(x=100.0, y=100.0)
        p2 = make_particle(x=400.0, y=300.0)  # Será tocada
        p3 = make_particle(x=700.0, y=500.0)
        landmark = make_landmark(x=0.5, y=0.5)  # Toca p2
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[p1, p2, p3],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == [p1, p3]
        assert hits == 1

    def test_invisible_landmark_does_not_collide(self) -> None:
        # Arrange
        particle = make_particle(x=400.0, y=300.0)
        landmark = make_landmark(x=0.5, y=0.5, visibility=0.3)  # Invisible
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[particle],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
            min_visibility=0.5,
        )

        # Assert
        assert remaining == [particle]
        assert hits == 0

    def test_non_touch_landmark_does_not_collide(self) -> None:
        # Arrange
        particle = make_particle(x=400.0, y=300.0)
        landmark = make_landmark(x=0.5, y=0.5, name="nose")  # No es tocador
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[particle],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == [particle]
        assert hits == 0

    def test_no_landmarks_returns_all_particles(self) -> None:
        # Arrange
        p1 = make_particle(x=100.0, y=100.0)
        p2 = make_particle(x=400.0, y=300.0)
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[p1, p2],
            landmarks=[],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == [p1, p2]
        assert hits == 0

    def test_validates_screen_dimensions(self) -> None:
        # Arrange
        particle = make_particle(x=100.0, y=100.0)
        landmark = make_landmark(x=0.5, y=0.5)

        # Act & Assert
        with pytest.raises(ValueError, match="screen_width"):
            detect_collisions(
                particles=[particle],
                landmarks=[landmark],
                screen_width=0,
                screen_height=600,
                hit_radius=30.0,
            )

        with pytest.raises(ValueError, match="screen_height"):
            detect_collisions(
                particles=[particle],
                landmarks=[landmark],
                screen_width=800,
                screen_height=0,
                hit_radius=30.0,
            )

    def test_preserves_order_of_remaining_particles(self) -> None:
        # Arrange
        p1 = make_particle(x=100.0, y=100.0)
        p2 = make_particle(x=400.0, y=300.0)  # Será tocada
        p3 = make_particle(x=700.0, y=500.0)
        landmark = make_landmark(x=0.5, y=0.5)
        screen_width, screen_height = 800, 600

        # Act
        remaining, hits = detect_collisions(
            particles=[p1, p2, p3],
            landmarks=[landmark],
            screen_width=screen_width,
            screen_height=screen_height,
            hit_radius=30.0,
        )

        # Assert
        assert remaining == [p1, p3]  # Orden preservado
        assert hits == 1
