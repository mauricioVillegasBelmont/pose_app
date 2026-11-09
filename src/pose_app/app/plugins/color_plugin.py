"""
Plugin del juego de color.
"""

from pose_app.app.game_context import GameContext
from pose_app.domain.games.color.main import ColorGame
from pose_app.domain.games.color.state import ColorState
from pose_app.domain.plugins.game_plugin import GamePlugin, GameProtocol
from pose_app.domain.ports.render_port import ColorRenderPort
from pose_app.domain.state.game_state_port import GameStatePort
from pose_app.infrastructure.errors.exceptions import ConfigurationError
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("app.plugins.color")


class ColorPlugin(GamePlugin):
    """Plugin que construye el juego de color."""

    @property
    def game_id(self) -> str:
        return "color"

    @property
    def display_name(self) -> str:
        return "Color Game"

    @property
    def description(self) -> str:
        return "Cambia el color de fondo según la posición de la pose."

    def create_state(self) -> GameStatePort:
        return ColorState()

    def create_game(self, context: GameContext) -> GameProtocol:
        renderer = self._create_renderer(context)
        palette_name = context.gameplay_config.game_options.get("palette", "fire")
        state = ColorState(palette_name=palette_name)

        return ColorGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            renderer=renderer,
            state=state,
            event_bus=context.event_bus,
            palette_name=palette_name,
        )

    # ==========================================
    # Helpers privados
    # ==========================================

    def _create_renderer(self, context: GameContext) -> ColorRenderPort:
        cfg = context.settings.render

        if cfg.debug_overlay:
            # NOTE(refactor-render): PoseDebugOverlay fue eliminado en favor
            # de OverlayPort (PoseOverlay) en la nueva arquitectura. ColorPlugin
            # es legacy: el overlay se habilitará cuando migre al SceneManager
            # (Fase 4). Mientras tanto se ignora con warning.
            logger.warning(
                "RENDER_DEBUG_OVERLAY=true ignorado en ColorPlugin (legacy). "
                "El overlay solo está disponible para el juego 'particles' "
                "hasta la migración de ColorPlugin a la nueva arquitectura."
            )

        if cfg.provider == "mock":
            from pose_app.adapters.mock.mock_render import MockColorRenderAdapter

            return MockColorRenderAdapter()

        if cfg.provider == "pygame":
            import pygame

            from pose_app.adapters.render.pygame_color_adapter import (
                PygameColorAdapter,
            )

            # NOTE(refactor-render): bootstrap mínimo de pygame para no romper
            # el arranque del juego 'color' hasta su migración completa a
            # SceneManager (Fase 4). NO es el patrón canónico: ver
            # ParticlesPlugin para el bootstrap correcto (centralizado, con
            # SceneManager dueño del ciclo de vida).
            pygame.init()
            surface = pygame.display.get_surface()
            if surface is None:
                surface = pygame.display.set_mode(
                    (cfg.width, cfg.height),
                    pygame.RESIZABLE,
                )
                pygame.display.set_caption(cfg.title)

            return PygameColorAdapter(
                surface=surface,
                title=cfg.title,
                target_fps=cfg.target_fps,
            )

        raise ConfigurationError(
            f"Proveedor de render desconocido: {cfg.provider}",
            context={"provider": cfg.provider, "plugin": self.game_id},
        )
