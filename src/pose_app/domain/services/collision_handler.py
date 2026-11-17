"""
Handlers de colisión para cursores de interacción.

Define el protocolo para calcular el punto de colisión de un cursor
a partir de landmarks del esqueleto, y proporciona implementaciones concretas.
"""

from __future__ import annotations

from typing import Protocol

from pose_app.domain.entities.hand_landmark_config import HandLandmarkConfig
from pose_app.domain.entities.pose_landmark import PoseLandmark


class CollisionHandler(Protocol):
    """
    Contrato para calcular el punto de colisión de un cursor.

    Implementaciones:
    - CentroidCollisionHandler: Promedia landmarks visibles y aplica offset.
    """

    def calculate_point(
        self,
        landmarks: list[PoseLandmark],
        config: HandLandmarkConfig,
    ) -> tuple[float, float] | None:
        """
        Calcula el punto de colisión (x, y) normalizado.

        Args:
            landmarks: Lista de landmarks del esqueleto.
            config: Configuración de landmarks y offset.

        Returns:
            Tupla (x, y) normalizada (0-1), o None si no hay landmarks suficientes.
        """
        ...


class CentroidCollisionHandler:
    """
    Calcula el centroide de landmarks visibles y aplica un offset.

    Filtra landmarks con visibility < 0.5, promedia los restantes,
    y aplica el offset configurado. Si no hay landmarks visibles,
    retorna None.
    """

    def calculate_point(
        self,
        landmarks: list[PoseLandmark],
        config: HandLandmarkConfig,
    ) -> tuple[float, float] | None:
        """
        Calcula el centroide de landmarks visibles con offset.

        Args:
            landmarks: Lista de landmarks del esqueleto.
            config: Configuración de landmarks y offset.

        Returns:
            Tupla (x, y) normalizada (0-1) con offset aplicado,
            o None si no hay landmarks visibles.
        """
        # Filtrar landmarks configurados y visibles
        visible_landmarks = []
        for landmark in landmarks:
            if landmark.name in config.landmark_names and landmark.is_visible():
                visible_landmarks.append(landmark)

        # Si no hay landmarks visibles, retornar None
        if not visible_landmarks:
            return None

        # Calcular centroide (promedio)
        sum_x = sum(lm.x for lm in visible_landmarks)
        sum_y = sum(lm.y for lm in visible_landmarks)
        count = len(visible_landmarks)

        centroid_x = sum_x / count
        centroid_y = sum_y / count

        # Aplicar offset
        final_x = centroid_x + config.offset_x
        final_y = centroid_y + config.offset_y

        return (final_x, final_y)
