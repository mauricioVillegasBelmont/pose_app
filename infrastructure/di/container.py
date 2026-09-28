"""
Contenedor de inyección de dependencias (manual).

Responsabilidades:
- Crear adaptadores según la configuración
- Inyectarlos en los casos de uso
- Gestionar el ciclo de vida (creación/cierre)
"""

from typing import Self

from adapters.api.fastapi_adapter import FastAPIAdapter
from adapters.camera.webcam_adapter import WebcamAdapter
from adapters.mock.mock_camera import MockCameraAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from adapters.pose.mediapipe_adapter import MediapipeAdapter
from adapters.render.pygame_base import PygameBaseAdapter
from app.state import AppState
from config.settings import Settings
from domain.entities.color import RGBColor
from domain.ports.camera_port import CameraPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import (
    BaseRenderPort,
    ColorRenderPort,
    ParticlesRenderPort,
)
from domain.use_cases.color_game import ColorGame
from domain.use_cases.particles_game import ParticlesGame
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.logging.logger import get_logger

logger = get_logger("di")


class Container:
    """Contenedor de dependencias."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._camera: CameraPort | None = None
        self._pose_estimator: PoseEstimatorPort | None = None
        self._state: AppState | None = None
        self._api: FastAPIAdapter | None = None
        self._active_renderer: BaseRenderPort | None = None
        # Nota: los renderers se crean por juego, no como singleton
        logger.debug("Contenedor DI inicializado")

    # ==========================================
    # Propiedades con lazy initialization
    # ==========================================

    @property
    def camera(self) -> CameraPort:
        if self._camera is None:
            self._camera = self._create_camera()
        return self._camera

    @property
    def pose_estimator(self) -> PoseEstimatorPort:
        if self._pose_estimator is None:
            self._pose_estimator = self._create_pose_estimator()
        return self._pose_estimator

    @property
    def state(self) -> AppState:
        if self._state is None:
            self._state = AppState()
        return self._state

    @property
    def api(self) -> FastAPIAdapter | None:
        if not self._settings.api.enabled:
            return None

        if self._api is None:
            self._api = FastAPIAdapter(
                settings=self._settings.api,
                state=self.state,
            )
        return self._api

    # ==========================================
    # Fábricas de adaptadores
    # ==========================================

    def _create_camera(self) -> CameraPort:
        cfg = self._settings.camera

        if self._settings.environment == "testing":
            logger.info("Usando MockCameraAdapter (entorno testing)")
            return MockCameraAdapter(width=cfg.width, height=cfg.height)

        try:
            logger.info(f"Creando WebcamAdapter (cámara {cfg.id})")
            return WebcamAdapter(
                camera_id=cfg.id,
                width=cfg.width,
                height=cfg.height,
                fps=cfg.fps,
            )
        except Exception as e:
            raise ConfigurationError(
                f"No se pudo crear la cámara: {e}",
                context={"camera_id": cfg.id},
            ) from e

    def _create_pose_estimator(self) -> PoseEstimatorPort:
        cfg = self._settings.pose

        if cfg.provider == "mock":
            logger.info("Usando MockPoseAdapter")
            return MockPoseAdapter()

        if cfg.provider == "mediapipe":
            logger.info(
                f"Usando MediapipeAdapter (complexity={cfg.model_complexity})"
            )
            return MediapipeAdapter(
                min_detection_confidence=cfg.min_detection_confidence,
                min_tracking_confidence=cfg.min_tracking_confidence,
                model_complexity=cfg.model_complexity,
            )

        raise ConfigurationError(
            f"Proveedor de pose desconocido: {cfg.provider}",
            context={"provider": cfg.provider},
        )

    def _create_particles_renderer(self) -> ParticlesRenderPort:
        """Crea el render de partículas, opcionalmente decorado."""
        cfg = self._settings.render

        # 1. Adaptador base
        if cfg.provider == "mock":
            from adapters.mock.mock_render import MockParticlesRenderAdapter
            base: ParticlesRenderPort = MockParticlesRenderAdapter()
        elif cfg.provider == "pygame":
            from adapters.render.pygame_particles_adapter import (
                PygameParticlesAdapter,
            )
            base = PygameParticlesAdapter(
                width=cfg.width,
                height=cfg.height,
                title=cfg.title,
                target_fps=cfg.target_fps,
                background_color=RGBColor(20, 20, 30),
            )
        else:
            raise ConfigurationError(
                f"Proveedor de render desconocido: {cfg.provider}",
                context={"provider": cfg.provider},
            )

        # 2. Decorador opcional (solo para Pygame)
        if cfg.debug_overlay and isinstance(base, PygameBaseAdapter):
            from adapters.render.decorators.pose_debug_overlay import (
                PoseDebugOverlay,
            )
            logger.info("Activando PoseDebugOverlay sobre Particles")
            return PoseDebugOverlay(base)

        self._active_renderer = base
        return base

    def _create_color_renderer(self) -> ColorRenderPort:
        """Crea el render de color, opcionalmente decorado."""
        cfg = self._settings.render

        # 1. Adaptador base
        if cfg.provider == "mock":
            from adapters.mock.mock_render import MockColorRenderAdapter
            base: ColorRenderPort = MockColorRenderAdapter()
        elif cfg.provider == "pygame":
            from adapters.render.pygame_color_adapter import (
                PygameColorAdapter,
            )
            base = PygameColorAdapter(
                width=cfg.width,
                height=cfg.height,
                title=cfg.title,
                target_fps=cfg.target_fps,
            )
        else:
            raise ConfigurationError(
                f"Proveedor de render desconocido: {cfg.provider}",
                context={"provider": cfg.provider},
            )

        # 2. Decorador opcional (solo para Pygame)
        if cfg.debug_overlay and isinstance(base, PygameBaseAdapter):
            from adapters.render.decorators.pose_debug_overlay import (
                PoseDebugOverlay,
            )
            logger.info("Activando PoseDebugOverlay sobre Color")
            return PoseDebugOverlay(base)

        self._active_renderer = base
        return base

    # ==========================================
    # Fábrica de casos de uso
    # ==========================================

    def create_game(self) -> ParticlesGame | ColorGame:
        game_type = self._settings.game.type

        if game_type == "particles":
            logger.info("Creando ParticlesGame")
            return ParticlesGame(
                camera=self.camera,
                pose_estimator=self.pose_estimator,
                renderer=self._create_particles_renderer(),  # ← con ()
                state=self.state,
                gravity=self._settings.game.gravity,
                burst_radius=50.0,
                burst_count=self._settings.game.burst_count,
                max_particles=self._settings.game.max_particles,
            )

        if game_type == "color":
            logger.info(
                f"Creando ColorGame (palette={self._settings.game.palette})"
            )
            return ColorGame(
                camera=self.camera,
                pose_estimator=self.pose_estimator,
                renderer=self._create_color_renderer(),  # ← con ()
                state=self.state,
                palette_name=self._settings.game.palette,
            )

        raise ConfigurationError(
            f"Tipo de juego desconocido: {game_type}",
            context={"game_type": game_type},
        )

    # ==========================================
    # Ciclo de vida
    # ==========================================

    def start_api(self) -> None:
        if self.api is not None:
            self.api.start()
            logger.info("API iniciada desde el contenedor")

    def shutdown(self) -> None:
        logger.info("Cerrando contenedor DI...")

        # API primero
        if self._api is not None:
            try:
                self._api.stop()
            except Exception as e:
                logger.error(f"Error cerrando API: {e}")
            self._api = None

        # Renderer activo
        if self._active_renderer is not None:
            try:
                self._active_renderer.close()  # idempotente
            except Exception as e:
                logger.error(f"Error cerrando renderer: {e}")
            self._active_renderer = None

        # Cámara
        if self._camera is not None:
            try:
                self._camera.stop()
            except Exception as e:
                logger.error(f"Error cerrando cámara: {e}")
            self._camera = None

        # Pose
        if self._pose_estimator is not None:
            try:
                self._pose_estimator.close()
            except Exception as e:
                logger.error(f"Error cerrando pose estimator: {e}")
            self._pose_estimator = None

        logger.info("Contenedor DI cerrado")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()