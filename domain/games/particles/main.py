"""
Juego de partículas (async).

- Corre en su propio asyncio.Task.
- Se suscribe a eventos del bus.
- Publica estado al ParticlesState.
- La cámara y el render corren en un thread separado via run_in_executor.
"""

import asyncio
from collections.abc import Callable
from typing import cast

from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark
from domain.events.game_events import GameResetRequested
from domain.games.particles.state import ParticlesState
from domain.ports import render_port as legacy_render
from domain.ports.camera_port import CameraPort
from domain.ports.event_bus_port import EventBusPort, EventHandler
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render import particles_render_port as new_render
from domain.ports.render.scene_port import ScenePort
from infrastructure.logging.logger import get_logger

logger = get_logger("use_cases.particles")


class ParticlesGame:
    """Juego de partículas que reacciona a la pose (async)."""

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        state: ParticlesState,
        event_bus: EventBusPort,
        renderer: legacy_render.ParticlesRenderPort | None = None,
        scene: ScenePort | None = None,
        particles_capability: new_render.ParticlesRenderPort | None = None,
        gravity: float = 0.1,
        burst_count: int = 5,
        max_particles: int = 2000,
    ):
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._renderer: legacy_render.ParticlesRenderPort | None = renderer
        self._state = state
        self._event_bus = event_bus
        self._scene = scene
        self._particles_capability = particles_capability
        self._gravity = gravity
        self._burst_count = burst_count
        self._max_particles = max_particles

        self._particles: list[Particle] = []
        self._frame_count = 0
        self._use_new_render = self._scene is not None

        self._frame_count = 0
        self._reset_requested = False

        # Suscripción a eventos
        event_bus.subscribe(
            GameResetRequested, cast(EventHandler, self._on_reset_requested)
        )

    # ==========================================
    # Estado
    # ==========================================

    @property
    def state(self) -> ParticlesState:
        """Estado consultable del juego (para el StateRegistry)."""
        return self._state

    # ==========================================
    # Handler de eventos
    # ==========================================

    async def _on_reset_requested(self, event: GameResetRequested) -> None:
        """Marca bandera; el loop aplica el reset."""
        self._reset_requested = True
        logger.info("Reset de partículas solicitado")

    # ==========================================
    # Loop principal
    # ==========================================

    async def run_async(
        self,
        should_stop: Callable[[], bool] | None = None,
    ) -> None:
        should_stop = should_stop or (lambda: False)

        await asyncio.to_thread(self._camera.start)
        logger.info("Juego de partículas iniciado (async)")

        try:
            while not should_stop():
                # Aplica reset si fue solicitado
                if self._reset_requested:
                    self._reset_particles()
                    self._use_new_render = self._scene is not None

                # Frame (bloqueante → executor)
                frame = await asyncio.to_thread(self._camera.get_frame)
                if frame is None:
                    await asyncio.sleep(0.001)
                    continue

                # Pose (bloqueante → executor)
                try:
                    landmarks = await asyncio.to_thread(
                        self._pose_estimator.estimate, frame
                    )
                except Exception as e:
                    logger.warning(f"Error estimando pose: {e}")
                    continue

                # Actualiza estado del juego
                self._state.update_pose(landmarks)
                self._state.increment_frames()

                # Partículas
                self._spawn_particles_from_landmarks(landmarks)
                self._update_particles()

                if self._use_new_render:
                    if not await self._render_new(landmarks):
                        break
                else:
                    if not await self._render_legacy(landmarks):
                        break

                # Publica al estado
                self._state.update_particles(self._particles)

                self._frame_count += 1
                if self._frame_count % 100 == 0:
                    logger.debug(
                        f"Frame {self._frame_count}, "
                        f"partículas activas: {len(self._particles)}"
                    )

                # Cede control al loop
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info("Juego de partículas cancelado")
            raise
        finally:
            try:
                if self._use_new_render and self._scene is not None:
                    self._scene.close()
                elif self._renderer is not None:
                    self._renderer.close()
            except Exception as e:
                logger.error(f"Error cerrando renderer: {e}")
            try:
                await asyncio.to_thread(self._camera.stop)
            except Exception as e:
                logger.error(f"Error cerrando cámara: {e}")
            logger.info(f"Juego particles terminado. Frames: {self._frame_count}")

    def reset(self) -> None:
        """
        Reinicia el sistema de partículas.

        Método público para uso externo (ej: comandos, tests).
        Internamente llama a `_reset_particles()`.
        """
        self._reset_particles()

    async def _render_new(self, landmarks: list[PoseLandmark]) -> bool:
        """
        Path nuevo: set_particles + scene.render_frame.

        Returns:
            True si el render fue exitoso, False si falló.
        """
        assert self._scene is not None
        if isinstance(self._particles_capability, new_render.ParticlesRenderPort):
            self._particles_capability.set_particles(self._particles)
        try:
            await asyncio.to_thread(self._scene.render_frame, landmarks)
            return True
        except Exception as e:
            logger.error(f"Error renderizando (nuevo): {e}")
            return False

    async def _render_legacy(self, landmarks: list[PoseLandmark]) -> bool:
        """
        Path legacy: renderer.render_particles.

        Returns:
            True si el render fue exitoso, False si falló.
        """
        assert self._renderer is not None
        if isinstance(self._renderer, legacy_render.LandmarkAwareRenderPort):
            self._renderer.update_landmarks(landmarks)
        try:
            await asyncio.to_thread(self._renderer.render_particles, self._particles)
            return True
        except Exception as e:
            logger.error(f"Error renderizando: {e}")
            return False

    # ==========================================
    # Lógica interna
    # ==========================================

    def _spawn_particles_from_landmarks(self, landmarks: list[PoseLandmark]) -> None:
        for landmark in landmarks:
            if landmark.is_visible():
                px = landmark.x * 640
                py = landmark.y * 480
                new_particles = Particle.create_burst(px, py, count=self._burst_count)
                self._particles.extend(new_particles)

        if len(self._particles) > self._max_particles:
            self._particles = self._particles[-int(self._max_particles * 0.75) :]

    def _update_particles(self) -> None:
        for particle in self._particles:
            particle.update(gravity=self._gravity)
        self._particles = [p for p in self._particles if p.is_alive()]

    def _reset_particles(self) -> None:
        self._particles.clear()
        logger.info("Sistema de partículas reiniciado")
