"""
Tests del GameContext (dataclass).
"""

from unittest.mock import Mock

import pytest

from pose_app.app.game_context import GameContext
from pose_app.config.game_profile import GameProfileConfig


def test_game_context_is_frozen() -> None:
    """El contexto debe ser inmutable."""
    ctx = GameContext(
        camera=Mock(),
        pose_estimator=Mock(),
        event_bus=Mock(),
        settings=Mock(),
        gameplay_config=GameProfileConfig(),  # <-- AÑADIR
    )
    with pytest.raises(AttributeError):
        ctx.camera = Mock()  # type: ignore


def test_game_context_stores_fields() -> None:
    cam = Mock()
    pose = Mock()
    bus = Mock()
    settings = Mock()
    config = GameProfileConfig()  # <-- AÑADIR

    ctx = GameContext(
        camera=cam,
        pose_estimator=pose,
        event_bus=bus,
        settings=settings,
        gameplay_config=config,  # <-- AÑADIR
    )

    assert ctx.camera is cam
    assert ctx.pose_estimator is pose
    assert ctx.event_bus is bus
    assert ctx.settings is settings
    assert ctx.gameplay_config is config
