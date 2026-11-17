"""
Configuración de landmarks para un cursor de interacción.

Define qué landmarks del esqueleto se usan para calcular el punto de colisión
de un cursor (mano, pie, cadera, etc.) y qué offset aplicar.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HandLandmarkConfig:
    """
    Configuración inmutable de landmarks para un cursor.

    Attributes:
        landmark_names: Tupla de nombres de landmarks a usar (ej: "left_wrist", "left_index").
                        Debe contener al menos un nombre.
        offset_x: Offset horizontal en coordenadas normalizadas (0-1). Default: 0.0.
        offset_y: Offset vertical en coordenadas normalizadas (0-1). Default: 0.0.

    Raises:
        ValueError: Si landmark_names está vacío o los offsets están fuera de rango.
    """

    landmark_names: tuple[str, ...]
    offset_x: float = 0.0
    offset_y: float = 0.0

    def __post_init__(self) -> None:
        """Valida que los valores sean correctos."""
        if not self.landmark_names:
            raise ValueError("HandLandmarkConfig landmark_names must not be empty")

        if not (-1.0 <= self.offset_x <= 1.0):
            raise ValueError(
                f"HandLandmarkConfig offset_x must be in range [-1.0, 1.0], got {self.offset_x}"
            )

        if not (-1.0 <= self.offset_y <= 1.0):
            raise ValueError(
                f"HandLandmarkConfig offset_y must be in range [-1.0, 1.0], got {self.offset_y}"
            )
