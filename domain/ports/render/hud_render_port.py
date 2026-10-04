"""
Puerto de render para capacidad de HUD.

Sigue el patrón set_* + render_* para separar la declaración
de qué dibujar de la ejecución del dibujo.
"""

from abc import ABC, abstractmethod


class HudRenderPort(ABC):
    """Capacidad de render: dibujar un HUD (puntos, rondas, timer)."""

    @abstractmethod
    def set_hud(
        self,
        score: int,
        rounds: int,
        timer: float,
        extra: dict[str, str] | None = None,
    ) -> None:
        """
        Declara los valores actuales del HUD.

        Args:
            score: Puntuación actual.
            rounds: Número de rondas.
            timer: Tiempo transcurrido/restante (segundos).
            extra: Campos adicionales específicos del juego.
        """

    @abstractmethod
    def render_hud(self) -> None:
        """Dibuja el HUD declarado."""

    @abstractmethod
    def close(self) -> None:
        """
        Cierra y libera recursos.

        Debe ser idempotente.
        """
