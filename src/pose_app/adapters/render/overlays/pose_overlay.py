"""
Renderer auxiliar para dibujar la pose (esqueleto) sobre una superficie Pygame.

Es una utilidad reutilizable, NO un puerto ni un adaptador completo.
Se usa por composición desde el decorador PoseDebugOverlay.
"""

from typing import Any

import pygame

from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render.overlay_port import OverlayPort
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pose_overlay")


class PoseOverlayRenderer:
    """
    Dibuja un esqueleto de pose sobre una superficie Pygame.

    Características:
    - Configurable: colores, anchos, radios, umbral de visibilidad.
    - Solo dibuja landmarks visibles (visibility >= min_visibility).
    - No depende del tamaño de la ventana: se le pasa explícitamente.
    """

    # Conexiones por defecto del esqueleto humano (Mediapipe)
    DEFAULT_CONNECTIONS: tuple[tuple[str, str], ...] = (
        # Brazos
        ("left_shoulder", "left_elbow"),
        ("left_elbow", "left_wrist"),
        ("right_shoulder", "right_elbow"),
        ("right_elbow", "right_wrist"),
        # Hombros
        ("left_shoulder", "right_shoulder"),
        # Torso
        ("left_shoulder", "left_hip"),
        ("right_shoulder", "right_hip"),
        ("left_hip", "right_hip"),
        # Piernas
        ("left_hip", "left_knee"),
        ("left_knee", "left_ankle"),
        ("right_hip", "right_knee"),
        ("right_knee", "right_ankle"),
        # Cabeza
        ("left_shoulder", "nose"),
        ("right_shoulder", "nose"),
    )

    def __init__(
        self,
        connections: tuple[tuple[str, str], ...] | None = None,
        line_color: tuple[int, int, int] = (255, 255, 255),
        line_width: int = 3,
        joint_color: tuple[int, int, int] = (0, 255, 0),
        joint_radius: int = 6,
        min_visibility: float = 0.5,
    ):
        self._connections = (
            tuple(connections) if connections else self.DEFAULT_CONNECTIONS
        )
        self._line_color = line_color
        self._line_width = line_width
        self._joint_color = joint_color
        self._joint_radius = joint_radius
        self._min_visibility = min_visibility

    def draw(
        self,
        surface: pygame.Surface,
        landmarks: list[PoseLandmark],
        window_size: tuple[int, int],
    ) -> None:
        """
        Dibuja el esqueleto en la superficie.

        Args:
            surface: Superficie Pygame donde dibujar.
            landmarks: Landmarks de la pose (puede estar vacío).
            window_size: (width, height) para escalar coordenadas normalizadas.
        """
        if not landmarks:
            return

        width, height = window_size

        # Índice por nombre, solo landmarks visibles
        lm_by_name: dict[str, PoseLandmark] = {
            lm.name: lm
            for lm in landmarks
            if lm.name and lm.visibility >= self._min_visibility
        }

        # 1. Líneas (conexiones)
        for name_a, name_b in self._connections:
            lm_a = lm_by_name.get(name_a)
            lm_b = lm_by_name.get(name_b)

            if lm_a is None or lm_b is None:
                continue

            pygame.draw.line(
                surface,
                self._line_color,
                self._to_pixels(lm_a, width, height),
                self._to_pixels(lm_b, width, height),
                self._line_width,
            )

        # 2. Puntos (articulaciones)
        for lm in lm_by_name.values():
            pygame.draw.circle(
                surface,
                self._joint_color,
                self._to_pixels(lm, width, height),
                self._joint_radius,
            )

    @staticmethod
    def _to_pixels(
        landmark: PoseLandmark,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Convierte coordenadas normalizadas (0-1) a píxeles."""
        return (int(landmark.x * width), int(landmark.y * height))


class PoseOverlay(OverlayPort):
    """Overlay que dibuja el esqueleto de pose."""

    def __init__(
        self,
        connections: tuple[tuple[str, str], ...] | None = None,
        line_color: tuple[int, int, int] = (255, 255, 255),
        line_width: int = 3,
        joint_color: tuple[int, int, int] = (0, 255, 0),
        joint_radius: int = 6,
        min_visibility: float = 0.5,
        mirror: bool = False,
    ) -> None:
        self._renderer = PoseOverlayRenderer(
            connections=connections,
            line_color=line_color,
            line_width=line_width,
            joint_color=joint_color,
            joint_radius=joint_radius,
            min_visibility=min_visibility,
        )

        self._mirror = mirror

    def draw(
        self,
        surface: Any,
        landmarks: list[PoseLandmark] | None = None,
    ) -> None:
        """
        Dibuja el esqueleto sobre la superficie.

        Args:
            surface: Superficie Pygame.
            landmarks: Landmarks de pose (None o vacío).
        """
        if landmarks is None or not landmarks:
            return

        if self._mirror:
            landmarks = self._mirror_landmarks(landmarks)

        width, height = surface.get_size()
        self._renderer.draw(surface, landmarks, (width, height))

    @staticmethod
    def _mirror_landmarks(landmarks: list[PoseLandmark]) -> list[PoseLandmark]:
        """
        Devuelve copias espejadas (x → 1-x).
        No muta los landmarks originales.
        """
        return [
            PoseLandmark(
                x=1.0 - lm.x,
                y=lm.y,
                z=lm.z,
                visibility=lm.visibility,
                name=lm.name,
            )
            for lm in landmarks
        ]

    def close(self) -> None:
        """Libera recursos. No hay recursos que liberar."""
