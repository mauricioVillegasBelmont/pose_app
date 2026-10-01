"""
Tests del decorador PoseDebugOverlay usando mocks.

Verifica la integración del juego con renderers mock,
incluyendo el flujo async de `run_async`.
"""

from unittest.mock import Mock

import numpy as np
import pytest

from adapters.mock.mock_render import MockParticlesRenderAdapter
from domain.entities.pose_landmark import PoseLandmark
from domain.games.particles.main import ParticlesGame
from domain.games.particles.state import ParticlesState
from infrastructure.events.async_event_bus import AsyncEventBus


@pytest.mark.asyncio
async def test_particles_game_with_mock_renderer():
    """
    Test end-to-end con mocks: verifica que el juego
    cierra el renderer al terminar `run_async`.
    """
    # Arrange
    mock_camera = Mock()
    mock_camera.get_frame.return_value = None  # Salir del loop rápido

    mock_pose = Mock()
    mock_pose.estimate.return_value = []

    mock_renderer = MockParticlesRenderAdapter()

    game = ParticlesGame(
        camera=mock_camera,
        pose_estimator=mock_pose,
        renderer=mock_renderer,
        state=ParticlesState(),
        event_bus=AsyncEventBus(),
    )

    # Act
    iterations = [0]

    def should_stop():
        iterations[0] += 1
        return iterations[0] > 3

    await game.run_async(should_stop=should_stop)  # ← await

    # Assert: el renderer fue cerrado por el juego
    assert mock_renderer.is_closed is True


@pytest.mark.asyncio
async def test_particles_game_with_landmarks():
    """
    Verifica que el juego notifique landmarks al renderer
    cuando éste implementa LandmarkAwareRenderPort.
    """
    # Arrange
    mock_camera = Mock()
    frames = [np.zeros((480, 640, 3), dtype=np.uint8), None]
    mock_camera.get_frame.side_effect = lambda: frames.pop(0) if frames else None

    mock_pose = Mock()
    mock_pose.estimate.return_value = [
        PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose"),
    ]

    mock_renderer = MockParticlesRenderAdapter()

    game = ParticlesGame(
        camera=mock_camera,
        pose_estimator=mock_pose,
        renderer=mock_renderer,
        state=ParticlesState(),
        event_bus=AsyncEventBus(),
    )

    # Act
    iterations = [0]

    def should_stop():
        iterations[0] += 1
        return iterations[0] > 2

    await game.run_async(should_stop=should_stop)  # ← await

    # Assert: el renderer recibió landmarks
    assert mock_renderer.update_landmarks_count > 0
    assert any(lm.name == "nose" for lm in mock_renderer.last_landmarks)