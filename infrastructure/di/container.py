"""
Contenedor DI.

Ahora:
- NO conoce juegos concretos (los delega al PluginRegistry).
- Construye SOLO dependencias compartidas (camera, pose, bus, registry).
- Carga plugins al inicio.
"""

import asyncio
from typing import Self

from adapters.api.fastapi_adapter import FastAPIAdapter
from adapters.camera.webcam_adapter import WebcamAdapter
from adapters.mock.mock_camera import MockCameraAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from adapters.pose.mediapipe_adapter import MediapipeAdapter
from app.game_context import GameContext
from app.plugin_registry import PluginRegistry
from app.plugins import register_builtin_plugins
from app.state_registry import StateRegistry
from config.settings import Settings
from domain.plugins.game_plugin import GameProtocol
from domain.ports.camera_port import CameraPort
from domain.ports.event_bus_port import EventBusPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.events.async_event_bus import AsyncEventBus
from infrastructure.logging.logger import get_logger

logger = get_logger("di")


class Container:
    """Contenedor de dependencias con plugin system."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._camera: CameraPort | None = None
        self._pose_estimator: PoseEstimatorPort | None = None
        self._event_bus: EventBusPort | None = None
        self._state_registry: StateRegistry | None = None
        self._plugin_registry: PluginRegistry | None = None
        self._api: FastAPIAdapter | None = None

    # ==========================================
    # Dependencias compartidas (lazy)
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
    def event_bus(self) -> EventBusPort:
        if self._event_bus is None:
            self._event_bus = AsyncEventBus()
        return self._event_bus

    @property
    def state_registry(self) -> StateRegistry:
        if self._state_registry is None:
            self._state_registry = StateRegistry()
        return self._state_registry

    @property
    def plugin_registry(self) -> PluginRegistry:
        """Registro de plugins (se auto-puebla con los builtin)."""
        if self._plugin_registry is None:
            self._plugin_registry = PluginRegistry()
            register_builtin_plugins(self._plugin_registry)
        return self._plugin_registry

    @property
    def api(self) -> FastAPIAdapter | None:
        """Adaptador de API (solo si está habilitada)."""
        if not self._settings.api.enabled:
            return None
        if self._api is None:
            self._api = FastAPIAdapter(
                settings=self._settings.api,
                event_bus=self.event_bus,
                registry=self.state_registry,
            )
        return self._api

    # ==========================================
    # Fábricas de adaptadores compartidos
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

    # ==========================================
    # Fábrica de juegos (delegada al plugin)
    # ==========================================

    def create_game(self) -> GameProtocol:
        """
        Crea el juego configurado usando el plugin correspondiente.

        Flujo:
            1. Obtiene el plugin del registro.
            2. Construye el GameContext con las dependencias compartidas.
            3. Delega en el plugin la creación del juego.
            4. Registra el estado del juego en el StateRegistry.
        """
        game_id = self._settings.game.type
        logger.info(f"Creando juego desde plugin: {game_id}")

        plugin = self.plugin_registry.get_or_raise(game_id)

        context = GameContext(
            camera=self.camera,
            pose_estimator=self.pose_estimator,
            event_bus=self.event_bus,
            settings=self._settings,
        )

        game = plugin.create_game(context)

        # Registra el estado del juego en el StateRegistry
        self.state_registry.register(game.state)
        logger.info(
            f"Estado del juego '{game.state.game_id}' registrado"
        )

        return game

    # ==========================================
    # Ciclo de vida
    # ==========================================

    async def shutdown(self) -> None:
        logger.info("Cerrando contenedor DI...")

        if self._api is not None:
            try:
                await self._api.shutdown()
            except Exception as e:
                logger.error(f"Error cerrando API: {e}")
            self._api = None

        if self._camera is not None:
            try:
                self._camera.stop()
            except Exception as e:
                logger.error(f"Error cerrando cámara: {e}")
            self._camera = None

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
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self.shutdown())
        except RuntimeError:
            asyncio.run(self.shutdown())