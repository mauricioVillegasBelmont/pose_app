# tests/unit/test_particles_game_integration.py
import unittest
from unittest.mock import Mock

import numpy as np

from domain.entities.pose_landmark import PoseLandmark
from domain.use_cases.particles_game import ParticlesGame


class TestParticlesGameRunLoop(unittest.TestCase):

    def setUp(self):
        self.mock_camera = Mock()
        self.mock_pose = Mock()
        self.mock_render = Mock()

        # Frame falso
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Simula que la cámara está activa 3 iteraciones, luego se detiene
        self.mock_camera.is_running.side_effect = [True, True, True, False]
        self.mock_camera.get_frame.return_value = self.frame

        # Pose fija
        self.mock_pose.estimate.return_value = [
            PoseLandmark(0.5, 0.5, 0.0, 1.0, 'nose'),
        ]

        self.game = ParticlesGame(
            self.mock_camera, self.mock_pose, self.mock_render
        )

    def test_run_calls_dependencies(self):
        """run() debe usar cámara, estimador y renderer."""
        # Act
        self.game.run()

        # Assert
        self.mock_camera.start.assert_called_once()
        self.mock_camera.stop.assert_called_once()
        self.mock_render.close.assert_called_once()

        # Se llamó get_frame 3 veces (una por iteración)
        self.assertEqual(self.mock_camera.get_frame.call_count, 3)

        # Se estimó pose 3 veces
        self.assertEqual(self.mock_pose.estimate.call_count, 3)

        # Se renderizó 3 veces
        self.assertEqual(self.mock_render.render_particles.call_count, 3)

    def test_run_generates_particles(self):
        """run() debe acumular partículas de cada frame."""
        # Act
        self.game.run()

        # Assert: 5 partículas por frame × 3 frames = 15
        # (asumiendo que ninguna murió)
        self.assertGreater(len(self.game._particles), 0)

    def test_run_stops_on_keyboard_interrupt(self):
        """run() debe detener limpiamente ante KeyboardInterrupt."""
        # Arrange: la cámara lanza KeyboardInterrupt en la 2da iteración
        self.mock_camera.is_running.side_effect = [True, True, KeyboardInterrupt]

        # Act / Assert: no debe propagar la excepción
        try:
            self.game.run()
        except KeyboardInterrupt:
            self.fail("run() no debe propagar KeyboardInterrupt")

        # Assert: cleanup ejecutado
        self.mock_camera.stop.assert_called_once()
        self.mock_render.close.assert_called_once()

    def test_run_skips_none_frames(self):
        """run() debe ignorar frames None y seguir el loop."""
        # Arrange: primer frame None, luego válido, luego None
        self.mock_camera.is_running.side_effect = [True, True, True, False]
        self.mock_camera.get_frame.side_effect = [None, self.frame, None]

        # Act
        self.game.run()

        # Assert: solo se estimó pose 1 vez (el frame válido)
        self.assertEqual(self.mock_pose.estimate.call_count, 1)


if __name__ == "__main__":
    unittest.main()