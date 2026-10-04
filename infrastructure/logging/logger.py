"""
Logger centralizado de la aplicación.

Soporta:
- Consola (console o json).
- Archivo opcional (app.log + errors.log) si LOG_FILE=true.

Separación de archivos:
- logs/app.log     → INFO, WARNING, DEBUG, ERROR, CRITICAL (todo)
- logs/errors.log  → solo ERROR y CRITICAL
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import LoggingSettings


# ==========================================
# Formatters
# ==========================================


class JSONFormatter(logging.Formatter):
    """Formatea logs como JSON (útil para producción)."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Formato legible con colores para consola."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        return (
            f"{color}[{timestamp}] {record.levelname:8s} "
            f"{record.name:20s} | {record.getMessage()}{self.RESET}"
        )


# ==========================================
# Filtros
# ==========================================


class MaxLevelFilter(logging.Filter):
    """Solo permite registros con nivel <= max_level."""

    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


class MinLevelFilter(logging.Filter):
    """Solo permite registros con nivel >= min_level."""

    def __init__(self, min_level: int):
        super().__init__()
        self.min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self.min_level


# ==========================================
# Setup
# ==========================================


def setup_logger(settings: LoggingSettings) -> logging.Logger:
    """
    Configura y devuelve el logger raíz de la aplicación.
    """
    logger = logging.getLogger("pose_ar")
    logger.setLevel(settings.level)
    logger.handlers.clear()
    logger.propagate = False

    # ==========================================
    # Handler de consola
    # ==========================================
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.format == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)

    # ==========================================
    # Handlers de archivo (opcionales)
    # ==========================================
    if settings.file:
        log_dir = Path(settings.directory)
        log_dir.mkdir(parents=True, exist_ok=True)

        # --- app.log: TODO ---
        app_log_path = log_dir / "app.log"
        app_handler = logging.FileHandler(app_log_path, encoding="utf-8")
        app_handler.setFormatter(JSONFormatter())  # archivo en JSON
        logger.addHandler(app_handler)

        # --- errors.log: solo ERROR y CRITICAL ---
        errors_log_path = log_dir / "errors.log"
        errors_handler = logging.FileHandler(errors_log_path, encoding="utf-8")
        errors_handler.setFormatter(JSONFormatter())
        errors_handler.addFilter(MinLevelFilter(logging.ERROR))
        logger.addHandler(errors_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger hijo."""
    return logging.getLogger(f"pose_ar.{name}")
