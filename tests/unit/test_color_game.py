import unittest
from unittest.mock import Mock

from domain.entities.pose_landmark import PoseLandmark
from domain.use_cases.color_game import ColorGame


class TestColorGame(unittest.TestCase):

    def test_color_calculation_with_hands_up(self):
        """Verifica que manos arriba generen colores cálidos."""
        # Arrange
        game = ColorGame(Mock(), Mock(), Mock(), palette_name='fire')

        # Manos arriba (y bajo)
        landmarks = [
            PoseLandmark(0.2, 0.2, 0.0, 1.0, 'left_wrist'),
            PoseLandmark(0.8, 0.2, 0.0, 1.0, 'right_wrist'),
            PoseLandmark(0.5, 0.3, 0.0, 1.0, 'nose'),
        ]

        # Act
        color = game._calculate_color_from_pose(landmarks)

        # Assert: debería ser predominantemente rojo o azul
        assert color.r > 100 or color.g > 100
        assert color.b < 150  # Menos azul

    def test_color_calculation_with_hands_down(self):
        """Verifica que manos abajo generen colores fríos."""
        # Arrange
        game = ColorGame(Mock(), Mock(), Mock(), palette_name='ocean')

        # Manos abajo (y alto)
        landmarks = [
            PoseLandmark(0.2, 0.9, 0.0, 1.0, 'left_wrist'),
            PoseLandmark(0.8, 0.9, 0.0, 1.0, 'right_wrist'),
            PoseLandmark(0.5, 0.6, 0.0, 1.0, 'nose'),
        ]

        # Act
        color = game._calculate_color_from_pose(landmarks)

        # Assert: debería tener menos rojo/azul intenso
        # (depende de la paleta ocean)
        assert color.b > 100