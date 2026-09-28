"""
Test del decorador PoseDebugOverlay usando mocks.

Nota: El decorador PoseDebugOverlay requiere un adaptador Pygame real
para acceder a `screen`, `width`, `height`. Por eso aquí solo
verificamos la integración con mocks a nivel de puerto.

El decorador en sí se prueba en tests/integration/ con Pygame real.
"""


from adapters.mock.mock_render import MockParticlesRenderAdapter
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark


def test_particles_game_with_mock_renderer():
    """
    Test end-to-end con mocks: verifica que el juego
    pasa las partículas al renderer.
    """
    from unittest.mock import Mock

    from domain.use_cases.particles_game import ParticlesGame

    # Arrange: mocks de todos los adaptadores
    mock_camera = Mock()
    mock_camera.get_frame.return_value = None  # Salir del loop rápido

    mock_pose = Mock()
    mock_pose.estimate.return_value = []

    mock_renderer = MockParticlesRenderAdapter()

    # El juego correrá un ciclo vacío (frame=None)
    game = ParticlesGame(
        camera=mock_camera,
        pose_estimator=mock_pose,
        renderer=mock_renderer,
        state=None,
    )

    # Act: corremos un ciclo y paramos
    iterations = [0]
    def should_stop():
        iterations[0] += 1
        return iterations[0] > 3

    game.run(should_stop=should_stop)

    # Assert: el renderer fue cerrado por el juego
    assert mock_renderer.is_closed is True


def test_particles_game_with_landmarks():
    """
    Verifica que el juego notifique landmarks al renderer
    cuando éste implementa LandmarkAwareRenderPort.
    """
    from unittest.mock import Mock

    from domain.use_cases.particles_game import ParticlesGame

    # Arrange
    mock_camera = Mock()
    # Simula un frame válido la primera vez, luego None
    import numpy as np
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
        state=None,
    )

    # Act
    iterations = [0]
    def should_stop():
        iterations[0] += 1
        return iterations[0] > 2

    game.run(should_stop=should_stop)

    # Assert: el renderer recibió landmarks (por ser LandmarkAware)
    assert mock_renderer.update_landmarks_count > 0
    assert any(lm.name == "nose" for lm in mock_renderer.last_landmarks)