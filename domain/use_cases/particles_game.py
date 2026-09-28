from collections.abc import Callable

from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.camera_port import CameraPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import (
    LandmarkAwareRenderPort,
    ParticlesRenderPort,
)
from domain.ports.state_port import StatePort
from infrastructure.logging.logger import get_logger

logger = get_logger("use_cases.particles")


class ParticlesGame:
    """Caso de uso: juego de partículas que reaccionan a la pose."""

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        renderer: ParticlesRenderPort,
        state: StatePort | None = None,
        gravity: float = 0.1,
        burst_radius: float = 50.0,
        burst_count: int = 5,
        max_particles: int = 2000,
    ):
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._renderer = renderer
        self._state = state
        self._gravity = gravity
        self._burst_radius = burst_radius
        self._burst_count = burst_count
        self._max_particles = max_particles
        self._particles: list[Particle] = []
        self._frame_count = 0

    def run(self, should_stop: Callable[[], bool] | None = None) -> None:
        should_stop = should_stop or (lambda: False)

        self._camera.start()
        logger.info("Juego de partículas iniciado")

        try:
            while not should_stop():
                # 1. Comandos
                self._process_commands()

                # 2. Frame
                frame = self._camera.get_frame()
                if frame is None:
                    continue

                # 3. Pose
                try:
                    landmarks = self._pose_estimator.estimate(frame)
                except Exception as e:
                    logger.warning(f"Error estimando pose: {e}")
                    continue

                # 4. Estado compartido
                if self._state:
                    self._state.update_pose(landmarks)
                    self._state.increment_frames()

                # 5. Notificar landmarks al renderer (si aplica)
                if isinstance(self._renderer, LandmarkAwareRenderPort):
                    self._renderer.update_landmarks(landmarks)

                # 6. Partículas
                self._spawn_particles_from_landmarks(landmarks)

                # 7. Física
                self._update_particles()

                # 8. Render
                try:
                    self._renderer.render_particles(self._particles)
                except Exception as e:
                    logger.error(f"Error renderizando: {e}")
                    break

                # 9. Publicar al estado
                if self._state:
                    self._state.update_game_data("particles", self._particles)
                    self._state.update_game_data(
                        "particles_count", len(self._particles)
                    )

                self._frame_count += 1

                if self._frame_count % 100 == 0:
                    logger.debug(
                        f"Frame {self._frame_count}, "
                        f"partículas activas: {len(self._particles)}"
                    )

        except KeyboardInterrupt:
            logger.info("Interrupción por teclado")
        except Exception as e:
            logger.error(f"Error en el loop del juego: {e}", exc_info=True)
        finally:
            # Cierre garantizado del renderer (idempotente)
            try:
                self._renderer.close()
            except Exception as e:
                logger.error(f"Error cerrando renderer: {e}")
            logger.info(
                f"Juego particles terminado. Frames: {self._frame_count}"
            )

    def _process_commands(self) -> None:
        """Consume comandos pendientes del estado compartido."""
        if self._state is None:
            return

        commands = self._state.drain_commands()
        for cmd in commands:
            if cmd.action == "reset_particles":
                self.reset()
                logger.info("Comando reset_particles aplicado")
            else:
                logger.debug(f"Comando ignorado por ParticlesGame: {cmd.action}")

    def _spawn_particles_from_landmarks(
        self, landmarks: list[PoseLandmark]
    ) -> None:
        for landmark in landmarks:
            if landmark.is_visible():
                px = landmark.x * 640
                py = landmark.y * 480

                new_particles = Particle.create_burst(
                    px, py, count=self._burst_count
                )
                self._particles.extend(new_particles)

        if len(self._particles) > self._max_particles:
            self._particles = self._particles[
                -int(self._max_particles * 0.75):
            ]

    def _update_particles(self) -> None:
        for particle in self._particles:
            particle.update(gravity=self._gravity)

        self._particles = [p for p in self._particles if p.is_alive()]

    def reset(self) -> None:
        """Reinicia el sistema de partículas."""
        self._particles.clear()
        logger.info("Sistema de partículas reiniciado")