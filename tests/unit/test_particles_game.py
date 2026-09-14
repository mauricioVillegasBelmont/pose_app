import unittest
from unittest.mock import Mock

import numpy as np

from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.use_cases.particles_game import ParticlesGame


class TestParticlesGame(unittest.TestCase):

    def test_particle_spawning(self):
        """Verifica que se generen partículas desde landmarks visibles."""
        # Arrange
        mock_camera = Mock()
        mock_camera.get_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

        mock_pose = Mock()
        mock_pose.estimate.return_value = [
            PoseLandmark(0.5, 0.5, 0.0, 1.0, 'nose'),  # Visible
            PoseLandmark(0.3, 0.3, 0.0, 0.0, 'left_shoulder'),  # No visible
        ]

        mock_render = Mock()

        game = ParticlesGame(mock_camera, mock_pose, mock_render)

        # Act
        game._spawn_particles_from_landmarks(mock_pose.estimate.return_value)

        # Assert
        assert len(game._particles) > 0
        # Solo debe generar partículas del landmark visible (nose)
        assert len(game._particles) == 5  # 5 partículas por landmark visible

    def test_particle_update_and_death(self):
        """Verifica que las partículas se actualicen y mueran correctamente."""
        # Arrange
        game = ParticlesGame(Mock(), Mock(), Mock())

        # Crea partículas con vida baja
        particle1 = Particle(0, 0, life=0.5)
        particle2 = Particle(0, 0, life=0.005)  # Casi muerta
        game._particles = [particle1, particle2]

        # Act
        game._update_particles()

        # Assert
        assert particle1 in game._particles  # Sigue viva
        assert particle2 not in game._particles  # Murió

    def test_reset_clears_particles(self):
        """Verifica que reset limpie todas las partículas."""
        # Arrange
        game = ParticlesGame(Mock(), Mock(), Mock())
        game._particles = [Particle(0, 0), Particle(1, 1)]

        # Act
        game.reset()

        # Assert
        assert len(game._particles) == 0