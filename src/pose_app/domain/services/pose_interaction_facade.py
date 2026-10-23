"""
Implementación de la fachada de interacción con la pose.

Aplica un filtro de Suavizado Exponencial (EMA) para mejorar el "game feel"
y encapsula la lógica de colisión para que los juegos no manipulen landmarks crudos.
"""

from typing import Literal

from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.pose_interaction_port import PoseInteractionPort


class PoseInteractionFacade(PoseInteractionPort):
    """
    Implementación de la fachada con suavizado Exponential Moving Average (EMA)
    y lógica de colisión unificada.
    """

    def __init__(self, smoothing_factor: float = 0.3):
        """
        Args:
            smoothing_factor: Valor entre 0.0 y 1.0 que controla la intensidad del suavizado.
                - 0.3 (Recomendado): Buen equilibrio. Suaviza el temblor sin introducir lag perceptible.
                - < 0.2 (Ej: 0.1): Suavizado muy agresivo. El movimiento será muy fluido,
                  pero se sentirá "pesado" o con retraso (input lag).
                - > 0.5 (Ej: 0.8): Suavizado ligero. Responde muy rápido, pero se notará
                  el 'jitter' o temblor natural de MediaPipe.
                - 1.0: Sin suavizado (comportamiento crudo).
        """
        if not (0.0 < smoothing_factor <= 1.0):
            raise ValueError("smoothing_factor debe estar entre 0.0 (excluido) y 1.0")

        self._smoothing_factor = smoothing_factor

        # Estado suavizado interno (coordenadas normalizadas 0-1)
        self._smoothed_left: tuple[float, float] | None = None
        self._smoothed_right: tuple[float, float] | None = None

    def update(self, landmarks: list[PoseLandmark]) -> None:
        """Aplica filtro EMA a las muñecas detectadas."""
        left_wrist = self._find_landmark(landmarks, "left_wrist")
        right_wrist = self._find_landmark(landmarks, "right_wrist")

        if left_wrist and left_wrist.is_visible():
            self._smoothed_left = self._ema(
                self._smoothed_left, (left_wrist.x, left_wrist.y)
            )
        else:
            # Si se pierde la mano, reseteamos para evitar saltos bruscos al reaparecer
            self._smoothed_left = None

        if right_wrist and right_wrist.is_visible():
            self._smoothed_right = self._ema(
                self._smoothed_right, (right_wrist.x, right_wrist.y)
            )
        else:
            self._smoothed_right = None

    def get_hand_position(
        self, hand: Literal["left", "right"], screen_w: int, screen_h: int
    ) -> tuple[float, float] | None:
        smoothed = self._smoothed_left if hand == "left" else self._smoothed_right
        if smoothed is None:
            return None

        # Convertir de normalizado (0-1) a píxeles de pantalla
        return (smoothed[0] * screen_w, smoothed[1] * screen_h)

    def is_touching(
        self,
        target_x: float,
        target_y: float,
        radius: float,
        screen_w: int,
        screen_h: int,
    ) -> bool:
        """
        Evalúa si la mano izquierda o derecha suavizada toca el objetivo.
        """
        left_pos = self.get_hand_position("left", screen_w, screen_h)
        if left_pos and self._distance(left_pos, (target_x, target_y)) <= radius:
            return True

        right_pos = self.get_hand_position("right", screen_w, screen_h)
        return bool(
            right_pos and self._distance(right_pos, (target_x, target_y)) <= radius
        )
        # if right_pos and self._distance(right_pos, (target_x, target_y)) <= radius:
        #     return True
        # return False

    # ==========================================
    # Métodos auxiliares privados
    # ==========================================

    def _find_landmark(
        self, landmarks: list[PoseLandmark], name: str
    ) -> PoseLandmark | None:
        """Búsqueda case-insensitive robusta."""
        name_lower = name.lower()
        for lm in landmarks:
            if lm.name and lm.name.lower() == name_lower:
                return lm
        return None

    def _ema(
        self, previous: tuple[float, float] | None, current: tuple[float, float]
    ) -> tuple[float, float]:
        """Exponential Moving Average para suavizado."""
        if previous is None:
            return current  # Primer frame, sin historial

        alpha = self._smoothing_factor
        smooth_x = alpha * current[0] + (1 - alpha) * previous[0]
        smooth_y = alpha * current[1] + (1 - alpha) * previous[1]
        return (smooth_x, smooth_y)

    def _distance(self, p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Distancia euclidiana 2D."""
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
