"""
Punto de entrada async de la aplicación.
"""

import asyncio
import contextlib
import signal
import sys

from config.settings import get_settings
from infrastructure.di.container import Container
from infrastructure.logging.logger import get_logger, setup_logger

# Timeout para shutdown ordenado (segundos)
SHUTDOWN_TIMEOUT = 5.0


async def main_async() -> int:
    settings = get_settings()
    setup_logger(settings.logging)
    logger = get_logger("main")

    logger.info(f"=== {settings.app_name} ===")
    logger.info(f"Entorno: {settings.environment}")
    logger.info(f"Juego: {settings.game.type}")
    logger.info(f"API: {'habilitada' if settings.api.enabled else 'deshabilitada'}")

    container = Container(settings)
    stop_event = asyncio.Event()

    # Señales
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    game_task: asyncio.Task | None = None
    api_task: asyncio.Task | None = None

    try:
        # Crea el juego
        game = container.create_game()
        game_task = asyncio.create_task(
            game.run_async(should_stop=stop_event.is_set),
            name="game",
        )

        # API
        # api = container.create_api()
        api = container.api
        if api is not None:
            api_task = asyncio.create_task(api.serve(), name="api")

        # Espera a: stop_event o fin de algún task
        waiter_tasks: list[asyncio.Task] = [game_task]
        if api_task is not None:
            waiter_tasks.append(api_task)
        waiter_tasks.append(asyncio.create_task(stop_event.wait(), name="stop"))

        done, _ = await asyncio.wait(
            waiter_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        # ---------- SHUTDOWN ORDENADO ----------
        logger.info("Iniciando shutdown ordenado...")

        # 1. Pedir a la API que se detenga por su propio mecanismo
        if api is not None:
            await api.shutdown()  # envía should_exit=True

        # 2. Dar tiempo a que los tasks terminen solos
        pending = [t for t in [game_task, api_task] if t is not None and not t.done()]
        if pending:
            done_now, still_pending = await asyncio.wait(
                pending, timeout=SHUTDOWN_TIMEOUT
            )
            # 3. Cancelar lo que quede (por si acaso)
            for task in still_pending:
                logger.warning(
                    f"Task {task.get_name()} no terminó a tiempo, cancelando"
                )
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    finally:
        await container.shutdown()

    return 0


def main() -> int:
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())