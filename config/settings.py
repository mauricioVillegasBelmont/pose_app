"""
Configuración centralizada de la aplicación.

Usa pydantic-settings para cargar desde:
1. Variables de entorno (prioridad alta)
2. Archivo .env
3. Valores por defecto (prioridad baja)
"""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CameraSettings(BaseSettings):
    """Configuración de la cámara."""

    model_config = SettingsConfigDict(
        env_prefix="CAMERA_",  # CAMERA_ID, CAMERA_WIDTH, etc.
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    id: int = Field(default=0, ge=0, description="ID de la cámara (0 = por defecto)")
    width: int = Field(default=640, ge=160, le=1920, description="Ancho de captura")
    height: int = Field(default=480, ge=120, le=1080, description="Alto de captura")
    fps: int = Field(default=30, ge=1, le=120, description="FPS objetivo")


class PoseSettings(BaseSettings):
    """Configuración del estimador de pose."""

    model_config = SettingsConfigDict(
        env_prefix="POSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["mediapipe", "mock"] = Field(
        default="mediapipe",
        description="Adaptador de estimación a usar"
    )
    model_complexity: int = Field(
        default=1, ge=0, le=2,
        description="Complejidad del modelo Mediapipe (0=rápido, 2=preciso)"
    )
    min_detection_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Confianza mínima para detección"
    )
    min_tracking_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Confianza mínima para tracking"
    )


class RenderSettings(BaseSettings):
    """Configuración del renderizador."""

    model_config = SettingsConfigDict(
        env_prefix="RENDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["pygame", "mock"] = Field(
        default="pygame",
        description="Adaptador de render a usar"
    )
    width: int = Field(default=800, ge=320, le=3840)
    height: int = Field(default=600, ge=240, le=2160)
    title: str = Field(default="Pose AR App")
    target_fps: int = Field(default=60, ge=15, le=144)


class GameSettings(BaseSettings):
    """Configuración del juego."""

    model_config = SettingsConfigDict(
        env_prefix="GAME_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    type: Literal["particles", "color"] = Field(
        default="particles",
        description="Tipo de juego a ejecutar"
    )
    gravity: float = Field(default=0.08, ge=0.0, le=1.0)
    burst_count: int = Field(default=5, ge=1, le=50, description="Partículas por landmark")
    max_particles: int = Field(default=2000, ge=100, le=10000)
    palette: Literal["fire", "ocean", "forest", "neon"] = Field(
        default="fire",
        description="Paleta de colores (solo para juego de color)"
    )


class LoggingSettings(BaseSettings):
    """Configuración de logging."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["json", "console"] = "console"
    file: str | None = Field(default=None, description="Archivo de log (opcional)")

class APISettings(BaseSettings):
    """Configuración de la API REST."""

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(
        default=True,
        description="Si la API debe iniciarse"
    )
    host: str = Field(default="0.0.0.0", description="Host de la API")
    port: int = Field(default=8000, ge=1024, le=65535, description="Puerto")
    cors_origins: list[str] = Field(
        default=["*"],
        description="Orígenes permitidos para CORS"
    )

class Settings(BaseSettings):
    """
    Configuración raíz de la aplicación.

    Agrupa todas las sub-configuraciones en una sola instancia.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Pose AR App")
    environment: Literal["development", "production", "testing"] = "development"
    debug: bool = Field(default=False)

    # Sub-configuraciones (se cargan desde sus propios prefijos)
    camera: CameraSettings = Field(default_factory=CameraSettings)
    pose: PoseSettings = Field(default_factory=PoseSettings)
    render: RenderSettings = Field(default_factory=RenderSettings)
    game: GameSettings = Field(default_factory=GameSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    api: APISettings = Field(default_factory=APISettings)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """En producción, forzamos debug=False."""
        if v == "production":
            # En producción, no queremos debug activo
            pass
        return v


# Singleton: una sola instancia de configuración en toda la app
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Obtiene la configuración global (singleton).

    Returns:
        Instancia única de Settings.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Resetea el singleton (útil para tests)."""
    global _settings
    _settings = None