"""
Tests unitarios para CollisionHandler.
Validan el cálculo del centroide y la aplicación de offset.
"""

import pytest

from pose_app.domain.entities.hand_landmark_config import HandLandmarkConfig
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.services.collision_handler import CentroidCollisionHandler


class TestCentroidCollisionHandler:
    def test_calculates_centroid_of_single_landmark(self) -> None:
        """Con un solo landmark visible, retorna ese punto."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(landmark_names=("left_wrist",))
        landmarks = [
            PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist"),
        ]

        result = handler.calculate_point(landmarks, config)

        assert result == (0.5, 0.5)

    def test_calculates_centroid_of_multiple_landmarks(self) -> None:
        """Con múltiples landmarks visibles, retorna el promedio."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(
            landmark_names=("left_wrist", "left_index", "left_pinky")
        )
        landmarks = [
            PoseLandmark(x=0.4, y=0.5, z=0.0, visibility=0.9, name="left_wrist"),
            PoseLandmark(x=0.5, y=0.4, z=0.0, visibility=0.9, name="left_index"),
            PoseLandmark(x=0.6, y=0.5, z=0.0, visibility=0.9, name="left_pinky"),
        ]

        result = handler.calculate_point(landmarks, config)

        # Promedio: x=(0.4+0.5+0.6)/3=0.5, y=(0.5+0.4+0.5)/3=0.4666...
        assert result is not None
        assert result[0] == pytest.approx(0.5)
        assert result[1] == pytest.approx(0.4666666666666667)

    def test_applies_offset(self) -> None:
        """Debe aplicar el offset configurado al centroide."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(
            landmark_names=("left_wrist",),
            offset_x=0.05,
            offset_y=-0.03,
        )
        landmarks = [
            PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist"),
        ]

        result = handler.calculate_point(landmarks, config)

        assert result == (0.55, 0.47)

    def test_ignores_invisible_landmarks(self) -> None:
        """Debe ignorar landmarks con visibility < 0.5."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(landmark_names=("left_wrist", "left_index"))
        landmarks = [
            PoseLandmark(x=0.4, y=0.5, z=0.0, visibility=0.9, name="left_wrist"),
            PoseLandmark(
                x=0.6, y=0.5, z=0.0, visibility=0.3, name="left_index"
            ),  # Invisible
        ]

        result = handler.calculate_point(landmarks, config)

        # Solo left_wrist es visible, así que el centroide es (0.4, 0.5)
        assert result == (0.4, 0.5)

    def test_returns_none_when_no_visible_landmarks(self) -> None:
        """Debe retornar None si no hay landmarks visibles."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(landmark_names=("left_wrist",))
        landmarks = [
            PoseLandmark(
                x=0.5, y=0.5, z=0.0, visibility=0.3, name="left_wrist"
            ),  # Invisible
        ]

        result = handler.calculate_point(landmarks, config)

        assert result is None

    def test_returns_none_when_no_configured_landmarks(self) -> None:
        """Debe retornar None si no hay landmarks configurados en la lista."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(landmark_names=("left_wrist",))
        landmarks = [
            PoseLandmark(
                x=0.5, y=0.5, z=0.0, visibility=0.9, name="right_wrist"
            ),  # No configurado
        ]

        result = handler.calculate_point(landmarks, config)

        assert result is None

    def test_ignores_unconfigured_landmarks(self) -> None:
        """Debe ignorar landmarks que no están en la configuración."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(landmark_names=("left_wrist",))
        landmarks = [
            PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist"),
            PoseLandmark(
                x=0.8, y=0.8, z=0.0, visibility=0.9, name="right_wrist"
            ),  # No configurado
        ]

        result = handler.calculate_point(landmarks, config)

        # Solo left_wrist cuenta
        assert result == (0.5, 0.5)

    def test_handles_empty_landmarks_list(self) -> None:
        """Debe retornar None si la lista de landmarks está vacía."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(landmark_names=("left_wrist",))

        result = handler.calculate_point([], config)

        assert result is None

    def test_mixed_visible_and_invisible(self) -> None:
        """Debe promediar solo los landmarks visibles."""
        handler = CentroidCollisionHandler()
        config = HandLandmarkConfig(
            landmark_names=("left_wrist", "left_index", "left_pinky", "left_thumb")
        )
        landmarks = [
            PoseLandmark(x=0.4, y=0.5, z=0.0, visibility=0.9, name="left_wrist"),
            PoseLandmark(x=0.5, y=0.4, z=0.0, visibility=0.9, name="left_index"),
            PoseLandmark(
                x=0.6, y=0.5, z=0.0, visibility=0.3, name="left_pinky"
            ),  # Invisible
            PoseLandmark(x=0.5, y=0.6, z=0.0, visibility=0.9, name="left_thumb"),
        ]

        result = handler.calculate_point(landmarks, config)

        # Solo 3 visibles: wrist, index, thumb
        # x=(0.4+0.5+0.5)/3=0.4666..., y=(0.5+0.4+0.6)/3=0.5
        assert result is not None
        assert result[0] == pytest.approx(0.4666666666666667)
        assert result[1] == pytest.approx(0.5)
