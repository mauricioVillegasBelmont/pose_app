"""
Juego de partículas con lógica real.

Mecánica:
- Aparecen N partículas al azar en el workspace.
- El usuario las toca con las manos (landmarks de pose).
- +1 punto por ronda completada.
- Si el timer se agota → nueva ronda (sin punto).
- Color de fondo cambia según puntuación.
- Victoria al alcanzar max_score.
"""

import asyncio
import random
import time
from collections.abc import Callable

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.games.particles.geometry import (
    Workspace,
    detect_collisions,
)
from pose_app.domain.games.particles.scoring import (
    color_for_score,
    is_winner,
    particles_per_round,
)
from pose_app.domain.games.particles.spawn import spawn_particles
from pose_app.domain.games.particles.state import ParticlesState
from pose_app.domain.ports.camera_port import CameraPort
from pose_app.domain.ports.event_bus_port import EventBusPort
from pose_app.domain.ports.pose_estimator_port import PoseEstimatorPort
from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.domain.ports.render.hud_render_port import HudRenderPort
from pose_app.domain.ports.render.particles_render_port import ParticlesRenderPort
from pose_app.domain.ports.render.scene_port import ScenePort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("use_cases.particles")


class ParticlesGame:
    """Juego de tocar partículas."""

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        scene: ScenePort,
        particles_capability: ParticlesRenderPort,
        color_capability: ColorRenderPort,
        hud_capability: HudRenderPort,
        state: ParticlesState,
        event_bus: EventBusPort,
        screen_width: int = 800,
        screen_height: int = 600,
        rng: random.Random | None = None,
        max_score: int = 10,
        time_per_round: float = 10.0,
        hit_radius: float = 30.0,
        workspace: Workspace | None = None,
        particle_min_distance: float = 0.15,
        particle_size: float = 20.0,
        particle_color: tuple[int, int, int] = (255, 200, 50),
    ) -> None:
        """
        Inicializa el juego.

        Args:
            camera: puerto de cámara.
            pose_estimator: puerto de estimación de pose.
            scene: compositor de render.
            particles_capability: capacidad de render de partículas.
            color_capability: capacidad de render de fondo.
            hud_capability: capacidad de render de HUD.
            state: estado del juego (consultable).
            event_bus: bus de eventos.
            screen_width: ancho de pantalla en píxeles.
            screen_height: alto de pantalla en píxeles.
            rng: generador aleatorio (inyectable para tests).
            max_score: puntuación objetivo para ganar.
            time_per_round: segundos por ronda.
            hit_radius: radio de colisión en píxeles.
            workspace: zona de spawn (default: Workspace por defecto).
            particle_min_distance: distancia mínima normalizada entre partículas.
            particle_size: tamaño base de partícula en píxeles.
            particle_color: color RGB base de partícula.
        """
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._scene = scene
        self._particles_capability = particles_capability
        self._color_capability = color_capability
        self._hud_capability = hud_capability
        self._state = state
        self._event_bus = event_bus

        self._screen_width = screen_width
        self._screen_height = screen_height
        self._rng = rng or random.Random()
        self._max_score = max_score
        self._time_per_round = time_per_round
        self._hit_radius = hit_radius
        self._workspace = workspace or Workspace()
        self._particle_min_distance = particle_min_distance
        self._particle_size = particle_size
        self._particle_color = particle_color

        self._particles: list[Particle] = []
        self._current_round: int = 1
        self._time_remaining: float = time_per_round
        self._frame_count: int = 0

    @property
    def state(self) -> ParticlesState:
        """Estado consultable del juego."""
        return self._state

    # ==========================================
    # Loop principal
    # ==========================================

    async def run_async(self, should_stop: Callable[[], bool] | None = None) -> None:
        """Loop principal del juego."""
        should_stop = should_stop or (lambda: False)

        await asyncio.to_thread(self._camera.start)
        logger.info("Juego de partículas iniciado")

        self._start_new_round()

        last_time = time.monotonic()

        try:
            while not should_stop():
                if self._state.is_game_over():
                    logger.info("Game over alcanzado")
                    break

                frame = await asyncio.to_thread(self._camera.get_frame)
                if frame is None:
                    await asyncio.sleep(0.001)
                    continue

                try:
                    landmarks = await asyncio.to_thread(
                        self._pose_estimator.estimate, frame
                    )
                except Exception as e:
                    logger.warning(f"Error estimando pose: {e}")
                    continue

                # Delta time
                now = time.monotonic()
                dt = now - last_time
                last_time = now

                # Lógica
                self._update_logic(landmarks, dt)

                # Render
                try:
                    await self._render_frame(landmarks)
                except Exception as e:
                    logger.error(f"Error renderizando: {e}")
                    break

                self._frame_count += 1
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info("Juego cancelado")
            raise
        finally:
            try:
                self._scene.close()
            except Exception as e:
                logger.error(f"Error cerrando scene: {e}")
            try:
                await asyncio.to_thread(self._camera.stop)
            except Exception as e:
                logger.error(f"Error cerrando cámara: {e}")
            logger.info(f"Juego terminado. Frames: {self._frame_count}")

    # ==========================================
    # Lógica de negocio
    # ==========================================

    def _start_new_round(self) -> None:
        """Genera partículas nuevas al inicio de una ronda."""
        num_particles = particles_per_round(self._current_round)

        self._particles = spawn_particles(
            count=num_particles,
            workspace=self._workspace,
            screen_width=self._screen_width,
            screen_height=self._screen_height,
            rng=self._rng,
            min_distance=self._particle_min_distance,
            particle_size=self._particle_size,
            particle_color=self._particle_color,
        )

        self._time_remaining = self._time_per_round

        self._state.set_particles_count(len(self._particles))
        self._state.set_time_remaining(self._time_remaining)
        self._state.set_round_number(self._current_round)

        logger.info(f"Ronda {self._current_round}: {len(self._particles)} partículas")

    def _update_logic(self, landmarks: list[PoseLandmark], dt: float) -> None:
        """Actualiza la lógica del juego para este frame."""
        # 1. Detectar colisiones
        remaining, hits = detect_collisions(
            particles=self._particles,
            landmarks=landmarks,
            screen_width=self._screen_width,
            screen_height=self._screen_height,
            hit_radius=self._hit_radius,
        )

        self._particles = remaining
        self._state.set_particles_count(len(self._particles))

        if hits > 0:
            logger.debug(f"¡{hits} partícula(s) tocada(s)!")

        # 2. ¿Ronda completada?
        if not self._particles:
            self._complete_round()
            return

        # 3. Actualizar timer
        self._time_remaining = max(0.0, self._time_remaining - dt)
        self._state.set_time_remaining(self._time_remaining)

        # 4. ¿Timer agotado?
        if self._time_remaining <= 0.0:
            logger.info(f"Timer agotado. Reiniciando ronda {self._current_round}")
            self._start_new_round()

    def _complete_round(self) -> None:
        """El usuario tocó todas las partículas."""
        self._state.increment_score()
        new_score = self._state.get_score()
        logger.info(f"¡Ronda completada! Puntos: {new_score}")

        if is_winner(new_score, self._max_score):
            self._state.set_game_over(winner=True)
            logger.info("¡VICTORIA!")
            return

        self._current_round += 1
        self._start_new_round()

    # ==========================================
    # Render
    # ==========================================

    async def _render_frame(self, landmarks: list[PoseLandmark]) -> None:
        """Actualiza capacidades y renderiza el frame."""
        # Fondo
        color = color_for_score(self._state.get_score())
        self._color_capability.set_color(color)

        # Partículas
        self._particles_capability.set_particles(self._particles)

        # HUD
        self._hud_capability.set_hud(
            score=self._state.get_score(),
            rounds=self._current_round,
            timer=self._time_remaining,
        )

        # Render
        await asyncio.to_thread(self._scene.render_frame, landmarks)
