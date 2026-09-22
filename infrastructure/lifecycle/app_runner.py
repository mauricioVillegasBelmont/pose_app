"""
Runner de la aplicación con graceful shutdown.

Captura SIGINT (Ctrl+C) y SIGTERM para cerrar recursos correctamente.
"""

import signal
from collections.abc import Callable

from infrastructure.logging.logger import get_logger

logger = get_logger("lifecycle")


class AppRunner:
    """
    Ejecuta la aplicación con manejo de señales.

    Uso:
        runner = AppRunner()
        runner.run(game.run)
    """

    def __init__(self):
        self._shutdown_requested = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Registra handlers para señales del sistema."""
        signal.signal(signal.SIGINT, self._handle_signal)

        # SIGTERM solo en sistemas Unix
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        """Handler de señales (Ctrl+C, SIGTERM)."""
        logger.info(f"Señal recibida: {signum}. Iniciando shutdown...")
        self._shutdown_requested = True

    def should_shutdown(self) -> bool:
        """Indica si se solicitó el shutdown."""
        return self._shutdown_requested

    def run(self, target: Callable[[], None]) -> int:
        """
        Ejecuta la función objetivo con manejo de señales.

        Args:
            target: Función a ejecutar (ej: game.run).

        Returns:
            Código de salida (0 = éxito, 1 = error).
        """
        exit_code = 0

        try:
            logger.info("Iniciando aplicación...")
            target()
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado")
        except Exception as e:
            logger.critical(f"Error fatal: {e}", exc_info=True)
            exit_code = 1
        finally:
            logger.info("Aplicación finalizada")

        return exit_code