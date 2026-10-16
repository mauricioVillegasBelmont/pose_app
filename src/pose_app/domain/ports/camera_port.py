from abc import ABC, abstractmethod
from typing import Self

import numpy as np


class CameraPort(ABC):
    """Puerto de entrada: captura de frames de cámara."""

    @abstractmethod
    def start(self) -> None:
        """Inicia la captura de video."""

    @abstractmethod
    def stop(self) -> None:
        """Detiene la captura de video."""

    @abstractmethod
    def get_frame(self) -> np.ndarray | None:
        """
        Obtiene el último frame capturado.
        Returns: Array numpy (H, W, 3) en formato BGR, o None si no hay frame.
        """

    @abstractmethod
    def is_running(self) -> bool:
        """Indica si la cámara está activa."""

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
