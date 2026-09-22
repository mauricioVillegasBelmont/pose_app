"""
Punto de entrada unificado de la aplicación.

Uso:
    python -m app.main
    # o
    python app/main.py
"""

import sys

from config.settings import get_settings
from infrastructure.di.container import Container
from infrastructure.errors.exceptions import AppError, ConfigurationError
from infrastructure.lifecycle.app_runner import AppRunner
from infrastructure.logging.logger import get_logger, setup_logger


def main() -> int:
    """Punto de entrada principal."""
    # 1. Carga configuración
    try:
        settings = get_settings()
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}", file=sys.stderr)
        return 1

    # 2. Configura logging
    setup_logger(settings.logging)
    logger = get_logger("main")

    logger.info(f"=== {settings.app_name} ===")
    logger.info(f"Entorno: {settings.environment}")
    logger.info(f"Juego: {settings.game.type}")
    logger.info(f"Pose: {settings.pose.provider}")
    logger.info(f"Render: {settings.render.provider}")
    logger.info(f"API: {'habilitada' if settings.api.enabled else 'deshabilitada'}")

    # 3. Contenedor DI + runner
    container = Container(settings)
    runner = AppRunner()

    try:
        # 4. Inicia la API (en thread separado)
        container.start_api()

        # 5. Crea el juego según configuración
        game = container.create_game()

        # 6. Ejecuta con graceful shutdown
        exit_code = runner.run(
            target=lambda: game.run(should_stop=runner.should_shutdown)
        )

        return exit_code

    except ConfigurationError as e:
        logger.critical(f"Error de configuración: {e}", exc_info=True)
        return 2
    except AppError as e:
        logger.critical(f"Error de aplicación: {e}", exc_info=True)
        return 3
    except Exception as e:
        logger.critical(f"Error inesperado: {e}", exc_info=True)
        return 99
    finally:
        # 6. Cleanup garantizado
        container.shutdown()


if __name__ == "__main__":
    sys.exit(main())