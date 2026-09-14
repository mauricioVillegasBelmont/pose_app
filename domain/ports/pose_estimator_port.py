"""
Puerto de estimación de pose.

Define el contrato que cualquier adaptador de estimación de pose debe cumplir.
El dominio NO sabe si usamos Mediapipe, OpenPose, YOLO-Pose, o un mock.
Solo sabe que hay algo que le da landmarks a partir de un frame.
"""

from abc import ABC, abstractmethod
from typing import Self

import numpy as np

from domain.entities.pose_landmark import PoseLandmark


class PoseEstimatorPort(ABC):
    """
    Puerto (interfaz) para estimación de pose humana.

    Cualquier adaptador (Mediapipe, OpenPose, Mock) debe implementar
    estos métodos para ser usable por los casos de uso del dominio.
    """

    @abstractmethod
    def estimate(self, frame: np.ndarray) -> list[PoseLandmark]:
        """
        Estima la pose a partir de un frame de imagen.

        Args:
            frame: Imagen en formato BGR (H, W, 3) como numpy array.
                   OpenCV usa BGR por defecto, así que todos los adaptadores
                   deben respetar este formato.

        Returns:
            Lista de PoseLandmark detectados en el frame.
            Si no hay persona detectada, devuelve lista vacía.

        Note:
            - Los landmarks deben venir en coordenadas normalizadas (0-1).
            - Los landmarks con visibilidad baja (< 0.5) pueden ser omitidos
              por el adaptador, pero eso es decisión de cada implementación.
        """

    @abstractmethod
    def get_landmark_names(self) -> list[str]:
        """
        Devuelve los nombres de los landmarks soportados por este adaptador.

        Returns:
            Lista de strings con nombres de landmarks (ej: 'left_shoulder').
            Útil para saber qué landmarks puede devolver el adaptador.

        Note:
            Diferentes adaptadores pueden devolver diferentes cantidades:
            - Mediapipe: 33 landmarks
            - OpenPose: 25 landmarks (formato BODY_25)
            - YOLO-Pose: 17 landmarks (formato COCO)
        """

    def close(self) -> None:
        """
        Libera recursos del adaptador (opcional).

        Por defecto no hace nada, pero los adaptadores que usen
        recursos externos (GPU, modelos ML) pueden sobrescribirlo.
        """

    def __enter__(self) -> Self:
        """
        Soporte para context manager (with ... as ...).
        Permite usar: with MediapipeAdapter() as estimator: ...
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Soporte para context manager: cierra recursos al salir."""
        self.close()