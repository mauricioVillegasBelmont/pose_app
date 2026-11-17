"""Tests unitarios de la construcción de spawn en ParticlesPlugin."""

from collections.abc import Callable
from typing import Any
from unittest.mock import Mock

import pytest

from pose_app.app.game_context import GameContext
from pose_app.app.plugins.particles_plugin import ParticlesPlugin
from pose_app.config.game_profile import GameProfileConfig
from pose_app.config.settings import Settings
from pose_app.domain.entities.particles.spawn.positions import RandomPositionStrategy
from pose_app.domain.entities.particles.spawn.selectors import WeightedSelector
from pose_app.domain.entities.particles.spawn.strategies import ComposedSpawnStrategy
from pose_app.domain.games.particles.main import ParticlesGame
from pose_app.domain.ports.event_bus_port import EventBusPort
from pose_app.infrastructure.errors.exceptions import ConfigurationError


class _FakeColorRenderer:
    def __init__(self, **kwargs: Any) -> None:
        self.screen = object()

    def _initialize(self) -> None:
        pass


class _FakeParticlesRenderer:
    def __init__(self, **kwargs: Any) -> None:
        pass


class _FakeHudRenderer:
    def __init__(self, **kwargs: Any) -> None:
        pass


class _FakeSceneManager:
    def __init__(self, **kwargs: Any) -> None:
        pass


class _FakeAssetLoader:
    """Fake configurable de AssetLoader para tests de sprite_config."""

    # Controlado por el test via monkeypatch: si está seteado, load_sprite_config lo usa
    next_result: object = None
    next_exception: Exception | None = None

    def load_sprite_config(self, **kwargs: Any) -> Any:
        if _FakeAssetLoader.next_exception is not None:
            raise _FakeAssetLoader.next_exception
        return _FakeAssetLoader.next_result


@pytest.fixture(autouse=True)
def _reset_fake_asset_loader() -> None:
    """Resetea el estado del fake entre tests."""
    _FakeAssetLoader.next_result = None
    _FakeAssetLoader.next_exception = None


