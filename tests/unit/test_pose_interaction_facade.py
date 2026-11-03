"""
Tests unitarios para PoseInteractionFacade.
Validan el suavizado EMA, gestión de múltiples cursores y timeout.
"""

import pytest

from pose_app.domain.entities.hand_landmark_config import HandLandmarkConfig
from pose_app.domain.entities.input_cursor import CursorCollision
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.services.pose_interaction_facade import PoseInteractionFacade


class TestPoseInteractionFacadeInitialization:
    def test_initial_state_has_no_visible_cursors(self) -> None:
        """Al iniciar, ningún cursor está visible."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)

        assert facade.get_hand_position("left", 800, 600) is None
        assert facade.get_hand_position("right", 800, 600) is None

    def test_default_cursor_configs(self) -> None:
        """Por defecto, se crean cursores para left_hand y right_hand."""
        facade = PoseInteractionFacade()

        cursors = facade.get_all_cursors()
        assert len(cursors) == 2
        assert any(c.cursor_id == "left_hand" for c in cursors)
        assert any(c.cursor_id == "right_hand" for c in cursors)

    def test_custom_cursor_configs(self) -> None:
        """Se pueden configurar cursores personalizados."""
        configs = {
            "left_hand": HandLandmarkConfig(
                landmark_names=("left_wrist", "left_index"),
                offset_x=0.02,
            ),
            "feet": HandLandmarkConfig(
                landmark_names=("left_ankle", "right_ankle"),
            ),
        }
        facade = PoseInteractionFacade(cursor_configs=configs)

        cursors = facade.get_all_cursors()
        assert len(cursors) == 2
        assert any(c.cursor_id == "left_hand" for c in cursors)
        assert any(c.cursor_id == "feet" for c in cursors)


class TestPoseInteractionFacadeSmoothing:
    def test_first_update_sets_position_directly(self) -> None:
        """En el primer frame, la posición es la cruda (sin historial)."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)
        landmarks = [
            PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")
        ]

        facade.update(landmarks, current_time=1.0)
        pos = facade.get_hand_position("left", 800, 600)

        assert pos == (400.0, 300.0)

    def test_second_update_applies_ema(self) -> None:
        """El segundo frame aplica EMA."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)

        # Frame 1
        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")],
            current_time=1.0,
        )

        # Frame 2: mano se mueve a 0.7
        facade.update(
            [PoseLandmark(x=0.7, y=0.7, z=0.0, visibility=0.9, name="left_wrist")],
            current_time=2.0,
        )

        pos = facade.get_hand_position("left", 100, 100)

        # EMA: 0.3 * 0.7 + 0.7 * 0.5 = 0.56
        assert pos == pytest.approx((56.0, 56.0))

    def test_lost_hand_persists_before_timeout(self) -> None:
        """Si la mano desaparece pero no ha pasado el timeout, mantiene posición."""
        facade = PoseInteractionFacade(smoothing_factor=0.3, hand_timeout=2.0)

        # Frame 1: mano visible
        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")],
            current_time=1.0,
        )

        # Frame 2: mano NO visible, pero dentro del timeout (1s < 2s)
        facade.update([], current_time=2.0)

        pos = facade.get_hand_position("left", 800, 600)

        # Debe mantener la última posición
        assert pos == (400.0, 300.0)

    def test_lost_hand_disappears_after_timeout(self) -> None:
        """Si la mano desaparece y pasa el timeout, se marca como invisible."""
        facade = PoseInteractionFacade(smoothing_factor=0.3, hand_timeout=2.0)

        # Frame 1: mano visible
        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")],
            current_time=1.0,
        )

        # Frame 2: mano NO visible, después del timeout (4s > 2s)
        facade.update([], current_time=4.0)

        pos = facade.get_hand_position("left", 800, 600)

        # Debe retornar None (cursor perdido)
        assert pos is None


class TestPoseInteractionFacadeCollision:
    def test_is_touching_uses_cursor_radius(self) -> None:
        """is_touching debe usar el radio del cursor, no un radio fijo."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)

        # Configurar cursor con radio grande
        cursor = facade.get_cursor("left_hand")
        assert cursor is not None
        cursor.collision = CursorCollision(radius=20.0)  # 20% del mínimo

        # Mano en (400, 300) en pantalla 800x600
        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")],
            current_time=1.0,
        )

        # Objetivo en (450, 300) con radio 10
        # Distancia = 50, radio cursor = 20% * 600 = 120, radio objetivo = 10
        # 50 <= 120 + 10 = 130 → True
        is_touching = facade.is_touching(
            target_x=450.0,
            target_y=300.0,
            radius=10.0,
            screen_w=800,
            screen_h=600,
            cursor_id="left_hand",
        )

        assert is_touching is True

    def test_is_touching_returns_false_when_outside(self) -> None:
        """is_touching retorna False cuando está fuera del radio."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)

        cursor = facade.get_cursor("left_hand")
        assert cursor is not None
        cursor.collision = CursorCollision(radius=5.0)  # 5% del mínimo

        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")],
            current_time=1.0,
        )

        # Objetivo muy lejos
        is_touching = facade.is_touching(
            target_x=450.0,
            target_y=300.0,
            radius=10.0,
            screen_w=800,
            screen_h=600,
            cursor_id="left_hand",
        )

        assert is_touching is False

    def test_is_touching_returns_false_when_cursor_not_visible(self) -> None:
        """is_touching retorna False si el cursor no está visible."""
        facade = PoseInteractionFacade(smoothing_factor=0.3, hand_timeout=1.0)

        # No hay landmarks, cursor no visible
        facade.update([], current_time=5.0)

        is_touching = facade.is_touching(
            target_x=450.0,
            target_y=300.0,
            radius=10.0,
            screen_w=800,
            screen_h=600,
            cursor_id="left_hand",
        )

        assert is_touching is False


class TestPoseInteractionFacadeMultipleCursors:
    def test_multiple_cursors_independent(self) -> None:
        """Múltiples cursores son independientes."""
        configs = {
            "left_hand": HandLandmarkConfig(landmark_names=("left_wrist",)),
            "right_hand": HandLandmarkConfig(landmark_names=("right_wrist",)),
        }
        facade = PoseInteractionFacade(cursor_configs=configs)

        landmarks = [
            PoseLandmark(x=0.3, y=0.5, z=0.0, visibility=0.9, name="left_wrist"),
            PoseLandmark(x=0.7, y=0.5, z=0.0, visibility=0.9, name="right_wrist"),
        ]

        facade.update(landmarks, current_time=1.0)

        left_pos = facade.get_hand_position("left", 800, 600)
        right_pos = facade.get_hand_position("right", 800, 600)

        assert left_pos == (240.0, 300.0)
        assert right_pos == (560.0, 300.0)

    def test_get_cursor_returns_specific_cursor(self) -> None:
        """get_cursor retorna un cursor específico."""
        facade = PoseInteractionFacade()

        cursor = facade.get_cursor("left_hand")

        assert cursor is not None
        assert cursor.cursor_id == "left_hand"

    def test_get_cursor_returns_none_for_unknown(self) -> None:
        """get_cursor retorna None para cursor desconocido."""
        facade = PoseInteractionFacade()

        cursor = facade.get_cursor("unknown_cursor")

        assert cursor is None
