"""
Tests unitarios para HandLandmarkConfig.
Validan la creación, validación e inmutabilidad de la configuración.
"""

import pytest

from pose_app.domain.entities.hand_landmark_config import HandLandmarkConfig


class TestHandLandmarkConfig:
    def test_creation_with_valid_landmarks(self) -> None:
        """HandLandmarkConfig con landmarks válidos."""
        config = HandLandmarkConfig(
            landmark_names=("left_wrist", "left_index", "left_pinky", "left_thumb")
        )

        assert config.landmark_names == (
            "left_wrist",
            "left_index",
            "left_pinky",
            "left_thumb",
        )
        assert config.offset_x == 0.0
        assert config.offset_y == 0.0

    def test_creation_with_custom_offsets(self) -> None:
        """HandLandmarkConfig con offsets personalizados."""
        config = HandLandmarkConfig(
            landmark_names=("right_wrist",),
            offset_x=0.05,
            offset_y=-0.03,
        )

        assert config.landmark_names == ("right_wrist",)
        assert config.offset_x == 0.05
        assert config.offset_y == -0.03

    def test_rejects_empty_landmark_names(self) -> None:
        """Debe rechazar una lista vacía de landmarks."""
        with pytest.raises(ValueError, match="landmark_names must not be empty"):
            HandLandmarkConfig(landmark_names=())

    def test_rejects_offset_x_out_of_range(self) -> None:
        """Debe rechazar offset_x fuera del rango [-1.0, 1.0]."""
        with pytest.raises(ValueError, match="offset_x must be in range"):
            HandLandmarkConfig(landmark_names=("left_wrist",), offset_x=1.5)

        with pytest.raises(ValueError, match="offset_x must be in range"):
            HandLandmarkConfig(landmark_names=("left_wrist",), offset_x=-1.5)

    def test_rejects_offset_y_out_of_range(self) -> None:
        """Debe rechazar offset_y fuera del rango [-1.0, 1.0]."""
        with pytest.raises(ValueError, match="offset_y must be in range"):
            HandLandmarkConfig(landmark_names=("left_wrist",), offset_y=2.0)

        with pytest.raises(ValueError, match="offset_y must be in range"):
            HandLandmarkConfig(landmark_names=("left_wrist",), offset_y=-2.0)

    def test_is_immutable(self) -> None:
        """HandLandmarkConfig es inmutable (frozen)."""
        config = HandLandmarkConfig(landmark_names=("left_wrist",))

        with pytest.raises(AttributeError):
            config.landmark_names = ("right_wrist",)  # type: ignore

        with pytest.raises(AttributeError):
            config.offset_x = 0.1  # type: ignore

    def test_accepts_boundary_offsets(self) -> None:
        """Debe aceptar offsets en los límites del rango."""
        config = HandLandmarkConfig(
            landmark_names=("left_wrist",),
            offset_x=-1.0,
            offset_y=1.0,
        )

        assert config.offset_x == -1.0
        assert config.offset_y == 1.0
