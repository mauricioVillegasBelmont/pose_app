"""
Puerto para elementos visuales superpuestos (overlays).

Los overlays se dibujan sobre la superficie y reciben landmarks
para elementos dependientes de pose (debug, efectos).
"""

from abc import ABC, abstractmethod
from typing import Any

from pose_app.domain.entities.pose_landmark import PoseLandmark


class OverlayPort(ABC):
    """Elemento visual superpuesto (debug, efectos)."""

    @abstractmethod
    def draw(
        self,
        surface: Any,
        landmarks: list[PoseLandmark] | None = None,
    ) -> None:
        """
        Dibuja el overlay sobre la superficie.

        Args:
            surface: Superficie de dibujo (tipo específico del adaptador).
            landmarks: Landmarks actuales de pose. Puede ser None o lista vacía.
                El SceneManager siempre pasará landmarks (puede ser []).
                Los overlays deciden si los usan.
        """

    @abstractmethod
    def close(self) -> None:
        """
        Cierra y libera recursos.

        Debe ser idempotente.
        """
