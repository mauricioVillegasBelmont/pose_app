"""
Test end-to-end del plugin de gestures.
"""

import pytest

from config.settings import Settings, reset_settings
from infrastructure.di.container import Container


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("POSE_PROVIDER", "mock")
    monkeypatch.setenv("RENDER_PROVIDER", "mock")
    monkeypatch.setenv("GAME_TYPE", "gestures")
    reset_settings()
    return Settings()


def test_gestures_plugin_registered():
    from app.plugin_registry import PluginRegistry
    from app.plugins import register_builtin_plugins

    registry = PluginRegistry()
    register_builtin_plugins(registry)

    assert "gestures" in registry.list_ids()
    plugin = registry.get_or_raise("gestures")
    assert plugin.display_name == "Gestures Game"


def test_gestures_container_creates_game(mock_settings):
    container = Container(mock_settings)
    game = container.create_game()

    assert game.state.game_id == "gestures"
    assert container.state_registry.get("gestures") is game.state


def test_gestures_initial_snapshot(mock_settings):
    container = Container(mock_settings)
    game = container.create_game()

    snapshot = game.state.snapshot()
    assert snapshot["active_gestures"] == []
    assert snapshot["frame_count"] == 0
