"""
Snapshot agregado de todos los juegos activos.

Es un DTO simple. La API lo usa para responder a GET /state.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AppSnapshot:
    """Snapshot completo de la aplicación."""

    games: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_games: list[str] = field(default_factory=list)
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Serializa a dict JSON-friendly."""
        return {
            "games": self.games,
            "active_games": self.active_games,
            "captured_at": self.captured_at.isoformat(),
        }


# python -c "from domain.state.snapshot import AppSnapshot; print(AppSnapshot().to_dict())"
