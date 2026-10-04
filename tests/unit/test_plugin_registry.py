"""
Tests del PluginRegistry.
"""

import pytest

from app.plugin_registry import PluginRegistry
from domain.plugins.game_plugin import GamePlugin, GameProtocol
from domain.state.game_state_port import GameStatePort
from infrastructure.errors.exceptions import ConfigurationError


# ==========================================
# Fakes para testing
# ==========================================


class _FakeState(GameStatePort):
    @property
    def game_id(self) -> str:
        return "fake"

    def snapshot(self) -> dict:
        return {"fake": True}

    def stats(self) -> dict:
        return {}


class _FakePlugin(GamePlugin):
    @property
    def game_id(self) -> str:
        return "fake"

    @property
    def display_name(self) -> str:
        return "Fake Game"

    def create_state(self) -> GameStatePort:
        return _FakeState()

    def create_game(self, context) -> GameProtocol:
        raise NotImplementedError("Not needed in this test")


# ==========================================
# Tests
# ==========================================


def test_register_and_get():
    registry = PluginRegistry()
    plugin = _FakePlugin()

    registry.register(plugin)

    assert registry.get("fake") is plugin
    assert "fake" in registry.list_ids()


def test_register_duplicate_raises():
    registry = PluginRegistry()
    registry.register(_FakePlugin())

    with pytest.raises(ConfigurationError):
        registry.register(_FakePlugin())


def test_get_or_raise_when_missing():
    registry = PluginRegistry()

    with pytest.raises(ConfigurationError) as exc:
        registry.get_or_raise("unknown")

    assert "unknown" in str(exc.value)


def test_get_returns_none_when_missing():
    registry = PluginRegistry()
    assert registry.get("unknown") is None


def test_list_ids_empty():
    registry = PluginRegistry()
    assert registry.list_ids() == []


def test_clear():
    registry = PluginRegistry()
    registry.register(_FakePlugin())

    registry.clear()

    assert registry.list_ids() == []
    assert registry.get("fake") is None


def test_all_returns_copy():
    """Modificar el dict devuelto no debe afectar el registro."""
    registry = PluginRegistry()
    registry.register(_FakePlugin())

    snapshot = registry.all()
    snapshot["hacked"] = None  # type: ignore

    assert "hacked" not in registry.list_ids()
