"""
Tests unitarios para GameProfileConfig.
Validan la carga unificada de perfiles de jugabilidad desde JSON.
"""

import json
from pathlib import Path

import pytest

from pose_app.config.game_profile import GameProfileConfig, load_game_profile
from pose_app.config.settings import GameSettings


class TestGameProfileConfigDefaults:
    def test_default_values_are_sensible(self) -> None:
        """Sin parámetros, los defaults deben ser jugables y seguros."""
        config = GameProfileConfig()

        assert config.pose_smoothing_factor == 0.3
        assert config.game_options == {}


class TestGameProfileConfigValidation:
    def test_rejects_invalid_smoothing_factor(self) -> None:
        """pose_smoothing_factor debe estar entre 0.0 (excluido) y 1.0."""
        with pytest.raises(ValueError, match="pose_smoothing_factor"):
            GameProfileConfig(pose_smoothing_factor=0.0)

        with pytest.raises(ValueError, match="pose_smoothing_factor"):
            GameProfileConfig(pose_smoothing_factor=1.5)

    def test_accepts_valid_custom_values_and_game_options(self) -> None:
        """Debe aceptar valores personalizados y opciones específicas del juego."""
        config = GameProfileConfig(
            pose_smoothing_factor=0.5,
            game_options={"max_score": 20, "gravity": 0.15, "burst_count": 10},
        )

        assert config.pose_smoothing_factor == 0.5
        assert config.game_options["max_score"] == 20
        assert config.game_options["gravity"] == 0.15


class TestGameProfileLoader:
    def test_raises_file_not_found_when_profile_does_not_exist(
        self, tmp_path: Path
    ) -> None:
        """load_game_profile DEBE lanzar FileNotFoundError si el archivo no existe."""
        missing = tmp_path / "particles" / "does_not_exist.json"
        with pytest.raises(FileNotFoundError):
            load_game_profile(missing)

    def test_loads_from_valid_json_path(self, tmp_path: Path) -> None:
        """Debe cargar configuración desde un archivo JSON válido."""
        config_data = {
            "pose_smoothing_factor": 0.4,
            "game_options": {"max_score": 15, "particle_size": 30.0},
        }
        config_file = tmp_path / "test_profile.json"
        config_file.write_text(json.dumps(config_data))

        config = load_game_profile(config_file)

        assert config.pose_smoothing_factor == 0.4
        assert config.game_options["max_score"] == 15
        assert config.game_options["particle_size"] == 30.0

    def test_uses_defaults_for_missing_fields(self, tmp_path: Path) -> None:
        """Si el JSON no tiene un campo, se usa el default del modelo."""
        config_data = {"game_options": {"custom_flag": True}}
        config_file = tmp_path / "minimal.json"
        config_file.write_text(json.dumps(config_data))

        config = load_game_profile(config_file)

        assert config.pose_smoothing_factor == 0.3  # default
        assert config.game_options["custom_flag"] is True

    def test_raises_on_invalid_json_content(self, tmp_path: Path) -> None:
        """Si el JSON tiene valores inválidos, debe fallar la validación de Pydantic."""
        config_data = {"pose_smoothing_factor": 2.0}  # inválido
        config_file = tmp_path / "invalid.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError, match="pose_smoothing_factor"):
            load_game_profile(config_file)


class TestGameSettingsProfile:
    def test_game_settings_has_profile_name_default_normal(self) -> None:
        """GameSettings debe tener profile_name='normal' por defecto."""
        settings = GameSettings()
        assert settings.profile_name == "normal"

    def test_game_settings_no_longer_has_legacy_game_fields(self) -> None:
        """GameSettings ya no debe tener campos específicos de juego (SRP)."""
        settings = GameSettings()
        assert not hasattr(settings, "gravity")
        assert not hasattr(settings, "burst_count")
        assert not hasattr(settings, "max_particles")
        assert not hasattr(settings, "palette")
