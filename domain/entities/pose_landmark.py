from dataclasses import dataclass


@dataclass(frozen=True)  # Inmutable, como debe ser una entidad de dominio
class PoseLandmark:
    """Representa un punto clave del esqueleto humano."""

    x: float  # Normalizado 0-1 (ancho)
    y: float  # Normalizado 0-1 (alto)
    z: float  # Profundidad (relativa)
    visibility: float  # 0-1 (qué tan visible está)
    name: str | None = None  # Ej: "left_shoulder", "right_wrist"

    def is_visible(self) -> bool:
        """Regla de negocio: un landmark es útil si tiene visibilidad > 0.5"""
        return self.visibility > 0.5

    def distance_to(self, other: "PoseLandmark") -> float:
        """Distancia euclidiana en el plano 2D (ignora z por simplicidad)."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
