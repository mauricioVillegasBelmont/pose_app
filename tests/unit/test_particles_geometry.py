import random

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ==========================================
# detect_collisions
# ==========================================
from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.games.particles.geometry import (
    Workspace,
    detect_collisions,
)


def _make_particle(x: float, y: float) -> Particle:
    """Helper para crear partículas de prueba."""
    return Particle(x=x, y=y, vx=0.0, vy=0.0, size=20.0, life=1.0)


def _make_landmark(
    name: str, x: float, y: float, visibility: float = 1.0
) -> PoseLandmark:
    """Helper para crear landmarks de prueba."""
    return PoseLandmark(x=x, y=y, z=0.0, visibility=visibility, name=name)


# ==========================================
# Workspace: construcción
# ==========================================


class TestWorkspaceConstruction:
    """Tests de creación y validación del Workspace."""

    def test_default_workspace_is_valid(self) -> None:
        """El workspace por defecto es válido."""
        ws = Workspace()
        assert ws.x_min == 0.2
        assert ws.x_max == 0.8
        assert ws.y_min == 0.15
        assert ws.y_max == 0.85

    def test_workspace_is_frozen(self) -> None:
        """El workspace es inmutable."""
        from dataclasses import FrozenInstanceError

        ws = Workspace()
        with pytest.raises(FrozenInstanceError):
            ws.x_min = 0.5  # type: ignore[misc]

    def test_invalid_x_range_raises(self) -> None:
        """x_min >= x_max lanza ValueError."""
        with pytest.raises(ValueError, match="x_min/x_max"):
            Workspace(x_min=0.8, x_max=0.2)

    def test_invalid_y_range_raises(self) -> None:
        """y_min >= y_max lanza ValueError."""
        with pytest.raises(ValueError, match="y_min/y_max"):
            Workspace(y_min=0.9, y_max=0.1)

    def test_out_of_bounds_x_raises(self) -> None:
        """x fuera de [0, 1] lanza ValueError."""
        with pytest.raises(ValueError):
            Workspace(x_min=-0.1, x_max=0.5)

    def test_out_of_bounds_y_raises(self) -> None:
        """y fuera de [0, 1] lanza ValueError."""
        with pytest.raises(ValueError):
            Workspace(y_min=0.0, y_max=1.5)


# ==========================================
# Workspace: random_point
# ==========================================


class TestWorkspaceRandomPoint:
    """Tests de generación aleatoria de puntos."""

    def test_random_point_within_workspace(self) -> None:
        """Los puntos siempre caen dentro del workspace."""
        ws = Workspace()
        rng = random.Random(42)
        for _ in range(100):
            x, y = ws.random_point(rng)
            assert ws.x_min <= x <= ws.x_max
            assert ws.y_min <= y <= ws.y_max

    def test_random_point_deterministic_with_seed(self) -> None:
        """Con la misma seed, los puntos son idénticos."""
        ws = Workspace()
        rng1 = random.Random(42)
        rng2 = random.Random(42)

        points1 = [ws.random_point(rng1) for _ in range(10)]
        points2 = [ws.random_point(rng2) for _ in range(10)]

        assert points1 == points2

    def test_random_point_varies_without_seed(self) -> None:
        """Sin seed, los puntos varían (no son siempre iguales)."""
        ws = Workspace()
        rng1 = random.Random()
        rng2 = random.Random()

        # Con altísima probabilidad, dos secuencias son distintas.
        # Verificamos que al menos uno de los puntos difiere.
        points1 = [ws.random_point(rng1) for _ in range(10)]
        points2 = [ws.random_point(rng2) for _ in range(10)]

        assert points1 != points2


# ==========================================
# Workspace: contains
# ==========================================


