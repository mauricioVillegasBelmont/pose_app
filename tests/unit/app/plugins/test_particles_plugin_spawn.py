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
    def load_sprite_config(self, **kwargs: Any) -> None:
        return None


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
            "size": 32.0,
            "color": [255, 80, 0],
        },
        {
            "name": "ice",
            "weight": 1.0,
            "size": 16.0,
            "color": [0, 200, 255],
        },
    ]
    game = plugin.create_game(context_factory({"particle_archetypes": archetypes_data}))

    assert isinstance(game, ParticlesGame)
    assert [archetype.name for archetype in game._archetypes] == ["fire", "ice"]
    assert [archetype.weight for archetype in game._archetypes] == [3.0, 1.0]
    assert [archetype.size for archetype in game._archetypes] == [32.0, 16.0]
    assert [archetype.color for archetype in game._archetypes] == [
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
