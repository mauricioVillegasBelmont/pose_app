"""
Script manual: cámara real + pose mock + render mock.

Requiere cámara física. NO se ejecuta con pytest (está en tests/manual/,
excluido vía norecursedirs en pyproject.toml).

Uso:
    uv run python tests/manual/webcam_mock_pose.py

Verifica que la cadena completa de adaptadores funcione corriendo el juego
por 2 segundos con cámara real y pose/render mockeados.
"""

import asyncio
import threading
import time

from pose_app.adapters.camera.webcam_adapter import WebcamAdapter
from pose_app.adapters.mock.mock_pose import MockPoseAdapter
from pose_app.adapters.mock.mock_render import MockParticlesRenderAdapter
from pose_app.domain.games.particles.main import ParticlesGame
from pose_app.domain.games.particles.state import ParticlesState
from pose_app.infrastructure.events.async_event_bus import AsyncEventBus


def run_webcam_mock_pose() -> None:
    """
    Corre el juego por 2 segundos con cámara real y mocks.

    Raises:
        AssertionError: Si no se renderizó ningún frame o el estado
            no registró frames procesados.
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

    def _run_game() -> None:
        asyncio.run(game.run_async(should_stop=lambda: stop_flag["stop"]))

    thread = threading.Thread(target=_run_game, daemon=True)
    thread.start()
    time.sleep(2.0)
    stop_flag["stop"] = True
    thread.join(timeout=3.0)

    # Assert
    assert renderer.render_count > 0, "No se renderizó ningún frame"
    assert state.snapshot()["frame_count"] > 0

    print(f"✅ Prueba completada: {renderer.render_count} frames renderizados")


if __name__ == "__main__":
    run_webcam_mock_pose()
