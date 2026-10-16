"""
Reglas de progresión y presentación del juego.

Conceptos de diseño de juego:
- color_for_score: feedback visual según puntuación.
- particles_per_round: dificultad progresiva.
- is_winner: condición de victoria.

Específicas de este juego, no reutilizables en otros.
"""

from pose_app.domain.entities.color import RGBColor

# ==========================================
# Paleta de fondos por puntuación
# ==========================================

BACKGROUND_COLORS: tuple[tuple[int, int, int], ...] = (
    (20, 20, 20),  # 0 puntos: negro
    (60, 60, 80),  # 1-2 puntos: gris azulado
    (60, 60, 120),  # 3-5 puntos: azul
    (120, 60, 30),  # 6+ puntos: naranja oscuro
)
"""Paleta de fondos ordenada de menor a mayor puntuación."""


# ==========================================
# Reglas de presentación
# ==========================================


def color_for_score(score: int) -> RGBColor:
    """
    Devuelve el color de fondo correspondiente a la puntuación.

    Reglas:
        - score <= 0 → negro (20, 20, 20)
        - 1 <= score <= 2 → gris azulado (60, 60, 80)
        - 3 <= score <= 5 → azul (60, 60, 120)
        - score >= 6 → naranja oscuro (120, 60, 30)

    Args:
        score: puntuación actual.

    Returns:
        RGBColor correspondiente.

    Contrato:
        - Nunca lanza excepción para ningún score (incluso negativos).
        - Es una función pura.
    """
    if score <= 0:
        rgb = BACKGROUND_COLORS[0]
    elif score <= 2:
        rgb = BACKGROUND_COLORS[1]
    elif score <= 5:
        rgb = BACKGROUND_COLORS[2]
    else:
        rgb = BACKGROUND_COLORS[3]

    return RGBColor(r=rgb[0], g=rgb[1], b=rgb[2])


# ==========================================
# Reglas de dificultad
# ==========================================


def particles_per_round(round_number: int) -> int:
    """
    Cantidad de partículas a spawnear según la ronda.

    Reglas:
        - Ronda 1 → 2 partículas
        - Ronda 2 → 3
        - Ronda 3 → 4
        - Ronda 4+ → 5 (máximo)
        - Ronda 0 o negativa → 2 (mínimo)

    Args:
        round_number: número de ronda (1-indexed).

    Returns:
        Cantidad de partículas para esa ronda.

    Contrato:
        - Siempre retorna >= 2 y <= 5.
        - Es una función pura.
    """
    MIN_PARTICLES = 2
    MAX_PARTICLES = 5

    particles = MIN_PARTICLES + max(0, round_number - 1)

    return min(particles, MAX_PARTICLES)


# ==========================================
# Reglas de fin de juego
# ==========================================


def is_winner(score: int, max_score: int) -> bool:
    """
    Verifica si el jugador ha alcanzado la puntuación máxima.

    Args:
        score: puntuación actual.
        max_score: puntuación objetivo.

    Returns:
        True si score >= max_score.

    Contrato:
        - Es una función pura.
        - Para max_score <= 0, retorna True siempre (no se juega).
    """
    return score >= max_score
