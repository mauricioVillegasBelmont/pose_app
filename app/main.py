"""
Punto de entrada async de la aplicación.
"""

import asyncio
import contextlib
import signal
import sys

from config.settings import get_settings
from infrastructure.di.container import Container
from infrastructure.errors.exceptions import AppError, ConfigurationError
from infrastructure.logging.logger import get_logger, setup_logger

SHUTDOWN_TIMEOUT = 5.0


async def main_async() -> int:
    """Ejecuta la aplicación. Devuelve código de salida."""
    settings = get_settings()
    setup_logger(settings.logging)
    logger = get_logger("main")

    logger.info(f"=== {settings.app_name} ===")
    logger.info(f"Entorno: {settings.environment}")
    logger.info(f"Juego: {settings.game.type}")
    logger.info(f"API: {'habilitada' if settings.api.enabled else 'deshabilitada'}")

    container = Container(settings)
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    game_task: asyncio.Task | None = None
    api_task: asyncio.Task | None = None

    try:
        # ==========================================
        # Fase de construcción (errores de config)
        # ==========================================
        try:
            game = container.create_game()
        except ConfigurationError as e:
            # Error de configuración: mensaje claro, sin stack trace
            logger.critical(f"Error de configuración: {e.message}")
            if e.context:
                logger.critical(f"  Detalles: {e.context}")
            return 2  # código de salida para config errors

        # ==========================================
        # Fase de ejecución (errores runtime)
        # ==========================================
        game_task = asyncio.create_task(
            game.run_async(should_stop=stop_event.is_set),
            name="game",
        )

        api = container.api
        if api is not None:
            api_task = asyncio.create_task(api.serve(), name="api")

        # Espera
        waiter_tasks: list[asyncio.Task] = [game_task]
        if api_task is not None:
            waiter_tasks.append(api_task)
        waiter_tasks.append(asyncio.create_task(stop_event.wait(), name="stop"))

        _done, _ = await asyncio.wait(waiter_tasks, return_when=asyncio.FIRST_COMPLETED)

        # ==========================================
        # Shutdown ordenado
        # ==========================================
        logger.info("Iniciando shutdown ordenado...")

        if api is not None:
            await api.shutdown()

        pending = [t for t in [game_task, api_task] if t is not None and not t.done()]
        if pending:
            _, still_pending = await asyncio.wait(pending, timeout=SHUTDOWN_TIMEOUT)
            for task in still_pending:
                logger.warning(
                    f"Task {task.get_name()} no terminó a tiempo, " f"cancelando"
                )
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        return 0

    except AppError as e:
        # Otros errores de la jerarquía AppError
        logger.critical(f"Error de aplicación: {e.message}")
        if e.context:
            logger.critical(f"  Detalles: {e.context}")
        return 3

    except Exception as e:
        # Errores inesperados: sí queremos stack trace
        logger.critical(
            f"Error inesperado: {type(e).__name__}: {e}",
            exc_info=True,
        )
        return 99

    finally:
        await container.shutdown()


def main() -> int:
    """
    Entry point síncrono.

    Captura errores de más arriba (ej: falla de asyncio.run).
    """
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        return 130  # 128 + SIGINT
    except Exception as e:
        # Este bloque solo se ejecuta si main_async NI SIQUIERA llegó
        # a capturar el error (raro), o si asyncio.run falla.
        print(f"❌ Fatal: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
