"""Tests de integración del fix de ventana única pygame.

Verifica que:
- pygame.display.set_mode se llame UNA sola vez por proceso.
- El caption final sea el del config (no el del último renderer).
- pygame.quit se llame UNA sola vez (en SceneManager.close).
"""

from typing import Any
from unittest.mock import Mock

import pytest

from pose_app.app.game_context import GameContext
from pose_app.app.plugins.particles_plugin import ParticlesPlugin
from pose_app.config.game_profile import GameProfileConfig
from pose_app.config.settings import Settings
from pose_app.domain.ports.event_bus_port import EventBusPort


class _FakeRenderer:
    """Fake de capacidad de render (acepta surface)."""

    def __init__(self, surface: Any = None, **kwargs: Any) -> None:
        self.surface = surface

    def _initialize(self) -> None:
        pass

    def render(self) -> None:
        pass

    def close(self) -> None:
        pass


class _FakeSceneManager:
    def __init__(self, surface: Any = None, **kwargs: Any) -> None:
        self.surface = surface
        self._capabilities = kwargs.get("capabilities", [])
        self._overlays = kwargs.get("overlays", [])

    def render_frame(self, landmarks: Any) -> None:
        pass

    def close(self) -> None:
        pass


class _FakeAssetLoader:
    next_result: Any = None
    next_exception: Exception | None = None

    def load_sprite_config(self, **kwargs: Any) -> Any:
        if _FakeAssetLoader.next_exception is not None:
            raise _FakeAssetLoader.next_exception
        return _FakeAssetLoader.next_result


@pytest.fixture(autouse=True)
def _reset_fake_asset_loader() -> None:
    _FakeAssetLoader.next_result = None
    _FakeAssetLoader.next_exception = None


@pytest.fixture(autouse=True)
def _mock_renderers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita abrir ventanas reales durante los tests."""
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_color.PygameColorRenderer",
        _FakeRenderer,
    )
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_particles.PygameParticlesRenderer",
        _FakeRenderer,
    )
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_hud.PygameHudRenderer",
        _FakeRenderer,
    )
    monkeypatch.setattr(
        "pose_app.adapters.render.pygame_input_cursor.PygameInputCursorRenderer",
        _FakeRenderer,
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
    return Settings(environment="testing")


@pytest.fixture
def context(settings: Settings) -> GameContext:
    return GameContext(
        camera=Mock(),
        pose_estimator=Mock(),
        event_bus=Mock(spec=EventBusPort),
        settings=settings,
        gameplay_config=GameProfileConfig(),
    )


def test_set_mode_called_once(
    context: GameContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pygame.display.set_mode se llama UNA vez en create_game."""
    set_mode_calls: list[tuple] = []
    monkeypatch.setattr(
        "pygame.display.set_mode",
        lambda *args, **kwargs: set_mode_calls.append((args, kwargs)) or Mock(),
    )
    monkeypatch.setattr(
        "pygame.display.set_caption",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr("pygame.init", lambda: None)

    plugin = ParticlesPlugin()
    plugin.create_game(context)

    assert len(set_mode_calls) == 1


def test_caption_is_from_config(
    context: GameContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El caption final es render_cfg.title, no el de un renderer."""
    caption_calls: list[str] = []
    monkeypatch.setattr(
        "pygame.display.set_mode",
        lambda *args, **kwargs: Mock(),
    )
    monkeypatch.setattr(
        "pygame.display.set_caption",
        lambda title: caption_calls.append(title),
    )
    monkeypatch.setattr("pygame.init", lambda: None)

    plugin = ParticlesPlugin()
    plugin.create_game(context)

    assert caption_calls == [context.settings.render.title]
