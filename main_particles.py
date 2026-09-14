import sys

from adapters.mock.mock_render import MockRenderAdapter

from adapters.mock.mock_camera import MockCameraAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from domain.use_cases.particles_game import ParticlesGame


def main():
    """Punto de entrada con inyección de dependencias manual."""
    # Configurar adaptadores
    camera = MockCameraAdapter(width=640, height=480)
    pose_estimator = MockPoseAdapter()

    # NOTA: El renderer real (Pygame) lo implementaremos en Fase 2
    # Por ahora usamos un renderer mock que solo imprime en consola
    renderer = MockRenderAdapter()

    # Crear caso de uso con inyección
    game = ParticlesGame(
        camera=camera,
        pose_estimator=pose_estimator,
        renderer=renderer,
        gravity=0.05,
        burst_radius=30
    )

    # Ejecutar
    try:
        game.run()
    except KeyboardInterrupt:
        print("\nJuego detenido por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()