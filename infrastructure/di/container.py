"""
Contenedor de inyección de dependencias (manual).

Responsabilidades:
- Crear adaptadores según la configuración
- Inyectarlos en los casos de uso
- Gestionar el ciclo de vida (creación/cierre)

Es el "wiring" de la aplicación.
"""


from typing import Self

import cv2

# Adaptadores
from adapters.api.fastapi_adapter import FastAPIAdapter
from adapters.camera.webcam_adapter import WebcamAdapter
from adapters.mock.mock_camera import MockCameraAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from adapters.mock.mock_render import MockRenderAdapter
from adapters.pose.mediapipe_adapter import MediapipeAdapter
from adapters.render.pygame_render_adapter import PygameRenderAdapter

# Estado compartido
from app.state import AppState

# configuración
from config.settings import Settings

# Puertos
from domain.ports.camera_port import CameraPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import RenderPort

# Casos de uso
from domain.use_cases.color_game import ColorGame
from domain.use_cases.particles_game import ParticlesGame

# Logger
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.logging.logger import get_logger

logger = get_logger("di")


class Container:
    """
    Contenedor de dependencias.

    Uso:
        container = Container(settings)
        game = container.create_game()
        game.run()
        container.shutdown()
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._camera: CameraPort | None = None
        self._pose_estimator: PoseEstimatorPort | None = None
        self._renderer: RenderPort | None = None
        self._state: AppState | None = None
        self._api: FastAPIAdapter | None = None
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
    def renderer(self) -> RenderPort:
        if self._renderer is None:
            self._renderer = self._create_renderer()
        return self._renderer

    @property
    def state(self) -> AppState:
        """Estado compartido (singleton dentro del contenedor)."""
        if self._state is None:
            self._state = AppState()
        return self._state

    @property
    def api(self) -> FastAPIAdapter | None:
        """Adaptador de API (solo si está habilitada)."""
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
        """Crea el adaptador de cámara según configuración."""
        cfg = self._settings.camera

        # En entorno de testing, siempre usar mock
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
                context={"camera_id": cfg.id}
            ) from e

    def _create_pose_estimator(self) -> PoseEstimatorPort:
        """Crea el adaptador de estimación de pose según configuración."""
        cfg = self._settings.pose

        if cfg.provider == "mock":
            logger.info("Usando MockPoseAdapter")
            return MockPoseAdapter()

        if cfg.provider == "mediapipe":
            logger.info(f"Usando MediapipeAdapter (complexity={cfg.model_complexity})")
            return MediapipeAdapter(
                min_detection_confidence=cfg.min_detection_confidence,
                min_tracking_confidence=cfg.min_tracking_confidence,
                model_complexity=cfg.model_complexity,
            )

        raise ConfigurationError(
            f"Proveedor de pose desconocido: {cfg.provider}",
            context={"provider": cfg.provider}
        )

    def _create_renderer(self) -> RenderPort:
        """Crea el adaptador de render según configuración."""
        cfg = self._settings.render

        if cfg.provider == "mock":
            logger.info("Usando MockRenderAdapter")
            return MockRenderAdapter()

        if cfg.provider == "pygame":
            logger.info(f"Usando PygameRenderAdapter ({cfg.width}x{cfg.height})")
            from domain.entities.color import RGBColor
            return PygameRenderAdapter(
                width=cfg.width,
                height=cfg.height,
                title=cfg.title,
                background_color=RGBColor(20, 20, 30),
            )

        raise ConfigurationError(
            f"Proveedor de render desconocido: {cfg.provider}",
            context={"provider": cfg.provider}
        )

    # ==========================================
    # Fábrica de casos de uso
    # ==========================================

    def create_game(self) -> ParticlesGame | ColorGame:
        """
        Crea el caso de uso según la configuración.

        Returns:
            Instancia del juego configurado (particles o color).
        """
        game_type = self._settings.game.type

        if game_type == "particles":
            logger.info("Creando ParticlesGame")
            return ParticlesGame(
                camera=self.camera,
                pose_estimator=self.pose_estimator,
                renderer=self.renderer,
                state=self.state,
                gravity=self._settings.game.gravity,
                burst_radius=50.0,
            )

        if game_type == "color":
            logger.info(f"Creando ColorGame (palette={self._settings.game.palette})")
            return ColorGame(
                camera=self.camera,
                pose_estimator=self.pose_estimator,
                renderer=self.renderer,
                state=self.state,
                palette_name=self._settings.game.palette,
            )

        raise ConfigurationError(
            f"Tipo de juego desconocido: {game_type}",
            context={"game_type": game_type}
        )

    # ==========================================
    # Ciclo de vida
    # ==========================================
    def start_api(self) -> None:
        """Inicia la API si está habilitada."""
        if self.api is not None:
            self.api.start()
            logger.info("API iniciada desde el contenedor")

    def shutdown(self) -> None:
        """Cierra todos los recursos creados."""
        logger.info("Cerrando contenedor DI...")

        if self._api is not None:
            try:
                self._api.stop()
            except Exception as e:
                logger.error(f"Error cerrando API: {e}")
            self._api = None

        if self._camera is not None:
            try:
                self._camera.stop()
            except cv2.error as e:
                logger.error(f"Error cerrando cámara: {e}")
            self._camera = None

        if self._pose_estimator is not None:
            try:
                self._pose_estimator.close()
            except cv2.error as e:
                logger.error(f"Error cerrando pose estimator: {e}")
            self._pose_estimator = None

        if self._renderer is not None:
            try:
                self._renderer.close()
            except cv2.error as e:
                logger.error(f"Error cerrando renderer: {e}")
            self._renderer = None

        logger.info("Contenedor DI cerrado")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()