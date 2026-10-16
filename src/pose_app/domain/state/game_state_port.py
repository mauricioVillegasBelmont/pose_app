"""
Puerto de estado de un juego.

Cada juego (particles, color, futuro audio, ...) implementa este puerto
para exponer su estado de forma consultable por la API u otros consumidores.

Un juego NO comparte estado con otro: cada uno es dueño de su propio
GameStatePort. La API consulta el StateRegistry para agregar todos.
"""

from abc import ABC, abstractmethod
from typing import Any


class GameStatePort(ABC):
    """
    Contrato que cada juego implementa para exponer su estado.

    Thread-safety: la implementación debe ser thread-safe porque será
    consultada desde el thread de la API mientras el juego la actualiza.
    """

    @property
    @abstractmethod
    def game_id(self) -> str:
        """
        Identificador único del juego.

        Convención: snake_case, sin espacios.
        Ejemplos: 'particles', 'color', 'audio'.
        """

    @abstractmethod
    def snapshot(self) -> dict[str, Any]:
        """
        Devuelve el estado actual como dict serializable (JSON-friendly).

        Contrato:
            - Retorna una COPIA, no referencias mutables.
            - No incluye datos no serializables (numpy, objetos, etc.).
            - Debe ser rápido (<1ms idealmente).
        """

    @abstractmethod
    def stats(self) -> dict[str, Any]:
        """
        Estadísticas específicas del juego (más ligero que snapshot).

        Ejemplos: frames procesados, elementos activos, fps.
        """


# python -c "from domain.state.game_state_port import GameStatePort; print('OK')"
