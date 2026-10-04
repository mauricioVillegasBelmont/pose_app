"""
Contrato de un plugin de juego.

Un plugin es una factory que sabe crear el juego y su estado.
El plugin NO es el juego: es el "manual de instrucciones" para construirlo.

Los plugins son descubiertos por el PluginRegistry y consumidos por el
Container. El núcleo de la aplicación NO conoce plugins concretos.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from domain.state.game_state_port import GameStatePort

if TYPE_CHECKING:
    # Import diferido para evitar ciclos:
    # domain no debe importar app en runtime.
    from app.game_context import GameContext


class GameProtocol(Protocol):
    """
    Protocolo estructural mínimo que debe cumplir un juego.

    No es ABC: usamos structural typing (duck typing tipado).
    Cualquier objeto con estos métodos satisface el protocolo.

    Ventaja: los juegos NO heredan de nada, solo implementan la forma.
    """

    @property
    def state(self) -> GameStatePort:
        """Estado consultable del juego (para el StateRegistry)."""
        ...

    async def run_async(self, should_stop: "Callable[[], bool] | None" = None) -> None:
        """Loop principal del juego."""
        ...


class GamePlugin(ABC):
    """
    Contrato que cada plugin debe cumplir.

    Cada plugin:
    - Se autoidentifica con `game_id` y `display_name`.
    - Sabe crear su estado (`create_state`).
    - Sabe crear su juego (`create_game`) a partir del contexto.
    """

    @property
    @abstractmethod
    def game_id(self) -> str:
        """
        Identificador único del plugin (coincide con GameStatePort.game_id).
        Convención: snake_case, sin espacios.
        """

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nombre legible para humanos (ej: 'Particles Game')."""

    @property
    def description(self) -> str:
        """Descripción corta opcional (default: vacío)."""
        return ""

    @abstractmethod
    def create_state(self) -> GameStatePort:
        """
        Crea el estado inicial del juego.

        Nota: el Container NO usa este método directamente. El plugin
        lo usa internamente dentro de `create_game()`, y el Container
        obtiene el estado via `game.state`.
        """

    @abstractmethod
    def create_game(self, context: "GameContext") -> GameProtocol:
        """
        Construye el juego con las dependencias compartidas.

        Args:
            context: Dependencias compartidas (camera, pose, bus, settings).

        Returns:
            Instancia del juego lista para `await game.run_async()`.
        """
