"""
Contrato de un plugin de juego.

Un plugin es una factory que sabe crear el juego y su estado.
El plugin NO es el juego, es el "manual de instrucciones" para construirlo.

Los plugins son descubiertos por el PluginRegistry y consumidos por el
Container. El núcleo de la aplicación NO conoce plugins concretos.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

from domain.state.game_state_port import GameStatePort

if TYPE_CHECKING:
    from app.game_context import GameContext


class GameProtocol(Protocol):
    """
    Protocolo mínimo que debe cumplir un juego para ser gestionado
    por el núcleo. No es una ABC (structural typing, no nominal).
    """

    @property
    def state(self) -> GameStatePort: ...

    async def run_async(self, should_stop=None) -> None: ...


class GamePlugin(ABC):
    """
    Contrato que cada plugin debe cumplir.

    Cada plugin se autoidentifica, expone un nombre legible, sabe crear
    su estado y su juego.
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
        """Descripción corta opcional."""
        return ""

    @abstractmethod
    def create_state(self) -> GameStatePort:
        """
        Crea el estado inicial del juego.

        El Container lo registra en el StateRegistry para que la API
        pueda consultarlo.
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
