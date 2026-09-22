"""
Manejo centralizado de errores.

Convierte excepciones en respuestas consistentes (log + acción).
"""

from collections.abc import Callable
from enum import Enum
from typing import Any

from infrastructure.errors.exceptions import (
    CameraError,
    ConfigurationError,
    PoseEstimationError,
    RenderError,
)
from infrastructure.logging.logger import get_logger

logger = get_logger("errors")


class ErrorAction(Enum):
    """Acciones posibles ante un error."""
    FATAL = "fatal"          # Detener la app
    RETRY = "retry"          # Reintentar
    SKIP = "skip"            # Ignorar y continuar
    DEGRADE = "degrade"      # Modo degradado


# Mapeo: tipo de excepción → acción
ERROR_ACTIONS: dict[type[Exception], ErrorAction] = {
    ConfigurationError: ErrorAction.FATAL,
    CameraError: ErrorAction.FATAL,
    PoseEstimationError: ErrorAction.SKIP,   # Omite frame y sigue
    RenderError: ErrorAction.FATAL,
}


def handle_error(
    error: Exception,
    context: dict[str, Any] | None = None
) -> ErrorAction:
    """
    Maneja un error según su tipo.

    Args:
        error: Excepción a manejar.
        context: Información adicional para el log.

    Returns:
        Acción a tomar.
    """
    context = context or {}

    # Determina la acción
    action = ErrorAction.FATAL  # Por defecto, fatal
    for exc_type, exc_action in ERROR_ACTIONS.items():
        if isinstance(error, exc_type):
            action = exc_action
            break

    # Log según severidad
    if action == ErrorAction.FATAL:
        logger.critical(
            f"Error fatal: {type(error).__name__}: {error}",
            extra={"extra_data": context}
        )
    elif action == ErrorAction.SKIP:
        logger.warning(
            f"Error recuperable (skip): {type(error).__name__}: {error}",
            extra={"extra_data": context}
        )
    else:
        logger.error(
            f"Error: {type(error).__name__}: {error}",
            extra={"extra_data": context}
        )

    return action


def safe_execute(
    func: Callable[..., Any],
    *args: Any,
    context: dict[str, Any] | None = None,
    **kwargs: Any
) -> tuple[bool, Any]:
    """
    Ejecuta una función capturando errores de forma segura.

    Returns:
        (success, result_or_none)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        action = handle_error(e, context=context)

        if action == ErrorAction.FATAL:
            raise  # Re-lanza para detener la app

        return False, None