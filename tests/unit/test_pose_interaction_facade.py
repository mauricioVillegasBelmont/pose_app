"""
Tests unitarios para PoseInteractionFacade.
Validan el suavizado EMA y la lógica de colisión en el dominio puro.
"""

import pytest

from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.services.pose_interaction_facade import PoseInteractionFacade


class TestPoseInteractionFacadeInitialization:
    def test_initial_state_has_no_hand_positions(self) -> None:
        """Al iniciar, no hay manos rastreadas, debe retornar None."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)

        assert facade.get_hand_position("left", 800, 600) is None
        assert facade.get_hand_position("right", 800, 600) is None


class TestPoseInteractionFacadeSmoothing:
    def test_first_update_sets_position_directly_without_smoothing(self) -> None:
        """En el primer frame, no hay historial, por lo que la posición es la cruda."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)
        landmarks = [
            PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")
        ]

        facade.update(landmarks)
        pos = facade.get_hand_position("left", 800, 600)

        # 0.5 * 800 = 400, 0.5 * 600 = 300
        assert pos == (400.0, 300.0)

    def test_second_update_applies_ema_formula_correctly(self) -> None:
        """
        El segundo frame debe aplicar la fórmula EMA:
        nuevo = alpha * actual + (1 - alpha) * previo
        alpha = 0.3, previo = 0.5, actual = 0.7
        esperado = 0.3 * 0.7 + 0.7 * 0.5 = 0.21 + 0.35 = 0.56
        """
        facade = PoseInteractionFacade(smoothing_factor=0.3)

        # Frame 1
        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")]
        )

        # Frame 2: la mano se mueve a 0.7
        facade.update(
            [PoseLandmark(x=0.7, y=0.7, z=0.0, visibility=0.9, name="left_wrist")]
        )
        pos = facade.get_hand_position(
            "left", 100, 100
        )  # Usamos 100x100 para facilitar el cálculo mental

        # 0.56 * 100 = 56.0
        assert pos == pytest.approx((56.0, 56.0))

    def test_lost_hand_resets_smoothing_to_prevent_jumps(self) -> None:
        """Si la mano desaparece y reaparece, no debe 'teletransportarse' desde la posición antigua."""
        facade = PoseInteractionFacade(smoothing_factor=0.3)

        # Frame 1: Mano visible
        facade.update(
            [PoseLandmark(x=0.2, y=0.2, z=0.0, visibility=0.9, name="left_wrist")]
        )

        # Frame 2: Mano NO visible (visibility < 0.5)
        facade.update(
            [PoseLandmark(x=0.2, y=0.2, z=0.0, visibility=0.4, name="left_wrist")]
        )
        assert facade.get_hand_position("left", 800, 600) is None

        # Frame 3: Mano reaparece en una posición muy lejana (0.9)
        facade.update(
            [PoseLandmark(x=0.9, y=0.9, z=0.0, visibility=0.9, name="left_wrist")]
        )
        pos = facade.get_hand_position("left", 100, 100)

        # Debe ser la posición cruda nueva (0.9 * 100 = 90), no un promedio con la antigua (0.2)
        assert pos == pytest.approx((90.0, 90.0))


class TestPoseInteractionFacadeCollision:
    def test_is_touching_returns_true_when_within_radius(self) -> None:
        facade = PoseInteractionFacade(smoothing_factor=0.3)
        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")]
        )

        # La mano está en (400, 300) en pantalla de 800x600
        # Preguntamos si toca un círculo en (410, 300) con radio 20
        # Distancia = 10, que es <= 20
        is_touching = facade.is_touching(
            target_x=410.0, target_y=300.0, radius=20.0, screen_w=800, screen_h=600
        )

        assert is_touching is True

    def test_is_touching_returns_false_when_outside_radius(self) -> None:
        facade = PoseInteractionFacade(smoothing_factor=0.3)
        facade.update(
            [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=0.9, name="left_wrist")]
        )

        # La mano está en (400, 300).
        # Preguntamos si toca un círculo en (500, 300) con radio 20.
        # Distancia = 100, que es > 20
        is_touching = facade.is_touching(
            target_x=500.0, target_y=300.0, radius=20.0, screen_w=800, screen_h=600
        )

        assert is_touching is False
