"""Tests del ConsoleFormatter (colores ANSI activos/desactivados)."""

import logging

from infrastructure.logging.logger import ConsoleFormatter


def _make_record(level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord(
        name="test.logger",
        level=level,
        pathname=__file__,
        lineno=0,
        msg="mensaje de prueba",
        args=(),
        exc_info=None,
    )


def test_formatter_includes_ansi_code_when_colors_enabled() -> None:
    """Con use_colors=True, la salida incluye el código ANSI del nivel."""
    # Arrange
    formatter = ConsoleFormatter(use_colors=True)
    record = _make_record(logging.ERROR)

    # Act
    output = formatter.format(record)

    # Assert
    assert "\033[31m" in output


def test_formatter_omits_ansi_codes_when_colors_disabled() -> None:
    """Con use_colors=False, la salida no contiene ningún código ANSI."""
    # Arrange
    formatter = ConsoleFormatter(use_colors=False)
    record = _make_record(logging.ERROR)

    # Act
    output = formatter.format(record)

    # Assert
    assert "\033[" not in output


def test_formatter_includes_message_and_level_regardless_of_colors() -> None:
    """El mensaje y el nivel aparecen con colores activados y desactivados."""
    record = _make_record(logging.WARNING)

    with_colors = ConsoleFormatter(use_colors=True).format(record)
    without_colors = ConsoleFormatter(use_colors=False).format(record)

    assert "mensaje de prueba" in with_colors and "WARNING" in with_colors
    assert "mensaje de prueba" in without_colors and "WARNING" in without_colors
