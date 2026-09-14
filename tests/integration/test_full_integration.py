# tests/integration/test_full_integration.py
from adapters.camera.webcam_adapter import WebcamAdapter
from adapters.pose.mediapipe_adapter import MediapipeAdapter
from adapters.render.pygame_render_adapter import PygameRenderAdapter
from domain.use_cases.particles_game import ParticlesGame


def test_full_particles_game():
    """
    Prueba completa: cámara real + Mediapipe + Pygame.
    Corre el juego de partículas por 10 segundos.
    """
    # Arrange
    camera = WebcamAdapter(camera_id=0, width=640, height=480)
    pose_estimator = MediapipeAdapter(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    )
    renderer = PygameRenderAdapter(
        width=800,
        height=600,
        title="Juego de Partículas - RA"
    )

    # Caso de uso
    game = ParticlesGame(
        camera=camera,
        pose_estimator=pose_estimator,
        renderer=renderer,
        gravity=0.08,
        burst_radius=50
    )

    # Act
    try:
        print("🎮 Iniciando juego de partículas...")
        print("Presiona Ctrl+C para detener")
        game.run()  # Esto corre hasta que se cierre la ventana o Ctrl+C

    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo juego...")

    finally:
        # Cleanup
        camera.stop()
        pose_estimator.close()
        renderer.close()
        print("✅ Juego terminado")


if __name__ == "__main__":
    test_full_particles_game()