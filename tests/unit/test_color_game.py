# tests/unit/test_color_game.py

from unittest.mock import Mock

import pytest

from domain.entities.color import RGBColor
from domain.entities.pose_landmark import PoseLandmark
from domain.games.color.main import ColorGame
from domain.games.color.state import ColorState


@pytest.fixture
def color_game() -> ColorGame:
    """Instancia sin adaptadores reales (para probar lógica pura)."""
    return ColorGame(
        camera=Mock(),
        pose_estimator=Mock(),
        renderer=Mock(),
        state=ColorState(palette_name="fire"),
        event_bus=Mock(),
        palette_name="fire",
    )


def test_color_calculation_with_hands_up(color_game: ColorGame):
    """Manos arriba → colores cálidos (componente rojo dominante)."""
    landmarks = [
        PoseLandmark(x=0.2, y=0.2, z=0.0, visibility=1.0, name="left_wrist"),
        PoseLandmark(x=0.8, y=0.2, z=0.0, visibility=1.0, name="right_wrist"),
        PoseLandmark(x=0.5, y=0.3, z=0.0, visibility=1.0, name="nose"),
    ]
    color = color_game._calculate_color(landmarks)

    # Un color cálido tiene el rojo como componente dominante
    assert color.r > color.g
    assert color.r > color.b


def test_color_calculation_with_hands_down(color_game: ColorGame):
    """Manos abajo → colores fríos."""
    landmarks = [
        PoseLandmark(x=0.2, y=0.9, z=0.0, visibility=1.0, name="left_wrist"),
        PoseLandmark(x=0.8, y=0.9, z=0.0, visibility=1.0, name="right_wrist"),
        PoseLandmark(x=0.5, y=0.6, z=0.0, visibility=1.0, name="nose"),
    ]
    color = color_game._calculate_color(landmarks)
    # Ajusta la aserción según tu paleta "fire"
    assert isinstance(color, RGBColor)