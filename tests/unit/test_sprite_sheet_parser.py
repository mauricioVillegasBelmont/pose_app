"""
Tests TDD para el SpriteSheetParser.
Valida que el parser extraiga correctamente las coordenadas de los frames
incluso si el JSON tiene formatos sucios (espacios en las claves).
"""

from pose_app.infrastructure.assets.sprite_sheet_parser import SpriteSheetParser


class TestSpriteSheetParser:
    """El parser debe extraer coordenadas (x, y, w, h) de cada frame."""

    def test_parses_standard_json_format(self) -> None:
        """Formato limpio estándar."""
        # Arrange
        data = {
            "frames": {
                "0": {"x": 0, "y": 0, "w": 64, "h": 64},
                "1": {"x": 64, "y": 0, "w": 64, "h": 64},
            },
            "meta": {"size": {"w": 128, "h": 64}},
        }
        parser = SpriteSheetParser()

        # Act
        frames = parser.parse(data)

        # Assert
        assert len(frames) == 2
        assert frames[0] == (0, 0, 64, 64)
        assert frames[1] == (64, 0, 64, 64)

    def test_handles_trailing_spaces_in_keys(self) -> None:
        """
        Formato sucio (como el de blood-curse.json):
        Las claves tienen espacios ('frames ', '0 ').
        """
        # Arrange
        data = {
            "frames ": {
                "0 ": {"x": 0, "y": 0, "w": 256, "h": 256},
                "1 ": {"x": 256, "y": 0, "w": 256, "h": 256},
                "15 ": {"x": 768, "y": 768, "w": 256, "h": 256},
            },
            "meta ": {"size": {"w": 1024, "h": 1024}},
        }
        parser = SpriteSheetParser()

        # Act
        frames = parser.parse(data)

        # Assert
        assert len(frames) == 3
        assert 0 in frames
        assert 1 in frames
        assert 15 in frames
        assert frames[0] == (0, 0, 256, 256)
        assert frames[15] == (768, 768, 256, 256)

    def test_ignores_non_numeric_frame_keys(self) -> None:
        """Si una clave no es un número (ej: 'background'), se ignora."""
        # Arrange
        data = {
            "frames": {
                "0": {"x": 0, "y": 0, "w": 64, "h": 64},
                "background": {"x": 0, "y": 0, "w": 100, "h": 100},
            },
            "meta": {},
        }
        parser = SpriteSheetParser()

        # Act
        frames = parser.parse(data)

        # Assert
        assert len(frames) == 1
        assert 0 in frames

    def test_returns_empty_dict_if_no_frames_key(self) -> None:
        """Si el JSON no tiene la clave 'frames', retorna vacío."""
        # Arrange
        data = {"meta": {"size": {"w": 100, "h": 100}}}
        parser = SpriteSheetParser()

        # Act & Assert
        assert parser.parse(data) == {}

    def test_returns_empty_dict_if_frames_is_empty(self) -> None:
        """Si 'frames' está vacío, retorna vacío."""
        # Arrange
        data = {"frames": {}, "meta": {}}
        parser = SpriteSheetParser()

        # Act & Assert
        assert parser.parse(data) == {}
