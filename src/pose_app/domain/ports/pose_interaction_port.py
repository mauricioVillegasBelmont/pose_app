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
    ) -> bool:
        """
        Verifica si alguna mano visible (izquierda o derecha) está intersectando
        con un círculo definido por (target_x, target_y, radius) en la pantalla.
        """