class TestWorkspaceContains:
    """Tests de verificación de pertenencia."""

    def test_center_is_inside(self) -> None:
        """El centro (0.5, 0.5) está dentro."""
        ws = Workspace()
        assert ws.contains(0.5, 0.5) is True

    def test_corners_are_inside(self) -> None:
        """Los bordes del workspace están dentro (inclusive)."""
        ws = Workspace()
        assert ws.contains(ws.x_min, ws.y_min) is True
        assert ws.contains(ws.x_max, ws.y_max) is True
        assert ws.contains(ws.x_min, ws.y_max) is True
        assert ws.contains(ws.x_max, ws.y_min) is True

    def test_outside_bounds(self) -> None:
        """Puntos fuera del rango lanzan False."""
        ws = Workspace()
        assert ws.contains(0.0, 0.5) is False
        assert ws.contains(1.0, 0.5) is False
        assert ws.contains(0.5, 0.0) is False
        assert ws.contains(0.5, 1.0) is False

    def test_far_outside(self) -> None:
        """Puntos muy fuera también son False."""
        ws = Workspace()
        assert ws.contains(-1.0, -1.0) is False
        assert ws.contains(2.0, 2.0) is False


# ==========================================
# Workspace: property-based tests
# ==========================================


class TestWorkspaceProperties:
    """Property-based tests del Workspace."""

    @given(
        x_min=st.floats(min_value=0.0, max_value=0.4, allow_nan=False),
        width=st.floats(min_value=0.1, max_value=0.5, allow_nan=False),
        y_min=st.floats(min_value=0.0, max_value=0.4, allow_nan=False),
        height=st.floats(min_value=0.1, max_value=0.5, allow_nan=False),
    )
    def test_valid_ranges_always_accepted(
        self, x_min: float, width: float, y_min: float, height: float
    ) -> None:
        """Cualquier rango válido se acepta sin error."""
        ws = Workspace(
            x_min=x_min,
            x_max=x_min + width,
            y_min=y_min,
            y_max=y_min + height,
        )
        assert ws.x_min == x_min
        assert ws.y_min == y_min

    @given(
        x_min=st.floats(min_value=0.0, max_value=0.9, allow_nan=False),
        x_max=st.floats(min_value=0.0, max_value=0.9, allow_nan=False),
    )
    def test_random_point_always_inside(self, x_min: float, x_max: float) -> None:
        """El punto siempre cae dentro (con rangos válidos)."""
        # Ignora el caso inválido (x_min >= x_max)
        if x_min >= x_max:
            return
        ws = Workspace(x_min=x_min, x_max=x_max)
        rng = random.Random(42)
        x, y = ws.random_point(rng)
        assert ws.contains(x, y)


