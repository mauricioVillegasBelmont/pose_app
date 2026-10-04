"""
Eventos del dominio.

Un evento es un hecho inmutable que ya ocurrió.
Convención: nombres en pasado (PoseUpdated, no UpdatePose).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """
    Clase base para todos los eventos del dominio.

    `kw_only=True` permite que las subclases añadan campos sin default
    sin conflictos de orden (los eventos se instancian por keyword).
    """

    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_name(self) -> str:
        return type(self).__name__
