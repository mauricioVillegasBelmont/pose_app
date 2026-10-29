"""
Configuración unificada de perfiles de jugabilidad (Game Profiles).

Permite ajustar el comportamiento de CUALQUIER juego (dificultad, física, suavizado)
mediante archivos JSON, sin modificar código Python.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class GameProfileConfig(BaseModel):
    """
    Modelo unificado de configuración de jugabilidad.

    Los campos de primer nivel son comunes a todos los juegos AR.
    Los campos específicos de cada juego van dentro de 'game_options'.
    """

    # Configuración común AR (aplica a todos los juegos)
    pose_smoothing_factor: float = 0.3

    # Configuración específica del juego (flexible pero tipada como dict)
    game_options: dict[str, Any] = {}

    model_config = ConfigDict(
        extra="allow"
    )  # Permite campos extra si se definen en JSON

    @field_validator("pose_smoothing_factor")
    @classmethod
    def validate_smoothing_factor(cls, v: float) -> float:
        if not (0.0 < v <= 1.0):
            raise ValueError(
                "pose_smoothing_factor must be between 0.0 (exclusive) and 1.0"
            )
        return v


def load_game_profile(config_path: Path) -> GameProfileConfig:
    """
    Carga un perfil de configuración desde un archivo JSON.

    Args:
        config_path: Ruta absoluta o relativa al archivo JSON del perfil.

    Returns:
        GameProfileConfig validado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el JSON tiene valores inválidos según el modelo.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Game profile config not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    return GameProfileConfig(**data)
