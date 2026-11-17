# test_settings.py
from pose_app.config.settings import get_settings, reset_settings


def test_settings_load():
    reset_settings()
    settings = get_settings()

    print(f"App: {settings.app_name}")
    print(f"Cámara: {settings.camera.width}x{settings.camera.height}")
    print(f"Pose: {settings.pose.provider}")
    print(f"Render: {settings.render.provider}")
    print(f"Juego: {settings.game.type}")
    print(f"Log: {settings.logging.level}")

    # Valida tipos
    assert isinstance(settings.camera.id, int)
    assert isinstance(settings.pose.provider, str)
    assert settings.camera.width > 0
    print("✅ Configuración cargada correctamente")


def test_camera_settings_includes_min_nonzero_ratio() -> None:
    """CameraSettings expone el umbral de validación de frames."""
    import pytest
    from pydantic import ValidationError

    from pose_app.config.settings import CameraSettings

    settings = CameraSettings()
    assert settings.min_nonzero_ratio == 0.3

    # Validación: fuera de [0.0, 1.0] debe fallar
    with pytest.raises(ValidationError):
        CameraSettings(min_nonzero_ratio=1.5)

    with pytest.raises(ValidationError):
        CameraSettings(min_nonzero_ratio=-0.1)


if __name__ == "__main__":
    test_settings_load()
