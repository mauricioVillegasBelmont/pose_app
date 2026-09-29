"""
Plugin del juego de partículas.
"""

from app.game_context import GameContext
from domain.games.particles.state import ParticlesState
from domain.plugins.game_plugin import GamePlugin, GameProtocol
from domain.state.game_state_port import GameStatePort
from domain.use_cases.particles_game import ParticlesGame
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.logging.logger import get_logger

logger = get_logger("app.plugins.particles")


class ParticlesPlugin(GamePlugin):
    """Plugin que construye el juego de partículas."""

    @property
    def game_id(self) -> str:
        return "particles"

    @property
    def display_name(self) -> str:
        return "Particles Game"

    @property
    def description(self) -> str:
        return "Emite partículas desde los landmarks visibles de la pose."

    def create_state(self) -> GameStatePort:
        return ParticlesState()

    def create_game(self, context: GameContext) -> GameProtocol:
        """Construye el ParticlesGame con las dependencias del contexto."""
        renderer = self._create_renderer(context)
        state = ParticlesState()

        return ParticlesGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            renderer=renderer,
            state=state,
            event_bus=context.event_bus,
            gravity=context.settings.game.gravity,
            burst_count=context.settings.game.burst_count,
            max_particles=context.settings.game.max_particles,
        )

    # ==========================================
    # Helpers privados
    # ==========================================

    def _create_renderer(self, context: GameContext):
        """Crea el renderer específico del juego de partículas."""
        from adapters.render.pygame_base import PygameBaseAdapter
        cfg = context.settings.render

        if cfg.provider == "mock":
            from adapters.mock.mock_render import MockParticlesRenderAdapter
            base = MockParticlesRenderAdapter()
        elif cfg.provider == "pygame":
            from adapters.render.pygame_particles_adapter import (
                PygameParticlesAdapter,
            )
            from domain.entities.color import RGBColor
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
                context={"provider": cfg.provider, "plugin": self.game_id},
            )

        # Decorador de debug (opcional, solo aplica a Pygame)
        if cfg.debug_overlay and isinstance(base, PygameBaseAdapter):
            from adapters.render.decorators.pose_debug_overlay import (
                PoseDebugOverlay,
            )
            logger.info("Activando PoseDebugOverlay sobre Particles")
            return PoseDebugOverlay(base)

        return base