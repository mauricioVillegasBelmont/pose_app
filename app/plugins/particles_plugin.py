"""
Plugin del juego Particles.

Vive en app/ (no en domain/) porque construye adaptadores concretos
(Pygame*). El dominio no debe conocer adapters.
"""

from app.game_context import GameContext
from domain.games.particles.main import ParticlesGame
from domain.games.particles.state import ParticlesState
from domain.plugins.game_plugin import GamePlugin, GameProtocol
from domain.state.game_state_port import GameStatePort
from infrastructure.logging.logger import get_logger

logger = get_logger("app.plugins.particles_plugin")


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
        """Construye el juego con SceneManager + capacidades."""
        import pygame

        from adapters.render.pygame_color import PygameColorRenderer
        from adapters.render.pygame_hud import PygameHudRenderer
        from adapters.render.pygame_particles import PygameParticlesRenderer
        from adapters.render.pygame_scene import PygameSceneManager

        settings = context.settings
        render_cfg = settings.render
        # game_cfg = settings.game

        # 1. Capacidades (la primera crea la ventana)
        color_capability = PygameColorRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title=render_cfg.title,
            target_fps=render_cfg.target_fps,
        )
        color_capability._initialize()

        particles_capability = PygameParticlesRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title="Particles",
            target_fps=render_cfg.target_fps,
        )

        hud_capability = PygameHudRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title="HUD",
            target_fps=render_cfg.target_fps,
        )

        # 2. Overlays (debug)
        overlays: list = []
        if render_cfg.debug_overlay:
            from adapters.render.overlays.fps_overlay import FpsOverlay
            from adapters.render.overlays.pose_overlay import PoseOverlay

            overlays.append(PoseOverlay())
            overlays.append(FpsOverlay())

        # 3. SceneManager
        scene = PygameSceneManager(
            surface=color_capability.screen,
            capabilities=[
                color_capability,
                particles_capability,
                hud_capability,
            ],
            overlays=overlays,
            target_fps=render_cfg.target_fps,
        )

        pygame.display.set_caption("Particles Game")

        # 4. Juego
        return ParticlesGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            scene=scene,
            particles_capability=particles_capability,
            color_capability=color_capability,
            hud_capability=hud_capability,
            state=ParticlesState(),
            event_bus=context.event_bus,
            screen_width=render_cfg.width,
            screen_height=render_cfg.height,
        )
