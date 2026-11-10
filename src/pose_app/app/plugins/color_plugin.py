"""
Plugin del juego de color.
"""

from pose_app.app.game_context import GameContext
from pose_app.domain.games.color.main import ColorGame
from pose_app.domain.games.color.state import ColorState
from pose_app.domain.plugins.game_plugin import GamePlugin, GameProtocol
from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.domain.ports.render.scene_port import ScenePort
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
        """Construye el juego con SceneManager + capacidad de color.

        Args:
            context: dependencias compartidas y configuración del perfil.

        Returns:
            Instancia de ``ColorGame`` configurada desde el JSON.
        """
        scene, color_capability = self._create_scene(context)
        palette_name = context.gameplay_config.game_options.get("palette", "fire")
        state = ColorState(palette_name=palette_name)

        return ColorGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            scene=scene,
            color_capability=color_capability,
            state=state,
            event_bus=context.event_bus,
            palette_name=palette_name,
        )

    # ==========================================
    # Helpers privados
    # ==========================================

    def _create_scene(self, context: GameContext) -> tuple[ScenePort, ColorRenderPort]:
        """Construye la escena y la capacidad de color según el proveedor.

        Args:
            context: dependencias compartidas y configuración del perfil.

        Returns:
            Tupla ``(scene, color_capability)`` lista para el juego.

        Raises:
            ConfigurationError: Si el proveedor de render es desconocido.
        """
        cfg = context.settings.render

        if cfg.provider == "mock":
            from pose_app.adapters.mock.mock_render import (
                MockColorRenderAdapter,
                MockSceneManager,
            )

            color_capability: ColorRenderPort = MockColorRenderAdapter()
            scene: ScenePort = MockSceneManager(capabilities=[color_capability])
            return scene, color_capability

        if cfg.provider == "pygame":
            import pygame

            from pose_app.adapters.render.overlays.pose_overlay import PoseOverlay
            from pose_app.adapters.render.pygame_color import PygameColorRenderer
            from pose_app.adapters.render.pygame_scene import PygameSceneManager

            # Bootstrap de pygame: UNA sola ventana por proceso.
            pygame.init()
            window = pygame.display.set_mode(
                (cfg.width, cfg.height),
                pygame.RESIZABLE,
            )
            pygame.display.set_caption(cfg.title)

            color_capability = PygameColorRenderer(
                surface=window,
                target_fps=cfg.target_fps,
                title=cfg.title,
            )

            overlays: list[PoseOverlay] = []
            if cfg.debug_overlay:
                overlays.append(PoseOverlay(mirror=cfg.mirror))

            scene = PygameSceneManager(
                surface=window,
                capabilities=[color_capability],
                overlays=overlays,
                target_fps=cfg.target_fps,
            )
            return scene, color_capability

        raise ConfigurationError(
            f"Proveedor de render desconocido: {cfg.provider}",
            context={"provider": cfg.provider, "plugin": self.game_id},
        )
