"""
Property-based tests para PluginRegistry.

Verifican invariantes del registro de plugins.
"""

from unittest.mock import MagicMock

import pytest
from hypothesis import given, strategies as st

from app.plugin_registry import PluginRegistry
from domain.plugins.game_plugin import GamePlugin
from infrastructure.errors.exceptions import ConfigurationError


# ==========================================
# Factory de plugins fake
# ==========================================


def make_fake_plugin(game_id: str) -> GamePlugin:
    """Crea un plugin fake con un game_id específico."""
    plugin = MagicMock(spec=GamePlugin)
    type(plugin).game_id = property(lambda self: game_id)
    type(plugin).display_name = property(lambda self: f"Fake {game_id}")
    return plugin


# Estrategia: game_ids válidos (snake_case corto)
game_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=20,
).filter(lambda s: not s.startswith("_") and not s.endswith("_"))


# ==========================================
# Propiedades
# ==========================================


class TestPluginRegistryInvariants:
    @given(game_id=game_id_strategy)
    def test_registered_plugin_can_be_retrieved(self, game_id: str):
        """Después de registrar, el plugin se puede recuperar."""
        registry = PluginRegistry()
        plugin = make_fake_plugin(game_id)

        registry.register(plugin)

        assert registry.get(game_id) is plugin

    @given(game_id=game_id_strategy)
    def test_unregistered_plugin_returns_none(self, game_id: str):
        """Un game_id no registrado devuelve None."""
        registry = PluginRegistry()
        assert registry.get(game_id) is None

    @given(game_id=game_id_strategy)
    def test_registering_twice_raises(self, game_id: str):
        """Registrar el mismo game_id dos veces lanza ConfigurationError."""
        registry = PluginRegistry()
        registry.register(make_fake_plugin(game_id))

        with pytest.raises(ConfigurationError):
            registry.register(make_fake_plugin(game_id))

    @given(
        game_ids=st.lists(
            game_id_strategy,
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    def test_list_ids_matches_registered(self, game_ids: list[str]):
        """list_ids() devuelve exactamente los registrados."""
        registry = PluginRegistry()
        for gid in game_ids:
            registry.register(make_fake_plugin(gid))

        assert sorted(registry.list_ids()) == sorted(game_ids)

    @given(
        game_ids=st.lists(
            game_id_strategy,
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    def test_all_returns_copy(self, game_ids: list[str]):
        """Modificar el dict devuelto no afecta al registro."""
        registry = PluginRegistry()
        for gid in game_ids:
            registry.register(make_fake_plugin(gid))

        snapshot = registry.all()
        snapshot.clear()  # Modificamos el dict

        # El registro no cambió
        assert sorted(registry.list_ids()) == sorted(game_ids)

    @given(game_id=game_id_strategy)
    def test_clear_removes_all(self, game_id: str):
        """clear() elimina todos los plugins."""
        registry = PluginRegistry()
        registry.register(make_fake_plugin(game_id))

        registry.clear()

        assert registry.get(game_id) is None
        assert registry.list_ids() == []

    @given(game_id=game_id_strategy)
    def test_get_or_raise_for_registered(self, game_id: str):
        """get_or_raise devuelve el plugin si existe."""
        registry = PluginRegistry()
        plugin = make_fake_plugin(game_id)
        registry.register(plugin)

        assert registry.get_or_raise(game_id) is plugin

    @given(game_id=game_id_strategy)
    def test_get_or_raise_for_unregistered(self, game_id: str):
        """get_or_raise lanza ConfigurationError si no existe."""
        registry = PluginRegistry()

        with pytest.raises(ConfigurationError):
            registry.get_or_raise(game_id)
