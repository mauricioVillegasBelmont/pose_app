# test_minimal.py
"""
Prueba mínima: verifica que la cadena completa funciona.
"""
from adapters.mock.mock_camera import MockCameraAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from adapters.mock.mock_render import MockRenderAdapter
from domain.use_cases.particles_game import ParticlesGame


def test_minimal_chain():
    print("🧪 Ejecutando prueba mínima...")

    # 1. Crea los adaptadores
    camera = MockCameraAdapter()
    pose = MockPoseAdapter()
    render = MockRenderAdapter()

    # 2. Crea el juego
    game = ParticlesGame(camera, pose, render)

    # 3. Simula un ciclo manual
    camera.start()
    frame = camera.get_frame()

    assert frame is not None, "❌ MockCamera no devolvió frame"
    print(f"✅ Frame capturado: shape={frame.shape}")

    landmarks = pose.estimate(frame)
    assert len(landmarks) > 0, "❌ MockPose no devolvió landmarks"
    print(f"✅ Landmarks detectados: {len(landmarks)}")

    # 4. Genera partículas
    game._spawn_particles_from_landmarks(landmarks)
    assert len(game._particles) > 0, "❌ No se generaron partículas"
    print(f"✅ Partículas generadas: {len(game._particles)}")

    # 5. Renderiza
    render.render_particles(game._particles)
    print("✅ Render ejecutado")

    # 6. Cleanup
    camera.stop()
    render.close()

    print("\n🎉 ¡Cadena completa funcionando!")


if __name__ == "__main__":
    test_minimal_chain()