"""
Plugin del juego Particles.

Vive en app/ (no en domain/) porque construye adaptadores concretos
(Pygame*). El dominio no debe conocer adapters.
"""

from app.game_context import GameContext
from domain.games.particles.main import ParticlesGame
from domain.games.particles.state import ParticlesState
from domain.plugins.game_plugin import GamePlugin, GameProtocol
from domain.ports.render.overlay_port import OverlayPort
from domain.state.game_state_port import GameStatePort
from infrastructure.logging.logger import get_logger

logger = get_logger("app.plugins.particles")


class ParticlesPlugin(GamePlugin):
    """Plugin que construye el juego Particles con arquitectura nueva."""

    @property
    def game_id(self) -> str:
        return "particles"

    @property
    def display_name(self) -> str:
        return "Particles Game"

    @property
    def description(self) -> str:
        return "Partículas que reaccionan a la pose humana."

    def create_state(self) -> GameStatePort:
        return ParticlesState()

    def create_game(self, context: GameContext) -> GameProtocol:
        """Construye el juego con SceneManager + capacidades + overlays."""
        from adapters.render.overlays.fps_overlay import FpsOverlay
        from adapters.render.overlays.pose_overlay import PoseOverlay
        from adapters.render.pygame_particles import PygameParticlesRenderer
        from adapters.render.pygame_scene import PygameSceneManager
        from domain.entities.color import RGBColor

        settings = context.settings
        render_cfg = settings.render
        game_cfg = settings.game

        particles_capability = PygameParticlesRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title=render_cfg.title,
            target_fps=render_cfg.target_fps,
            background_color=RGBColor(20, 20, 30),
        )
        # Initialize to access screen safely in non-interactive contexts if needed
        try:
            particles_capability._initialize()
        except Exception as e:
            logger.error(f"Error inicializando plugin renderer: {e}")

        overlays: list[OverlayPort] = []
        if getattr(render_cfg, "debug_overlay", False):
            overlays.append(PoseOverlay())
            overlays.append(FpsOverlay())

        scene = PygameSceneManager(
            surface=particles_capability.screen,
            capabilities=[particles_capability],
            overlays=overlays,
            target_fps=render_cfg.target_fps,
        )

        return ParticlesGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            state=ParticlesState(),
            event_bus=context.event_bus,
            renderer=None,
            scene=scene,
            particles_capability=particles_capability,
            gravity=game_cfg.gravity,
            burst_count=game_cfg.burst_count,
            max_particles=game_cfg.max_particles,
        )
