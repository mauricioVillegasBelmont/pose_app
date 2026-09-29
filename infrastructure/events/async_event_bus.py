"""
Event Bus asíncrono con dispatch thread-safe.

Diseño:
- Los handlers son `async def`.
- El bus mantiene un dict de event_type → [handlers].
- `publish()` corre los handlers en el MISMO loop asyncio del caller.
- Los suscriptores deben suscribirse/desuscribirse en el loop principal.

Thread-safety:
- `subscribe()` y `unsubscribe()` usan Lock (pueden venir de otros threads).
- `publish()` asume que corre en el loop principal de asyncio.
"""

from collections import defaultdict
from threading import Lock

from domain.events.base import DomainEvent
from domain.ports.event_bus_port import EventBusPort, EventHandler
from infrastructure.logging.logger import get_logger

logger = get_logger("events.async_bus")


class AsyncEventBus(EventBusPort):
    """Implementación async del Event Bus."""

    def __init__(self):
        self._handlers: dict[
            type[DomainEvent], list[EventHandler]
        ] = defaultdict(list)
        self._lock = Lock()

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        with self._lock:
            handlers = self._handlers[event_type]
            if handler in handlers:
                logger.debug(
                    f"Handler {handler.__name__} ya suscrito a "
                    f"{event_type.__name__}, ignorando"
                )
                return
            handlers.append(handler)
            logger.debug(
                f"Handler {handler.__name__} suscrito a "
                f"{event_type.__name__}"
            )

    def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publica y espera a todos los handlers (secuencial)."""
        with self._lock:
            handlers = list(self._handlers.get(type(event), []))

        if not handlers:
            return

        logger.debug(
            f"Publicando {event.event_name} a {len(handlers)} handlers"
        )

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Error en handler {handler.__name__} para "
                    f"{event.event_name}: {e}",
                    exc_info=True,
                )
                # Continúa con el siguiente handler

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()