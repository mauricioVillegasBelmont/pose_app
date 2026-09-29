"""
Gestos reconocibles por el GesturesGame.

Definirlos como Enum (en lugar de strings sueltos) evita typos y
hace el código autocompletable.
"""

from enum import Enum


class Gesture(str, Enum):
    """
    Gestos soportados.

    Hereda de `str` para que sea JSON-serializable directamente.
    Ejemplo: `Gesture.HAND_UP.value == "hand_up"`.
    """

    HAND_UP = "hand_up"
    GREETING = "greeting"
    ARMS_CROSSED = "arms_crossed"
    T_POSE = "t_pose"
    SQUAT = "squat"
    ONE_LEG_BALANCE = "one_leg_balance"

    @property
    def display_name(self) -> str:
        """Nombre legible para logs."""
        return self.value.replace("_", " ").title()