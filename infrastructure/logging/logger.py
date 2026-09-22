"""
Logger centralizado de la aplicación.

Soporta dos formatos:
- console: legible para humanos (desarrollo)
- json: estructurado para agregadores (producción)
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import LoggingSettings


class JSONFormatter(logging.Formatter):
    """Formatea logs como JSON (útil para producción)."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Añade información extra si existe
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Formato legible con colores para consola."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Verde
        "WARNING": "\033[33m",   # Amarillo
        "ERROR": "\033[31m",     # Rojo
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]

        return (
            f"{color}[{timestamp}] {record.levelname:8s} "
            f"{record.name:20s} | {record.getMessage()}{self.RESET}"
        )


def setup_logger(settings: LoggingSettings) -> logging.Logger:
    """
    Configura y devuelve el logger raíz de la aplicación.

    Args:
        settings: Configuración de logging.

    Returns:
        Logger configurado.
    """
    logger = logging.getLogger("pose_ar")
    logger.setLevel(settings.level)
    logger.handlers.clear()  # Evita duplicados si se llama varias veces

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.format == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)

    # Handler de archivo (opcional)
    if settings.file:
        log_path = Path(settings.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())  # Siempre JSON en archivo
        logger.addHandler(file_handler)

    # No propaga al root logger (evita duplicados)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger hijo (para módulos específicos).

    Args:
        name: Nombre del módulo (ej: "adapters.webcam").

    Returns:
        Logger hijo que hereda la configuración del padre.
    """
    return logging.getLogger(f"pose_ar.{name}")