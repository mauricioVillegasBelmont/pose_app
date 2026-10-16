"""
Puerto del Event Bus (async).

Contrato:
- Suscriptores async.
- Publicación async: los handlers se ejecutan secuencialmente (await).
- Errores en handlers se loggean y NO rompen el bus.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from pose_app.domain.events.base import DomainEvent

EventHandler = Callable[[Any], Awaitable[None]]


class EventBusPort(ABC):
    """Puerto del bus de eventos."""

    @abstractmethod
    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        """
        Registra un handler para un tipo de evento.

        Si el mismo handler se suscribe dos veces al mismo evento,
        NO se duplica.
        """

    @abstractmethod
    def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        """Desregistra un handler."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento. Todos los handlers suscritos se ejecutan
        (await secuencial).

        Contrato:
            - Los handlers se ejecutan en orden de suscripción.
            - Si un handler falla, se loggea y se continúa con el siguiente.
            - Es thread-safe (si la implementación lo garantiza).
        """

    @abstractmethod
    def clear(self) -> None:
        """Elimina todos los suscriptores (útil en tests)."""
