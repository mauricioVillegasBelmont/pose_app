"""
Puerto de interacción con la pose.

Define el contrato para una fachada que abstrae la complejidad de los landmarks crudos,
aplica suavizado (smoothing) y proporciona consultas de alto nivel para la lógica del juego.
"""

from abc import ABC, abstractmethod
from typing import Literal

from pose_app.domain.entities.pose_landmark import PoseLandmark


class PoseInteractionPort(ABC):
    """
    Fachada de interacción con la pose.
    Abstrae la complejidad de los landmarks crudos, aplicando suavizado
    y proporcionando consultas de alto nivel para la lógica del juego.
    """

    @abstractmethod
    def update(self, landmarks: list["PoseLandmark"]) -> None:
        """
        Actualiza el estado interno con los nuevos landmarks.
        Aquí es donde se aplica el suavizado (ej: EMA) para evitar
        el 'jitter' o temblor inherente a la estimación de pose en tiempo real.
        """

    @abstractmethod
    def get_hand_position(
        self, hand: Literal["left", "right"], screen_w: int, screen_h: int
    ) -> tuple[float, float] | None:
        """
        Devuelve la posición (x, y) en píxeles de la pantalla de la muñeca
        (o centro de la mano) indicada, ya suavizada.
        Retorna None si la mano no es visible o la confianza es baja.
        """

    @abstractmethod
    def is_touching(
        self,
        target_x: float,
        target_y: float,
        radius: float,
        screen_w: int,
        screen_h: int,
        cursor_id: str | None = None,  # ← NUEVO: opcional
    ) -> bool:
        """
        Verifica si algún cursor (o uno específico) está intersectando
        con un círculo definido por (target_x, target_y, radius) en la pantalla.

        Args:
            target_x: Posición X del objetivo en píxeles.
            target_y: Posición Y del objetivo en píxeles.
            radius: Radio del objetivo en píxeles.
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.
            cursor_id: Identificador del cursor específico. Si es None,
                    verifica todos los cursores activos.
        """
