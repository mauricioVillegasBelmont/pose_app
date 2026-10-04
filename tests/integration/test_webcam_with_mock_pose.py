"""
Test de integración: cámara real + pose mock + render mock.

Verifica que la cadena completa de adaptadores funcione.
Marcado como skip si no hay cámara disponible.
"""

import threading
import time

import pytest

from adapters.camera.webcam_adapter import WebcamAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from adapters.mock.mock_render import MockParticlesRenderAdapter
from domain.games.particles.main import ParticlesGame  # ← ruta nueva
from domain.games.particles.state import ParticlesState
from infrastructure.events.async_event_bus import AsyncEventBus


@pytest.mark.skip(reason="Requiere cámara física, correr manualmente")
def test_webcam_with_mock_pose_and_render():
    """
    Corre el juego por 2 segundos con cámara real y mocks.

    Se marca skip por defecto (requiere hardware).
    Correr con: pytest -k webcam --no-skip
    """
    # Arrange
    camera = WebcamAdapter(camera_id=0, width=320, height=240)
    pose_estimator = MockPoseAdapter()
    renderer = MockParticlesRenderAdapter()
    state = ParticlesState()
    event_bus = AsyncEventBus()

    game = ParticlesGame(
        camera=camera,
        pose_estimator=pose_estimator,
        renderer=renderer,
        state=state,
        event_bus=event_bus,
    )

    # Act: corre por 2 segundos en un thread
    stop_flag = {"stop": False}

    def run_game():
        import asyncio

        asyncio.run(game.run_async(should_stop=lambda: stop_flag["stop"]))

    thread = threading.Thread(target=run_game, daemon=True)
    thread.start()
    time.sleep(2.0)
    stop_flag["stop"] = True
    thread.join(timeout=3.0)

    # Assert
    assert renderer.render_count > 0, "No se renderizó ningún frame"
    assert state.snapshot()["frame_count"] > 0