class TestDetectCollisionsBehavior:
    """Tests del comportamiento de colisiones."""

    def test_no_hands_no_collisions(self) -> None:
        """Sin landmarks, ninguna partícula colisiona."""
        particles = [_make_particle(400, 300)]
        remaining, hits = detect_collisions(
            particles=particles,
            landmarks=[],
            screen_width=800,
            screen_height=600,
        )
        assert hits == 0
        assert remaining == particles

    def test_landmark_not_hand_ignored(self) -> None:
        """Un landmark que no es mano (ej: nariz) no causa colisión."""
        particles = [_make_particle(400, 300)]
        # Nariz en el centro (donde está la partícula)
        landmarks = [_make_landmark("nose", 0.5, 0.5)]

        remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
        )
        assert hits == 0
        assert remaining == particles

    def test_invisible_hand_ignored(self) -> None:
        """Landmark de mano no visible no causa colisión."""
        particles = [_make_particle(400, 300)]
        landmarks = [_make_landmark("left_wrist", 0.5, 0.5, visibility=0.3)]

        _remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
        )
        assert hits == 0

    def test_hand_directly_on_particle_hits(self) -> None:
        """Mano exactamente sobre partícula → colisión."""
        particles = [_make_particle(400, 300)]
        # Mano en (0.5, 0.5) → (400, 300) píxeles
        landmarks = [_make_landmark("left_wrist", 0.5, 0.5)]

        remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
            hit_radius=30.0,
        )
        assert hits == 1
        assert remaining == []

    def test_hand_within_radius_hits(self) -> None:
        """Mano a menos de hit_radius → colisión."""
        particles = [_make_particle(400, 300)]
        # Mano a 20 px de distancia (dentro de 30)
        landmarks = [_make_landmark("left_wrist", 420 / 800, 300 / 600)]

        _remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
            hit_radius=30.0,
        )
        assert hits == 1

    def test_hand_outside_radius_no_hit(self) -> None:
        """Mano a más de hit_radius → no colisión."""
        particles = [_make_particle(400, 300)]
        # Mano a 50 px de distancia (fuera de 30)
        landmarks = [_make_landmark("left_wrist", 450 / 800, 300 / 600)]

        remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
            hit_radius=30.0,
        )
        assert hits == 0
        assert remaining == particles

    def test_multiple_particles_one_hand(self) -> None:
        """Una mano puede tocar varias partículas."""
        particles = [
            _make_particle(400, 300),
            _make_particle(410, 305),  # cerca de la mano
            _make_particle(700, 500),  # lejos
        ]
        landmarks = [_make_landmark("left_wrist", 0.5, 0.5)]

        remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
            hit_radius=30.0,
        )
        assert hits == 2
        assert len(remaining) == 1
        assert remaining[0].x == 700

    def test_multiple_hands_one_particle_counts_once(self) -> None:
        """Si 2 manos tocan la misma partícula, cuenta 1 vez."""
        particles = [_make_particle(400, 300)]
        landmarks = [
            _make_landmark("left_wrist", 0.5, 0.5),
            _make_landmark("right_wrist", 0.51, 0.5),
        ]

        _remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
            hit_radius=30.0,
        )
        assert hits == 1

    def test_all_hand_landmarks_work(self) -> None:
        """Los 4 landmarks de manos funcionan."""
        for name in ["left_wrist", "right_wrist", "left_index", "right_index"]:
            particles = [_make_particle(400, 300)]
            landmarks = [_make_landmark(name, 0.5, 0.5)]

            _, hits = detect_collisions(
                particles=particles,
                landmarks=landmarks,
                screen_width=800,
                screen_height=600,
            )
            assert hits == 1, f"Fallo con landmark: {name}"

    def test_preserves_remaining_order(self) -> None:
        """El orden de las partículas no tocadas se preserva."""
        p1 = _make_particle(100, 100)
        p2 = _make_particle(400, 300)  # será tocada
        p3 = _make_particle(700, 500)
        particles = [p1, p2, p3]
        landmarks = [_make_landmark("left_wrist", 0.5, 0.5)]

        remaining, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
        )
        assert hits == 1
        assert remaining == [p1, p3]


class TestDetectCollisionsProperties:
    """Property-based tests."""

    @given(
        px=st.floats(min_value=0, max_value=800, allow_nan=False),
        py=st.floats(min_value=0, max_value=600, allow_nan=False),
    )
    def test_particle_on_hand_always_hits(self, px: float, py: float) -> None:
        """Si la mano está exactamente sobre la partícula, siempre colisiona."""
        particles = [_make_particle(px, py)]
        # Convertir píxeles a normalizado
        landmarks = [_make_landmark("left_wrist", px / 800, py / 600)]

        _, hits = detect_collisions(
            particles=particles,
            landmarks=landmarks,
            screen_width=800,
            screen_height=600,
            hit_radius=10.0,
        )
        assert hits == 1

    @given(n_particles=st.integers(min_value=0, max_value=10))
    def test_no_hands_preserves_all(self, n_particles: int) -> None:
        """Sin manos, todas las partículas quedan."""
        particles = [_make_particle(i * 50, i * 50) for i in range(n_particles)]
        remaining, hits = detect_collisions(
            particles=particles,
            landmarks=[],
            screen_width=800,
            screen_height=600,
        )
        assert hits == 0
        assert len(remaining) == n_particles
