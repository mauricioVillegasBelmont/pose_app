# tests/unit/test_mediapipe_adapter.py
import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from adapters.pose.mediapipe_adapter import MediapipeAdapter
from domain.entities.pose_landmark import PoseLandmark


class TestMediapipeAdapter(unittest.TestCase):

    def setUp(self):
        """Parchea mediapipe para no necesitar la librería real."""
        # Este parche debe ir ANTES de instanciar el adapter
        patcher = patch('adapters.pose.mediapipe_adapter.mp')
        self.mock_mp = patcher.start()
        self.addCleanup(patcher.stop)

        # Simula el objeto Pose de mediapipe
        self.mock_pose_instance = MagicMock()
        self.mock_mp.solutions.pose.Pose.return_value = self.mock_pose_instance

        self.adapter = MediapipeAdapter(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )

    def _make_fake_landmarks(self, n=33):
        """Crea landmarks falsos estilo mediapipe."""
        fake = []
        for i in range(n):
            lm = Mock()
            lm.x = 0.5
            lm.y = 0.5
            lm.z = 0.0
            lm.visibility = 0.9
            fake.append(lm)
        return fake

    def test_estimate_returns_pose_landmarks(self):
        """estimate() debe convertir la salida de mediapipe a PoseLandmark."""
        # Arrange
        fake_mp_landmarks = self._make_fake_landmarks(33)
        mock_results = Mock()
        mock_results.pose_landmarks = Mock()
        mock_results.pose_landmarks.landmark = fake_mp_landmarks
        self.mock_pose_instance.process.return_value = mock_results

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Act
        landmarks = self.adapter.estimate(frame)

        # Assert
        self.assertEqual(len(landmarks), 33)
        self.assertIsInstance(landmarks[0], PoseLandmark)
        self.assertAlmostEqual(landmarks[0].x, 0.5)
        self.assertAlmostEqual(landmarks[0].visibility, 0.9)

    def test_estimate_returns_empty_when_no_pose(self):
        """Si mediapipe no detecta pose, debe devolver lista vacía."""
        # Arrange
        mock_results = Mock()
        mock_results.pose_landmarks = None
        self.mock_pose_instance.process.return_value = mock_results

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Act
        landmarks = self.adapter.estimate(frame)

        # Assert
        self.assertEqual(landmarks, [])

    def test_draw_landmarks_returns_same_shape(self):
        """draw_landmarks no debe cambiar el shape del frame."""
        # Arrange
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = [
            PoseLandmark(0.5, 0.5, 0.0, 1.0, 'nose'),
        ]

        # Act
        result = self.adapter.draw_landmarks(frame, landmarks)

        # Assert
        self.assertEqual(result.shape, frame.shape)

    def test_close_releases_resources(self):
        """close() debe llamar a close() del objeto mediapipe."""
        # Act
        self.adapter.close()

        # Assert
        self.mock_pose_instance.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()