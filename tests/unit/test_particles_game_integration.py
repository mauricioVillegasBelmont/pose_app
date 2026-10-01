"""
Tests de integración del loop run_async de ParticlesGame.

Usa mocks puros (sin cámara, sin pygame real).
"""

import asyncio
from unittest.mock import Mock

import numpy as np
import pytest

from adapters.mock.mock_render import MockParticlesRenderAdapter
from domain.entities.pose_landmark import PoseLandmark
from domain.games.particles.main import ParticlesGame
from domain.games.particles.state import ParticlesState
from infrastructure.events.async_event_bus import AsyncEventBus


@pytest.fixture
def game_with_frame():
    """Game con cámara que devuelve un frame y luego None."""
    mock_camera = Mock()
    frames = [np.zeros((480, 640, 3), dtype=np.uint8), None]
    mock_camera.get_frame.side_effect = lambda: frames.pop(0) if frames else None

    mock_pose = Mock()
    mock_pose.estimate.return_value = [
        PoseLandmark(0.5, 0.5, 0.0, 1.0, "nose"),
    ]

    mock_renderer = MockParticlesRenderAdapter()

    return ParticlesGame(
        camera=mock_camera,
        pose_estimator=mock_pose,
        renderer=mock_renderer,
        state=ParticlesState(),
        event_bus=AsyncEventBus(),
    )


@pytest.mark.asyncio
async def test_run_generates_particles(game_with_frame):
    """El loop genera partículas cuando hay landmarks visibles."""
    stop_after = {"count": 0}

    def should_stop():
        stop_after["count"] += 1
        return stop_after["count"] > 3

    await game_with_frame.run_async(should_stop=should_stop)

    # El estado debe reflejar frames procesados
    assert game_with_frame.state.snapshot()["frame_count"] > 0


@pytest.mark.asyncio
async def test_run_calls_renderer(game_with_frame):
    """El loop llama al renderer."""
    stop_after = {"count": 0}

    def should_stop():
        stop_after["count"] += 1
        return stop_after["count"] > 3

    await game_with_frame.run_async(should_stop=should_stop)

    assert game_with_frame._renderer.render_count > 0