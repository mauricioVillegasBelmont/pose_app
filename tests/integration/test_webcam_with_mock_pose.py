# tests/integration/test_webcam_with_mock_pose.py
import time

from adapters.camera.webcam_adapter import WebcamAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from adapters.mock.mock_render import MockRenderAdapter
from domain.use_cases.particles_game import ParticlesGame


def test_webcam_with_mock_pose():
    """
    Prueba de integración: cámara real + estimador mock.
    Verifica que los frames se capturen y se procesen correctamente.
    """
    # Arrange: adaptadores reales + mocks
    camera = WebcamAdapter(camera_id=0, width=320, height=240)
    pose_estimator = MockPoseAdapter()
    renderer = MockRenderAdapter()

    # Caso de uso con inyección
    game = ParticlesGame(camera, pose_estimator, renderer)

    # Act: corre por 2 segundos
    import threading

    def run_game():
        game.run()  # Esto bloquearía, así que lo ejecutamos en hilo

    thread = threading.Thread(target=run_game, daemon=True)
    thread.start()

    # Espera 2 segundos
    print("⏳ Ejecutando juego por 2 segundos...")
    time.sleep(2.0)

    # Detiene el juego (simula Ctrl+C)
    # Nota: en producción usarías una bandera de stop
    camera.stop()
    renderer.close()

    thread.join(timeout=1.0)

    # Assert: verificamos que se capturaron frames
    assert camera._frame_count > 0, "No se capturaron frames"
    assert len(game._particles) > 0, "No se generaron partículas"

    print(f"✅ Prueba exitosa: {camera._frame_count} frames capturados")