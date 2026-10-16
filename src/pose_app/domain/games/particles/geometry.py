"""
Geometría espacial del juego de partículas.

Conceptos puramente geométricos:
- Workspace: zona rectangular normalizada.
- detect_collisions: distancia entre partículas y landmarks de toque.

Sin dependencias de framework. Sin lógica de presentación.
Testeable en aislamiento con pytest + hypothesis.
"""

import math
import random
from dataclasses import dataclass

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.pose_landmark import PoseLandmark

# ==========================================
# Constantes de toque
# ==========================================

TOUCH_LANDMARKS: frozenset[str] = frozenset(
    {
        "left_wrist",
        "right_wrist",
        "left_index",
        "right_index",
    }
)
"""
Landmarks de pose que se consideran "tocadores" para la detección
de colisiones. Cualquier otro landmark (nariz, rodilla, etc.) no
cuenta.

Renombrado desde HAND_LANDMARKS para reflejar que el juego podría
usar otros puntos de contacto (pies, cabeza, etc.) en el futuro.
"""


# ==========================================
# Workspace
# ==========================================


@dataclass(frozen=True)
class Workspace:
    """
    Área rectangular normalizada (0-1) donde pueden aparecer partículas.

    Las coordenadas están normalizadas para ser coherentes con los
    landmarks de pose (también normalizados). La conversión a píxeles
    se hace al usar el workspace, no al definirlo.

    Attributes:
        x_min: borde izquierdo (0-1).
        x_max: borde derecho (0-1).
        y_min: borde superior (0-1).
        y_max: borde inferior (0-1).

    Raises:
        ValueError: si los márgenes son inválidos (x_min >= x_max, etc.).
    """

    x_min: float = 0.2
    x_max: float = 0.8
    y_min: float = 0.15
    y_max: float = 0.85

    def __post_init__(self) -> None:
        """Valida que los márgenes sean coherentes."""
        if not (0.0 <= self.x_min < self.x_max <= 1.0):
            raise ValueError(
                f"x_min/x_max inválidos: [{self.x_min}, {self.x_max}]. "
                f"Debe cumplirse 0 <= x_min < x_max <= 1."
            )
        if not (0.0 <= self.y_min < self.y_max <= 1.0):
            raise ValueError(
                f"y_min/y_max inválidos: [{self.y_min}, {self.y_max}]. "
                f"Debe cumplirse 0 <= y_min < y_max <= 1."
            )

    def random_point(self, rng: random.Random) -> tuple[float, float]:
        """
        Devuelve un punto aleatorio normalizado dentro del workspace.

        Args:
            rng: generador aleatorio (inyectable para tests deterministas).

        Returns:
            (x, y) normalizados, dentro de los límites del workspace.
        """
        return (
            rng.uniform(self.x_min, self.x_max),
            rng.uniform(self.y_min, self.y_max),
        )

    def contains(self, x: float, y: float) -> bool:
        """
        Verifica si un punto normalizado está dentro del workspace.

        Args:
            x: coordenada x normalizada (0-1).
            y: coordenada y normalizada (0-1).

        Returns:
            True si el punto está dentro (incluye bordes).
        """
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


# ==========================================
# Detección de colisiones
# ==========================================


def detect_collisions(
    particles: list[Particle],
    landmarks: list[PoseLandmark],
    screen_width: int,
    screen_height: int,
    hit_radius: float = 30.0,
    touch_landmarks: frozenset[str] = TOUCH_LANDMARKS,
    min_visibility: float = 0.5,
) -> tuple[list[Particle], int]:
    """
    Detecta colisiones entre landmarks de toque y partículas.

    Una partícula colisiona si su distancia euclidiana a algún
    landmark de toque visible es menor que `hit_radius`.

    Args:
        particles: partículas activas (coordenadas en píxeles).
        landmarks: landmarks de pose (coordenadas normalizadas).
        screen_width: ancho de pantalla (para convertir landmarks).
        screen_height: alto de pantalla (para convertir landmarks).
        hit_radius: radio de colisión en píxeles.
        touch_landmarks: nombres de landmarks considerados "tocadores".
        min_visibility: visibilidad mínima para considerar un landmark.

    Returns:
        (partículas_no_tocadas, número_de_partículas_tocadas).

    Raises:
        ValueError: si `screen_width <= 0` o `screen_height <= 0`.

    Contrato:
        - Solo landmarks de toque visibles (visibility >= min_visibility).
        - Cada partícula cuenta como máximo 1 vez.
        - Si no hay landmarks de toque visibles, no hay colisiones.
        - Orden de `partículas_no_tocadas` preserva el orden original.
    """
    if screen_width <= 0:
        raise ValueError(f"screen_width debe ser > 0, recibido: {screen_width}")
    if screen_height <= 0:
        raise ValueError(f"screen_height debe ser > 0, recibido: {screen_height}")

    hands = [
        lm
        for lm in landmarks
        if lm.name in touch_landmarks and lm.visibility >= min_visibility
    ]

    if not hands:
        return (list(particles), 0)

    remaining: list[Particle] = []
    hits = 0

    hand_positions_px = [
        (hand.x * screen_width, hand.y * screen_height) for hand in hands
    ]

    for particle in particles:
        touched = False
        for hx, hy in hand_positions_px:
            distance = math.hypot(particle.x - hx, particle.y - hy)
            if distance < hit_radius:
                touched = True
                break

        if touched:
            hits += 1
        else:
            remaining.append(particle)

    return (remaining, hits)
