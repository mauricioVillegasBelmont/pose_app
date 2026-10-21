"""
Cargador de assets (Infraestructura).
Lee metadatos de sprites (JSON) y construye configuraciones de dominio.
"""

import json
from pathlib import Path

from pose_app.domain.capabilities.particles.components import SpriteConfig
from pose_app.infrastructure.assets.sprite_sheet_parser import SpriteSheetParser
from pose_app.infrastructure.logging.logger import get_logger
from pose_app.infrastructure.paths import ASSETS_DIR

logger = get_logger("infrastructure.assets.asset_loader")


class AssetLoader:
    """Carga metadatos de assets desde el sistema de archivos."""

    def __init__(self, assets_dir: Path | None = None) -> None:
        self._assets_dir = assets_dir or ASSETS_DIR
        self._parser = SpriteSheetParser()

    def load_sprite_config(
        self,
        category: str,  # ej: "particles"
        sprite_name: str,  # ej: "blood-curse"
        fps: float = 12.0,
        animation_mode: str = "loop",
    ) -> SpriteConfig | None:
        """
        Lee el JSON de un sprite sheet y retorna un SpriteConfig de dominio.
        Si no encuentra el JSON, usa valores por defecto razonables.
        """
        json_path = self._assets_dir / category / "sprites" / f"{sprite_name}.json"
        image_path = self._assets_dir / category / "sprites" / f"{sprite_name}.png"

        if not image_path.exists():
            logger.warning(f"Imagen de sprite no encontrada: {image_path}")
            return None

        # Valores por defecto (fallback)
        frame_width = 256.0
        frame_height = 256.0
        frame_count = 1

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                frames = self._parser.parse(data)
                if frames:
                    # Asumimos que todos los frames tienen el mismo tamaño.
                    # El parser retorna: {0: (x, y, w, h), 1: (x, y, w, h), ...}
                    first_frame_coords = next(iter(frames.values()))
                    frame_width = float(first_frame_coords[2])  # w
                    frame_height = float(first_frame_coords[3])  # h
                    frame_count = len(frames)
            except Exception as e:
                logger.error(f"Error leyendo JSON de sprite '{sprite_name}': {e}")

        return SpriteConfig(
            path=f"{sprite_name}.png",
            frame_width=frame_width,
            frame_height=frame_height,
            frame_count=frame_count,
            fps=fps,
            animation_mode=animation_mode,  # type: ignore[arg-type]
        )
