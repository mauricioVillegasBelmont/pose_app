"""
Excepciones del dominio.

Define una jerarquía clara:
- AppError (base)
  - ConfigurationError (falla al inicio)
  - InfrastructureError (adaptadores)
    - CameraError
    - PoseEstimationError
    - RenderError
  - DomainError (reglas de negocio)
"""


class AppError(Exception):
    """Excepción base de la aplicación."""

    def __init__(self, message: str, *, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            return f"{self.message} | context={self.context}"
        return self.message


# ==========================================
# Errores de configuración (fail-fast)
# ==========================================

class ConfigurationError(AppError):
    """Error en la configuración (variables de entorno inválidas, etc.)."""


# ==========================================
# Errores de infraestructura (adaptadores)
# ==========================================

class InfrastructureError(AppError):
    """Error genérico de infraestructura."""


class CameraError(InfrastructureError):
    """Error relacionado con la cámara."""


class CameraNotAvailableError(CameraError):
    """La cámara no está disponible (desconectada, ocupada)."""


class PoseEstimationError(InfrastructureError):
    """Error en la estimación de pose."""


class RenderError(InfrastructureError):
    """Error en el renderizado."""


# ==========================================
# Errores de dominio
# ==========================================

class DomainError(AppError):
    """Error en las reglas de negocio."""
