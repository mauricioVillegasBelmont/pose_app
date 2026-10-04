"""
Plugin del juego de color.
"""

from app.game_context import GameContext
from domain.games.color.main import ColorGame
from domain.games.color.state import ColorState
from domain.plugins.game_plugin import GamePlugin, GameProtocol
from domain.ports.render_port import ColorRenderPort
from domain.state.game_state_port import GameStatePort
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.logging.logger import get_logger

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
        palette_name = context.settings.game.palette
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

    def _create_renderer(self, context: GameContext):
        from adapters.render.pygame_base import PygameBaseAdapter

        cfg = context.settings.render

        base: ColorRenderPort
        if cfg.provider == "mock":
            from adapters.mock.mock_render import MockColorRenderAdapter

            base = MockColorRenderAdapter()
        elif cfg.provider == "pygame":
            from adapters.render.pygame_color_adapter import PygameColorAdapter

            base = PygameColorAdapter(
                width=cfg.width,
                height=cfg.height,
                title=cfg.title,
                target_fps=cfg.target_fps,
            )
        else:
            raise ConfigurationError(
                f"Proveedor de render desconocido: {cfg.provider}",
                context={"provider": cfg.provider, "plugin": self.game_id},
            )

        if cfg.debug_overlay and isinstance(base, PygameBaseAdapter):
            from adapters.render.decorators.pose_debug_overlay import (
                PoseDebugOverlay,
            )

            logger.info("Activando PoseDebugOverlay sobre Color")
            # TODO(refactor-render): ver nota en particles_plugin.py.
            return PoseDebugOverlay(base)  # type: ignore[arg-type]

        return base
