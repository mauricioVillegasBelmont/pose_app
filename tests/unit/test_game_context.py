"""
Tests del GameContext (dataclass).
"""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.game_context import GameContext


def test_game_context_is_frozen():
    """El contexto debe ser inmutable."""
    ctx = GameContext(
        camera=Mock(),
        pose_estimator=Mock(),
        event_bus=Mock(),
        settings=Mock(),
    )

    with pytest.raises(FrozenInstanceError):
        ctx.camera = Mock()


def test_game_context_stores_fields():
    cam = Mock()
    pose = Mock()
    bus = Mock()
    settings = Mock()

    ctx = GameContext(
        camera=cam,
        pose_estimator=pose,
        event_bus=bus,
        settings=settings,
    )

    assert ctx.camera is cam
    assert ctx.pose_estimator is pose
    assert ctx.event_bus is bus
    assert ctx.settings is settings
