"""
Plugin del juego Particles.

Vive en app/ (no en domain/) porque construye adaptadores concretos
(Pygame*). El dominio no debe conocer adapters.
"""

from typing import Any

from pose_app.adapters.render.pygame_input_cursor import PygameInputCursorRenderer
from pose_app.app.game_context import GameContext
from pose_app.domain.entities.hand_landmark_config import HandLandmarkConfig
from pose_app.domain.entities.input_cursor import (
    CursorAppearance,
    CursorCollision,
    InputCursor,
)
from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.components import Appearance, SpriteConfig
from pose_app.domain.entities.particles.spawn.ports import (
    ArchetypeSelector,
    PositionStrategy,
)
from pose_app.domain.entities.particles.spawn.positions import RandomPositionStrategy
from pose_app.domain.entities.particles.spawn.selectors import WeightedSelector
from pose_app.domain.entities.particles.spawn.strategies import ComposedSpawnStrategy
from pose_app.domain.games.particles.main import ParticlesGame
from pose_app.domain.games.particles.state import ParticlesState
from pose_app.domain.plugins.game_plugin import GamePlugin, GameProtocol
from pose_app.domain.services.pose_interaction_facade import PoseInteractionFacade
from pose_app.domain.state.game_state_port import GameStatePort
from pose_app.infrastructure.assets.asset_loader import AssetLoader
from pose_app.infrastructure.errors.exceptions import ConfigurationError
from pose_app.infrastructure.logging.logger import get_logger

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
        """Construye el juego con SceneManager + capacidades + overlays.

        Args:
            context: dependencias compartidas y configuración del perfil.

        Returns:
            Instancia de ``ParticlesGame`` configurada desde el JSON.

        Raises:
            ConfigurationError: Si la configuración de spawn es inválida o
                usa estrategias desconocidas.
        """
        from pose_app.adapters.render.pygame_color import PygameColorRenderer
        from pose_app.adapters.render.pygame_hud import PygameHudRenderer
        from pose_app.adapters.render.pygame_particles import PygameParticlesRenderer
        from pose_app.adapters.render.pygame_scene import PygameSceneManager

        settings = context.settings
        render_cfg = settings.render
        _pose_cfg = settings.pose

        profile_config = context.gameplay_config
        opts = profile_config.game_options
        extra_config = profile_config.model_extra or {}

        raw_archetypes = extra_config.get(
            "particle_archetypes",
            opts.get("particle_archetypes"),
        )
        raw_spawn_config = extra_config.get(
            "spawn_config",
            opts.get("spawn_config"),
        )

        # ==========================================
        # Construir cursores de interacción
        # ==========================================
        raw_cursors = opts.get("cursors")
        cursor_timeout = float(opts.get("cursor_timeout", 2.0))
        cursor_configs, cursors = self._build_cursors(raw_cursors, opts)

        # Reconstruir pose_interaction con cursor_configs
        pose_interaction = PoseInteractionFacade(
            smoothing_factor=profile_config.pose_smoothing_factor,
            hand_timeout=cursor_timeout,
            cursor_configs=cursor_configs,
            cursors=cursors,
        )

        asset_loader = AssetLoader()
        sprite_config = asset_loader.load_sprite_config(
            category="particles",
            sprite_name="demo",
            fps=12.0,
            animation_mode="loop",
        )

        archetypes = self._build_archetypes(
            raw_archetypes,
            opts,
            sprite_config,
        )
        spawn_strategy = self._build_spawn_strategy(raw_spawn_config, opts)

        # Leer mirror del config
        mirror = render_cfg.mirror

        # 1. Capacidades
        color_capability = PygameColorRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title=render_cfg.title,
            target_fps=render_cfg.target_fps,
            # color NO se espeja
        )
        color_capability._initialize()

        cursor_capability = PygameInputCursorRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title="cursors",
            target_fps=render_cfg.target_fps,
            mirror=mirror,
        )
        cursor_capability.set_cursors(cursors)

        particles_capability = PygameParticlesRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title="Particles",
            target_fps=render_cfg.target_fps,
            mirror=mirror,  # ← AÑADIR
        )

        hud_capability = PygameHudRenderer(
            width=render_cfg.width,
            height=render_cfg.height,
            title="HUD",
            target_fps=render_cfg.target_fps,
            # HUD NO se espeja
        )

        # 2. Overlays
        overlays: list = []
        if render_cfg.debug_overlay:
            from pose_app.adapters.render.overlays.fps_overlay import FpsOverlay
            from pose_app.adapters.render.overlays.pose_overlay import PoseOverlay

            overlays.append(
                PoseOverlay(mirror=mirror)  # ← AÑADIR
            )
            overlays.append(
                FpsOverlay()
                # FPS NO se espeja
            )

        # 3. SceneManager
        scene = PygameSceneManager(
            surface=color_capability.screen,
            capabilities=[
                color_capability,
                particles_capability,
                cursor_capability,
                hud_capability,
            ],
            overlays=overlays,
            target_fps=render_cfg.target_fps,
        )

        # 4. Juego
        return ParticlesGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            pose_interaction=pose_interaction,
            scene=scene,
            particles_capability=particles_capability,
            color_capability=color_capability,
            hud_capability=hud_capability,
            state=ParticlesState(),
            event_bus=context.event_bus,
            spawn_strategy=spawn_strategy,
            archetypes=archetypes,
            screen_width=render_cfg.width,
            screen_height=render_cfg.height,
            max_score=opts.get("max_score", 10),
            time_per_round=opts.get("time_per_round", 10.0),
            hit_radius=opts.get("hit_radius", 30.0),
            cursors=cursors,
        )

    def _build_archetypes(
        self,
        raw_archetypes: Any,
        opts: dict[str, Any],
        sprite_config: SpriteConfig | None,
    ) -> list[ParticleArchetype]:
        """Construye los arquetipos declarados en la configuración JSON.

        Args:
            raw_archetypes: Lista de arquetipos en bruto o ``None`` para usar
                el arquetipo por defecto.
            opts: Opciones del juego usadas como fallback.
            sprite_config: Configuración de sprite compartida por arquetipos.

        Returns:
            Lista de ``ParticleArchetype`` validados.

        Raises:
            ConfigurationError: Si la sección no es una lista o algún
                arquetipo contiene valores inválidos.
        """
        if raw_archetypes is None or raw_archetypes == []:
            return [self._default_archetype(opts, sprite_config)]

        if not isinstance(raw_archetypes, list):
            raise ConfigurationError(
                "particle_archetypes must be a list",
                context={"type": type(raw_archetypes).__name__},
            )

        archetypes: list[ParticleArchetype] = []
        for index, item in enumerate(raw_archetypes):
            if not isinstance(item, dict):
                raise ConfigurationError(
                    f"particle_archetypes[{index}] must be an object",
                    context={"index": index},
                )

            try:
                name = item.get("name", f"archetype_{index}")
                if not isinstance(name, str) or not name:
                    raise ValueError("name must be a non-empty string")

                weight = float(item.get("weight", 1.0))
                appearance = self._parse_appearance(item.get("appearance"), index)

                archetypes.append(
                    ParticleArchetype(
                        name=name,
                        weight=weight,
                        appearance=appearance,
                        sprite_config=sprite_config,
                    )
                )
            except (TypeError, ValueError) as e:
                raise ConfigurationError(
                    f"Invalid particle archetype at index {index}: {e}",
                    context={"index": index},
                ) from e

        return archetypes

    def _default_archetype(
        self,
        opts: dict[str, Any],
        sprite_config: SpriteConfig | None,
    ) -> ParticleArchetype:
        """Crea el arquetipo por defecto a partir de las opciones del juego.

        Args:
            opts: Opciones del juego con posibles ``particle_size`` y
                ``particle_color``.
            sprite_config: Configuración de sprite compartida.

        Returns:
            Arquetipo por defecto validado.

        Raises:
            ConfigurationError: Si el tamaño o color por defecto son inválidos.
        """
        try:
            size = float(opts.get("particle_size", 20.0))
            color = self._parse_color(opts.get("particle_color", [255, 200, 50]))
            appearance = Appearance(size=size, color=color)
        except (TypeError, ValueError) as e:
            raise ConfigurationError(
                "Invalid default particle archetype configuration",
                context={"error": str(e)},
            ) from e

        return ParticleArchetype(
            name="default",
            appearance=appearance,
            sprite_config=sprite_config,
        )

    def _parse_appearance(
        self,
        raw_appearance: Any,
        index: int,
    ) -> Appearance:
        """Parsea el bloque ``appearance`` de un arquetipo del JSON.

        Args:
            raw_appearance: Bloque appearance en bruto o ``None`` para defaults.
            index: Índice del arquetipo (para contexto de error).

        Returns:
            ``Appearance`` validado.

        Raises:
            ConfigurationError: Si el bloque es inválido.
        """
        if raw_appearance is None:
            return Appearance()

        if not isinstance(raw_appearance, dict):
            raise ConfigurationError(
                f"particle_archetypes[{index}].appearance must be an object",
                context={"index": index},
            )

        try:
            size = float(raw_appearance.get("size", 20.0))
            color = self._parse_color(raw_appearance.get("color", [255, 200, 50]))
            padding_x = float(raw_appearance.get("padding_x", 0.0))
            padding_y = float(raw_appearance.get("padding_y", 0.0))

            return Appearance(
                size=size,
                color=color,
                padding_x=padding_x,
                padding_y=padding_y,
            )
        except (TypeError, ValueError) as e:
            raise ConfigurationError(
                f"Invalid appearance for archetype {index}: {e}",
                context={"index": index},
            ) from e

    def _build_spawn_strategy(
        self,
        raw_spawn_config: Any,
        opts: dict[str, Any],
    ) -> ComposedSpawnStrategy:
        """Construye la estrategia compuesta a partir del JSON.

        Args:
            raw_spawn_config: Configuración de spawn en bruto o ``None``.
            opts: Opciones del juego usadas como fallback.

        Returns:
            Estrategia compuesta configurada.

        Raises:
            ConfigurationError: Si la sección es inválida o declara
                estrategias desconocidas.
        """
        if raw_spawn_config is None:
            raw_spawn_config = {}

        if not isinstance(raw_spawn_config, dict):
            raise ConfigurationError(
                "spawn_config must be an object",
                context={"type": type(raw_spawn_config).__name__},
            )

        selector_name = raw_spawn_config.get("archetype_selector", "weighted")
        position_name = raw_spawn_config.get("position_strategy", "random")

        if not isinstance(selector_name, str):
            raise ConfigurationError("archetype_selector must be a string")

        if selector_name != "weighted":
            raise ConfigurationError(
                f"Unknown archetype_selector: '{selector_name}'. "
                "Supported values: weighted",
                context={"archetype_selector": selector_name},
            )

        if not isinstance(position_name, str):
            raise ConfigurationError("position_strategy must be a string")

        if position_name != "random":
            raise ConfigurationError(
                f"Unknown position_strategy: '{position_name}'. "
                "Supported values: random",
                context={"position_strategy": position_name},
            )

        try:
            min_distance = float(
                raw_spawn_config.get(
                    "min_distance",
                    opts.get("particle_min_distance", 0.15),
                )
            )
        except (TypeError, ValueError) as e:
            raise ConfigurationError(
                "Invalid spawn_config.min_distance",
                context={"error": str(e)},
            ) from e

        if min_distance < 0:
            raise ConfigurationError(
                "spawn_config.min_distance must be non-negative",
                context={"min_distance": min_distance},
            )

        selector: ArchetypeSelector = WeightedSelector()
        position_strategy: PositionStrategy = RandomPositionStrategy(
            min_distance=min_distance,
        )

        return ComposedSpawnStrategy(
            archetype_selector=selector,
            position_strategy=position_strategy,
        )

    def _build_cursors(
        self,
        raw_cursors: Any,
        opts: dict[str, Any],
    ) -> tuple[dict[str, HandLandmarkConfig], list[InputCursor]]:
        """Construye cursores de interacción desde la configuración JSON.

        Args:
            raw_cursors: Diccionario de cursores en bruto desde el JSON.
            opts: Opciones del juego (fallback para defaults).

        Returns:
            Tupla (cursor_configs, cursors) donde:
            - cursor_configs: dict[str, HandLandmarkConfig] para la fachada
            - cursors: list[InputCursor] con configuración visual y de colisión

        Raises:
            ConfigurationError: Si la configuración es inválida.
        """
        if raw_cursors is None or not isinstance(raw_cursors, dict):
            # Defaults: left_hand y right_hand con wrist único
            default_config = HandLandmarkConfig(
                landmark_names=("left_wrist",),
            )
            default_cursor = InputCursor(cursor_id="left_hand")
            return (
                {
                    "left_hand": default_config,
                    "right_hand": HandLandmarkConfig(landmark_names=("right_wrist",)),
                },
                [default_cursor, InputCursor(cursor_id="right_hand")],
            )

        cursor_configs: dict[str, HandLandmarkConfig] = {}
        cursors: list[InputCursor] = []

        for cursor_id, cursor_data in raw_cursors.items():
            if not isinstance(cursor_data, dict):
                raise ConfigurationError(
                    f"Cursor '{cursor_id}' must be an object",
                    context={"cursor_id": cursor_id},
                )

            try:
                # 1. Construir HandLandmarkConfig
                landmark_names = tuple(
                    cursor_data.get("landmark_names", [f"{cursor_id}_wrist"])
                )
                offset_x = float(cursor_data.get("offset_x", 0.0))
                offset_y = float(cursor_data.get("offset_y", 0.0))

                hand_config = HandLandmarkConfig(
                    landmark_names=landmark_names,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )
                cursor_configs[cursor_id] = hand_config

                # 2. Construir CursorAppearance
                appearance_data = cursor_data.get("appearance", {})
                appearance = CursorAppearance(
                    size=float(appearance_data.get("size", 40.0)),
                    color=tuple(appearance_data.get("color", [255, 255, 0])),
                    padding_x=float(appearance_data.get("padding_x", 0.0)),
                    padding_y=float(appearance_data.get("padding_y", 0.0)),
                )

                # 3. Construir CursorCollision
                collision_data = cursor_data.get("collision", {})
                collision = CursorCollision(
                    radius=float(collision_data.get("radius", 5.0)),
                )

                # 4. Construir InputCursor
                cursor = InputCursor(
                    cursor_id=cursor_id,
                    appearance=appearance,
                    collision=collision,
                )
                cursors.append(cursor)

            except (TypeError, ValueError) as e:
                raise ConfigurationError(
                    f"Invalid cursor configuration for '{cursor_id}': {e}",
                    context={"cursor_id": cursor_id},
                ) from e

        return cursor_configs, cursors

    @staticmethod
    def _parse_color(raw_color: Any) -> tuple[int, int, int]:
        """Convierte un color JSON en una tupla RGB validada.

        Args:
            raw_color: Valor en bruto proveniente del JSON.

        Returns:
            Tupla ``(r, g, b)``.

        Raises:
            ValueError: Si el valor no es una secuencia de 3 enteros.
        """
        if not isinstance(raw_color, (list, tuple)) or len(raw_color) != 3:
            raise ValueError("color must be a list or tuple of 3 integers")

        if any(not isinstance(component, int) for component in raw_color):
            raise ValueError("color components must be integers")

        return (int(raw_color[0]), int(raw_color[1]), int(raw_color[2]))