@pytest.fixture(autouse=True)
def _mock_native_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita abrir ventanas pygame durante los tests del plugin."""
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_color.PygameColorRenderer",
        _FakeColorRenderer,
    )
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_particles.PygameParticlesRenderer",
        _FakeParticlesRenderer,
    )
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_hud.PygameHudRenderer",
        _FakeHudRenderer,
    )
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_scene.PygameSceneManager",
        _FakeSceneManager,
    )
    monkeypatch.setattr(
        "pose_app.app.plugins.particles_plugin.AssetLoader",
        _FakeAssetLoader,
    )


@pytest.fixture
def settings() -> Settings:
    """Settings mínimos sin hardware ni variables externas."""
    return Settings(environment="testing")


@pytest.fixture
def context_factory(
    settings: Settings,
) -> Callable[[dict[str, Any] | None], GameContext]:
    """Crea GameContext con mocks y opciones de juego inyectables."""

    def _create(game_options: dict[str, Any] | None = None) -> GameContext:
        return GameContext(
            camera=Mock(),
            pose_estimator=Mock(),
            event_bus=Mock(spec=EventBusPort),
            settings=settings,
            gameplay_config=GameProfileConfig(game_options=game_options or {}),
        )

    return _create


@pytest.fixture
def plugin() -> ParticlesPlugin:
    """Plugin de partículas sin registro global."""
    return ParticlesPlugin()


def test_plugin_creates_game_with_default_archetypes(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """Sin archetypes en el JSON se usa el arquetipo por defecto."""
    game = plugin.create_game(context_factory())

    assert isinstance(game, ParticlesGame)
    assert len(game._archetypes) == 1
    assert game._archetypes[0].name == "default"


def test_plugin_creates_game_with_custom_archetypes(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """Los archetypes se construyen desde los datos del JSON."""
    archetypes_data = [
        {
            "name": "fire",
            "weight": 3.0,
            "appearance": {"size": 32.0, "color": [255, 80, 0]},
        },
        {
            "name": "ice",
            "weight": 1.0,
            "appearance": {"size": 16.0, "color": [0, 200, 255]},
        },
    ]
    game = plugin.create_game(context_factory({"particle_archetypes": archetypes_data}))

    assert isinstance(game, ParticlesGame)
    assert [archetype.name for archetype in game._archetypes] == ["fire", "ice"]
    assert [archetype.weight for archetype in game._archetypes] == [3.0, 1.0]
    assert [archetype.appearance.size for archetype in game._archetypes] == [32.0, 16.0]
    assert [archetype.appearance.color for archetype in game._archetypes] == [
        (255, 80, 0),
        (0, 200, 255),
    ]


def test_plugin_creates_weighted_strategy(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """El spawn_config construye WeightedSelector + RandomPositionStrategy."""
    game = plugin.create_game(
        context_factory(
            {
                "spawn_config": {
                    "archetype_selector": "weighted",
                    "position_strategy": "random",
                    "min_distance": 0.25,
                }
            }
        )
    )

    assert isinstance(game, ParticlesGame)
    strategy = game._spawn_strategy

    assert isinstance(strategy, ComposedSpawnStrategy)
    assert isinstance(strategy.archetype_selector, WeightedSelector)
    assert isinstance(strategy.position_strategy, RandomPositionStrategy)
    assert strategy.position_strategy.min_distance == 0.25


def test_plugin_raises_on_unknown_selector(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """Un archetype_selector desconocido lanza ConfigurationError."""
    context = context_factory(
        {
            "spawn_config": {
                "archetype_selector": "mystery",
            }
        }
    )

    with pytest.raises(ConfigurationError, match="Unknown archetype_selector"):
        plugin.create_game(context)


def test_plugin_raises_on_unknown_positioner(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """Un position_strategy desconocido lanza ConfigurationError."""
    context = context_factory(
        {
            "spawn_config": {
                "position_strategy": "mystery",
            }
        }
    )

    with pytest.raises(ConfigurationError, match="Unknown position_strategy"):
        plugin.create_game(context)


def test_plugin_builds_archetype_with_padding_from_json(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """El JSON puede declarar padding_x/padding_y en appearance."""
    archetypes_data = [
        {
            "name": "padded",
            "appearance": {
                "size": 20.0,
                "color": [255, 0, 0],
                "padding_x": 4.0,
                "padding_y": 6.0,
            },
        }
    ]
    game = plugin.create_game(context_factory({"particle_archetypes": archetypes_data}))

    arch = game._archetypes[0]
    assert arch.appearance.size == 20.0
    assert arch.appearance.padding_x == 4.0
    assert arch.appearance.padding_y == 6.0


class TestSpriteConfigFromJson:
    """sprite_config se lee por archetype desde el JSON (o None si no se declara)."""

    def test_build_archetypes_with_sprite_config_from_json(
        self,
        plugin: ParticlesPlugin,
        context_factory: Callable[[dict[str, Any] | None], GameContext],
    ) -> None:
        """Un archetype con sprite_config construye SpriteConfig via AssetLoader."""
        from pose_app.domain.entities.particles.components import SpriteConfig

        sprite = SpriteConfig(
            path="/abs/demo.png",
            frame_width=32,
            frame_height=32,
            frame_count=4,
            fps=12.0,
            animation_mode="loop",
        )
        _FakeAssetLoader.next_result = sprite
        _FakeAssetLoader.next_exception = None

        archetypes_data = [
            {
                "name": "bomb",
                "weight": 1.0,
                "appearance": {"size": 32.0, "color": [255, 100, 100]},
                "sprite_config": {
                    "sprite_name": "demo",
                    "fps": 12.0,
                    "animation_mode": "loop",
                },
            }
        ]
        game = plugin.create_game(
            context_factory({"particle_archetypes": archetypes_data})
        )

        arch = game._archetypes[0]
        assert arch.sprite_config is not None
        assert arch.sprite_config.path == "/abs/demo.png"
        assert arch.sprite_config.fps == 12.0
        assert arch.sprite_config.animation_mode == "loop"

    def test_build_archetypes_without_sprite_config_returns_none(
        self,
        plugin: ParticlesPlugin,
        context_factory: Callable[[dict[str, Any] | None], GameContext],
    ) -> None:
        """Sin sprite_config en el JSON, el archetype queda con None."""
        _FakeAssetLoader.next_result = None
        _FakeAssetLoader.next_exception = None

        archetypes_data = [
            {
                "name": "default",
                "weight": 1.0,
                "appearance": {"size": 20.0, "color": [255, 200, 50]},
            }
        ]
        game = plugin.create_game(
            context_factory({"particle_archetypes": archetypes_data})
        )

        assert game._archetypes[0].sprite_config is None

    def test_build_archetypes_with_invalid_sprite_name_raises(
        self,
        plugin: ParticlesPlugin,
        context_factory: Callable[[dict[str, Any] | None], GameContext],
    ) -> None:
        """Si AssetLoader falla, se envuelve en ConfigurationError con contexto."""
        _FakeAssetLoader.next_result = None
        _FakeAssetLoader.next_exception = ValueError("sprite not found")

        archetypes_data = [
            {
                "name": "bad",
                "appearance": {"size": 20.0, "color": [255, 0, 0]},
                "sprite_config": {"sprite_name": "nonexistent"},
            }
        ]
        with pytest.raises(ConfigurationError, match="Invalid sprite_config"):
            plugin.create_game(
                context_factory({"particle_archetypes": archetypes_data})
            )

    def test_build_archetypes_with_missing_sprite_name_raises(
        self,
        plugin: ParticlesPlugin,
        context_factory: Callable[[dict[str, Any] | None], GameContext],
    ) -> None:
        """sprite_config sin sprite_name lanza ConfigurationError."""
        _FakeAssetLoader.next_result = None
        _FakeAssetLoader.next_exception = None

        archetypes_data = [
            {
                "name": "bad",
                "appearance": {"size": 20.0, "color": [255, 0, 0]},
                "sprite_config": {"fps": 10.0},
            }
        ]
        with pytest.raises(ConfigurationError, match="sprite_name is required"):
            plugin.create_game(
                context_factory({"particle_archetypes": archetypes_data})
            )

    def test_build_archetypes_mixed_sprite_configs(
        self,
        plugin: ParticlesPlugin,
        context_factory: Callable[[dict[str, Any] | None], GameContext],
    ) -> None:
        """Unos archetypes con sprite, otros sin sprite, conviven."""
        from pose_app.domain.entities.particles.components import SpriteConfig

        sprite = SpriteConfig(
            path="/abs/demo.png",
            frame_width=32,
            frame_height=32,
            frame_count=4,
            fps=12.0,
            animation_mode="loop",
        )
        _FakeAssetLoader.next_result = sprite
        _FakeAssetLoader.next_exception = None

        archetypes_data = [
            {
                "name": "bomb",
                "appearance": {"size": 32.0, "color": [255, 0, 0]},
                "sprite_config": {"sprite_name": "demo"},
            },
            {
                "name": "coin",
                "appearance": {"size": 16.0, "color": [255, 255, 0]},
            },
        ]
        game = plugin.create_game(
            context_factory({"particle_archetypes": archetypes_data})
        )

        assert game._archetypes[0].sprite_config is not None
        assert game._archetypes[1].sprite_config is None

    def test_default_archetype_has_no_sprite_config(
        self,
        plugin: ParticlesPlugin,
        context_factory: Callable[[dict[str, Any] | None], GameContext],
    ) -> None:
        """Sin particle_archetypes en el JSON, el default no lleva sprite."""
        _FakeAssetLoader.next_result = None
        _FakeAssetLoader.next_exception = None

        game = plugin.create_game(context_factory())

        assert len(game._archetypes) == 1
        assert game._archetypes[0].name == "default"
        assert game._archetypes[0].sprite_config is None
