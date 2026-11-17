"""
Test end-to-end del plugin de gestures.
"""

import pytest

from pose_app.config.game_profile import GameProfileConfig
from pose_app.config.settings import Settings, reset_settings
from pose_app.infrastructure.di.container import Container


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("POSE_PROVIDER", "mock")
    monkeypatch.setenv("RENDER_PROVIDER", "mock")
    monkeypatch.setenv("GAME_TYPE", "gestures")
    reset_settings()
    return Settings()


def test_gestures_plugin_registered():
    from pose_app.app.plugin_registry import PluginRegistry
    from pose_app.app.plugins import register_builtin_plugins

    registry = PluginRegistry()
    register_builtin_plugins(registry)

    assert "gestures" in registry.list_ids()
    plugin = registry.get_or_raise("gestures")
    assert plugin.display_name == "Gestures Game"


def test_gestures_container_creates_game(mock_settings) -> None:
    container = Container(mock_settings)
    gameplay_config = GameProfileConfig()
    game = container.create_game(gameplay_config=gameplay_config)

    assert game is not None
    assert game.state.game_id == "gestures"


def test_gestures_initial_snapshot(mock_settings) -> None:
    container = Container(mock_settings)
    gameplay_config = GameProfileConfig()
    game = container.create_game(gameplay_config=gameplay_config)

    snapshot = game.state.snapshot()
    assert "active_gestures" in snapshot
    assert "frame_count" in snapshot
