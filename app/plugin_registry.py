"""
Registro de plugins de juego.

Responsabilidades:
- Mantener mapping game_id → GamePlugin.
- Permitir registro, consulta y listado.
- Ser thread-safe (aunque el registro ocurre en startup).

Uso:
    registry = PluginRegistry()
    registry.register(ParticlesPlugin())
    registry.register(ColorPlugin())

    plugin = registry.get_or_raise("particles")
"""

from threading import Lock

from domain.plugins.game_plugin import GamePlugin
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.logging.logger import get_logger

logger = get_logger("app.plugin_registry")


class PluginRegistry:
    """Registro thread-safe de plugins de juego."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._plugins: dict[str, GamePlugin] = {}

    def register(self, plugin: GamePlugin) -> None:
        """
        Registra un plugin.

        Raises:
            ConfigurationError: si ya existe un plugin con el mismo game_id.
        """
        with self._lock:
            if plugin.game_id in self._plugins:
                raise ConfigurationError(
                    f"Plugin duplicado: '{plugin.game_id}'",
                    context={"game_id": plugin.game_id},
                )
            self._plugins[plugin.game_id] = plugin
            logger.info(f"Plugin registrado: {plugin.game_id} ({plugin.display_name})")

    def get(self, game_id: str) -> GamePlugin | None:
        """Devuelve un plugin o None si no está registrado."""
        with self._lock:
            return self._plugins.get(game_id)

    def get_or_raise(self, game_id: str) -> GamePlugin:
        """
        Devuelve un plugin o lanza ConfigurationError.

        Raises:
            ConfigurationError: si el plugin no está registrado.
        """
        plugin = self.get(game_id)
        if plugin is None:
            available = self.list_ids()
            raise ConfigurationError(
                f"Plugin desconocido: '{game_id}'. Disponibles: {available}",
                context={"requested": game_id, "available": available},
            )
        return plugin

    def list_ids(self) -> list[str]:
        """Lista los game_id registrados."""
        with self._lock:
            return list(self._plugins.keys())

    def all(self) -> dict[str, GamePlugin]:
        """Devuelve una copia del mapping (seguro para iterar)."""
        with self._lock:
            return dict(self._plugins)

    def clear(self) -> None:
        """Limpia el registro (útil en tests)."""
        with self._lock:
            self._plugins.clear()
