"""
Plugin del juego de gestures.
"""

from app.game_context import GameContext
from domain.games.gestures.main import GesturesGame
from domain.games.gestures.state import GesturesState
from domain.plugins.game_plugin import GamePlugin, GameProtocol
from domain.state.game_state_port import GameStatePort
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.logging.logger import get_logger

logger = get_logger("app.plugins.gestures")


class GesturesPlugin(GamePlugin):
    """Plugin que construye el juego de reconocimiento de gestos."""

    @property
    def game_id(self) -> str:
        return "gestures"

    @property
    def display_name(self) -> str:
        return "Gestures Game"

    @property
    def description(self) -> str:
        return (
            "Reconoce 6 gestos: mano arriba, saludo, brazos cruzados, "
            "pose T, cuclillas, equilibrio en un pie."
        )

    def create_state(self) -> GameStatePort:
        return GesturesState()

    def create_game(self, context: GameContext) -> GameProtocol:
        renderer = self._create_renderer(context)
        state = GesturesState()

        return GesturesGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            renderer=renderer,
            state=state,
            event_bus=context.event_bus,
        )

    def _create_renderer(self, context: GameContext):
        cfg = context.settings.render

        if cfg.provider == "mock":
            from adapters.mock.mock_render import MockColorRenderAdapter

            return MockColorRenderAdapter()

        if cfg.provider == "pygame":
            from adapters.render.pygame_color_adapter import PygameColorAdapter

            return PygameColorAdapter(
                width=cfg.width,
                height=cfg.height,
                title="Gestures Game",
                target_fps=cfg.target_fps,
            )

        raise ConfigurationError(
            f"Proveedor de render desconocido: {cfg.provider}",
            context={"provider": cfg.provider, "plugin": self.game_id},
        )
