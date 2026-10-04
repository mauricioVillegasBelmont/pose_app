"""
Tests unitarios de ParticlesGame (lógica pura).

Estos tests NO inicializan adaptadores reales.
"""

from unittest.mock import Mock

import pytest

from domain.entities.pose_landmark import PoseLandmark
from domain.games.particles.main import ParticlesGame
from domain.games.particles.state import ParticlesState
from infrastructure.events.async_event_bus import AsyncEventBus


@pytest.fixture
def game() -> ParticlesGame:
    """Game con mocks y estado real (para probar la lógica)."""
    return ParticlesGame(
        camera=Mock(),
        pose_estimator=Mock(),
        renderer=Mock(),
        state=ParticlesState(),
        event_bus=AsyncEventBus(),
    )


class TestParticlesGame:
    def test_particle_spawning(self, game: ParticlesGame):
        """Verifica que se generen partículas desde landmarks visibles."""
        landmarks = [
            PoseLandmark(0.5, 0.5, 0.0, 1.0, "nose"),  # Visible
            PoseLandmark(0.3, 0.3, 0.0, 0.0, "left_shoulder"),  # No visible
        ]

        game._spawn_particles_from_landmarks(landmarks)

        assert len(game._particles) > 0
        # Solo debe generar partículas del landmark visible
        assert len(game._particles) == 5  # burst_count default

    def test_particle_update_and_death(self, game: ParticlesGame):
        """Verifica que las partículas se actualicen y mueran."""
        from domain.entities.particle import Particle

        particle1 = Particle(0, 0, life=0.5)
        particle2 = Particle(0, 0, life=0.005)  # Casi muerta
        game._particles = [particle1, particle2]

        game._update_particles()

        assert particle1 in game._particles
        assert particle2 not in game._particles

    def test_reset_clears_particles(self, game: ParticlesGame):
        """Verifica que reset limpie todas las partículas."""
        from domain.entities.particle import Particle

        game._particles = [Particle(0, 0), Particle(1, 1)]

        game.reset()

        assert len(game._particles) == 0
