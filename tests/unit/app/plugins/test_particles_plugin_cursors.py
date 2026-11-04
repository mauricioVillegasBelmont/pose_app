"""
Tests de integración para cursores de interacción en ParticlesPlugin.
Validan que el plugin construye correctamente los cursores desde el JSON.
"""

from collections.abc import Callable
from typing import Any
from unittest.mock import Mock

import pytest

from pose_app.app.game_context import GameContext
from pose_app.app.plugins.particles_plugin import ParticlesPlugin
from pose_app.config.game_profile import GameProfileConfig
from pose_app.config.settings import Settings
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
        self._capabilities = list(kwargs.get("capabilities", []))


class _FakeAssetLoader:
    def load_sprite_config(self, **kwargs: Any) -> None:
        return None


class _FakeInputCursorRenderer:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._cursors: list[Any] = []

    def set_cursors(self, cursors: list[Any]) -> None:
        self._cursors = cursors


@pytest.fixture(autouse=True)
def _mock_native_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita abrir ventanas pygame durante los tests."""
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
    monkeypatch.setattr(
        "pose_app.app.plugins.particles_plugin.PygameInputCursorRenderer",
        _FakeInputCursorRenderer,
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="testing")


@pytest.fixture
def context_factory(
    settings: Settings,
) -> Callable[[dict[str, Any] | None], GameContext]:
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
    return ParticlesPlugin()


def test_plugin_creates_default_cursors_when_not_configured(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """Sin configuración de cursores, se usan defaults (left_hand, right_hand)."""
    game = plugin.create_game(context_factory())

    # El juego debe tener pose_interaction con cursores
    assert hasattr(game, "_pose_interaction")
    cursors = game._pose_interaction.get_all_cursors()
    assert len(cursors) == 2
    assert any(c.cursor_id == "left_hand" for c in cursors)
    assert any(c.cursor_id == "right_hand" for c in cursors)


def test_plugin_creates_custom_cursors_from_json(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """Los cursores se construyen desde el JSON."""
    cursors_config = {
        "left_hand": {
            "landmark_names": ["left_wrist", "left_index"],
            "offset_x": 0.02,
            "offset_y": -0.03,
            "appearance": {"size": 50.0, "color": [255, 0, 0]},
            "collision": {"radius": 10.0},
        },
        "feet": {
            "landmark_names": ["left_ankle", "right_ankle"],
            "appearance": {"size": 30.0, "color": [0, 255, 0]},
            "collision": {"radius": 8.0},
        },
    }

    game = plugin.create_game(context_factory({"cursors": cursors_config}))

    cursors = game._pose_interaction.get_all_cursors()
    assert len(cursors) == 2
    assert any(c.cursor_id == "left_hand" for c in cursors)
    assert any(c.cursor_id == "feet" for c in cursors)

    # Verificar configuración del cursor left_hand
    left_hand = next(c for c in cursors if c.cursor_id == "left_hand")
    assert left_hand.appearance.size == 50.0
    assert left_hand.appearance.color == (255, 0, 0)
    assert left_hand.collision.radius == 10.0


def test_plugin_applies_cursor_timeout(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """El timeout de cursores se lee del JSON."""
    game = plugin.create_game(context_factory({"cursor_timeout": 3.0}))

    # Verificar que el timeout se aplicó a la fachada
    assert hasattr(game._pose_interaction, "_hand_timeout")
    assert game._pose_interaction._hand_timeout == 3.0


def test_plugin_raises_on_invalid_cursor_config(
    plugin: ParticlesPlugin,
    context_factory: Callable[[dict[str, Any] | None], GameContext],
) -> None:
    """Configuración inválida de cursor lanza ConfigurationError."""
    invalid_config = {
        "left_hand": "not_a_dict",  # Debe ser un dict
    }

    with pytest.raises(ConfigurationError, match="must be an object"):
        plugin.create_game(context_factory({"cursors": invalid_config}))
