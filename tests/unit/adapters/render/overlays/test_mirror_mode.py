"""
Tests de mirror mode.
"""

from unittest.mock import Mock

import pytest

from pose_app.adapters.render.overlays.pose_overlay import PoseOverlay
from pose_app.domain.entities.pose_landmark import PoseLandmark


class TestPoseOverlayMirror:
    def test_mirror_false_no_transforms(self) -> None:
        """Con mirror=False, los landmarks se pasan tal cual."""
        overlay = PoseOverlay(mirror=False)
        landmarks = [
            PoseLandmark(x=0.3, y=0.5, z=0.0, visibility=1.0, name="nose"),
        ]

        overlay._renderer = Mock()
        surface = Mock()
        surface.get_size.return_value = (800, 600)

        overlay.draw(surface, landmarks)

        called_landmarks = overlay._renderer.draw.call_args[0][1]
        assert called_landmarks[0].x == pytest.approx(0.3)

    def test_mirror_true_transforms(self) -> None:
        """Con mirror=True, x se invierte (1 - x)."""
        overlay = PoseOverlay(mirror=True)
        landmarks = [
            PoseLandmark(x=0.3, y=0.5, z=0.0, visibility=1.0, name="nose"),
            PoseLandmark(x=0.7, y=0.5, z=0.0, visibility=1.0, name="left_wrist"),
        ]

        overlay._renderer = Mock()
        surface = Mock()
        surface.get_size.return_value = (800, 600)

        overlay.draw(surface, landmarks)

        called_landmarks = overlay._renderer.draw.call_args[0][1]
        assert called_landmarks[0].x == pytest.approx(0.7)
        assert called_landmarks[1].x == pytest.approx(0.3)

        # Originales no mutados
        assert landmarks[0].x == pytest.approx(0.3)
        assert landmarks[1].x == pytest.approx(0.7)

    def test_mirror_with_empty_landmarks(self) -> None:
        """Con landmarks vacíos, no hace nada."""
        overlay = PoseOverlay(mirror=True)
        overlay._renderer = Mock()
        surface = Mock()

        overlay.draw(surface, None)
        overlay.draw(surface, [])

        overlay._renderer.draw.assert_not_called()

    def test_mirror_preserves_other_fields(self) -> None:
        """Mirror preserva y, z, visibility, name."""
        overlay = PoseOverlay(mirror=True)
        landmarks = [
            PoseLandmark(
                x=0.3,
                y=0.42,
                z=-0.5,
                visibility=0.87,
                name="nose",
            ),
        ]

        mirrored = overlay._mirror_landmarks(landmarks)

        assert mirrored[0].x == pytest.approx(0.7)
        assert mirrored[0].y == 0.42
        assert mirrored[0].z == -0.5
        assert mirrored[0].visibility == 0.87
        assert mirrored[0].name == "nose"
