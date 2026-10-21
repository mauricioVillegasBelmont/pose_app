"""
Parser para archivos JSON de sprite sheets (formato AutoSprite/TexturePacker).
Traduce el JSON a un diccionario de coordenadas utilizable por el adaptador de render.
"""

from typing import Any


class SpriteSheetParser:
    """
    Extrae las coordenadas (x, y, w, h) de cada frame desde un JSON.

    Es robusto ante claves con espacios en blanco (ej: 'frames ', '0 '),
    común en exportadores de sprites gratuitos.
    """

    def parse(self, data: dict[str, Any]) -> dict[int, tuple[int, int, int, int]]:
        """
        Parsea el JSON y retorna un diccionario {frame_index: (x, y, w, h)}.
        Args:
            data: Contenido del JSON cargado como diccionario.
        Returns:
            Diccionario mapeando el índice del frame a sus coordenadas.
        """
        # Buscar la clave 'frames' ignorando espacios directamente en el diccionario
        frames_key = next((k for k in data if k.strip() == "frames"), None)

        if not frames_key:
            return {}

        frames_data = data[frames_key]
        result: dict[int, tuple[int, int, int, int]] = {}

        for key, value in frames_data.items():
            # Limpiar clave y convertir a int
            try:
                frame_index = int(key.strip())
            except ValueError:
                # Ignorar claves no numéricas (ej: 'background')
                continue

            x = value.get("x", 0)
            y = value.get("y", 0)
            w = value.get("w", 0)
            h = value.get("h", 0)

            result[frame_index] = (x, y, w, h)

        return result
