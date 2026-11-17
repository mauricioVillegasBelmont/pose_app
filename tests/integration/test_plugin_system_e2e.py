"""
Test end-to-end del plugin system con mocks.

Verifica:
1. El Container carga plugins.
2. create_game() funciona sin if/elif.
3. El estado se registra correctamente.
"""

import pytest

from pose_app.config.game_profile import GameProfileConfig
from pose_app.config.settings import Settings, reset_settings
from pose_app.infrastructure.di.container import Container


@pytest.fixture
def mock_settings(monkeypatch):
    """Settings con todo mock, sin hardware."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("POSE_PROVIDER", "mock")
    monkeypatch.setenv("RENDER_PROVIDER", "mock")
    reset_settings()
    return Settings()


def test_container_creates_particles_game(mock_settings, monkeypatch) -> None:
    monkeypatch.setenv("GAME_TYPE", "particles")
    reset_settings()
    settings = Settings()

    container = Container(settings)
    gameplay_config = GameProfileConfig()
    game = container.create_game(gameplay_config=gameplay_config)

    assert game is not None
    assert game.state.game_id == "particles"


def test_container_creates_color_game(mock_settings, monkeypatch) -> None:
    monkeypatch.setenv("GAME_TYPE", "color")
    reset_settings()
    settings = Settings()

    container = Container(settings)
    gameplay_config = GameProfileConfig()
    game = container.create_game(gameplay_config=gameplay_config)

    assert game is not None
    assert game.state.game_id == "color"


def test_container_raises_on_unknown_game(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("GAME_TYPE", "unknown")
    reset_settings()
    settings = Settings()

    from pose_app.infrastructure.errors.exceptions import ConfigurationError

    container = Container(settings)
    gameplay_config = GameProfileConfig()
    with pytest.raises(ConfigurationError):
        container.create_game(gameplay_config=gameplay_config)
