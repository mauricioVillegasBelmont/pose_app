"""
Tests de los plugins builtin.
"""

from pose_app.app.plugin_registry import PluginRegistry
from pose_app.app.plugins import register_builtin_plugins


def test_builtin_plugins_register():
    registry = PluginRegistry()
    register_builtin_plugins(registry)

    ids = registry.list_ids()
    assert "particles" in ids
    assert "color" in ids


def test_particles_plugin_metadata():
    registry = PluginRegistry()
    register_builtin_plugins(registry)

    plugin = registry.get_or_raise("particles")
    assert plugin.game_id == "particles"
    assert plugin.display_name == "Particles Game"
    assert plugin.description != ""


def test_color_plugin_metadata():
    registry = PluginRegistry()
    register_builtin_plugins(registry)

    plugin = registry.get_or_raise("color")
    assert plugin.game_id == "color"
    assert plugin.display_name == "Color Game"
    assert plugin.description != ""


def test_particles_plugin_creates_state():
    registry = PluginRegistry()
    register_builtin_plugins(registry)

    plugin = registry.get_or_raise("particles")
    state = plugin.create_state()

    assert state.game_id == "particles"
    assert state.snapshot()["particles_count"] == 0


def test_color_plugin_creates_state():
    registry = PluginRegistry()
    register_builtin_plugins(registry)

    plugin = registry.get_or_raise("color")
    state = plugin.create_state()

    assert state.game_id == "color"
    snapshot = state.snapshot()
    assert "background_color" in snapshot
    assert "current_palette" in snapshot
