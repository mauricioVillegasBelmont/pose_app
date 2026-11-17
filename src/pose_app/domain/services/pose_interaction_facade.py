"""
Fachada de interacción con la pose.

Gestiona múltiples cursores de interacción (manos, pies, cadera, etc.),
aplica suavizado EMA y gestiona timeout de visibilidad.
"""

from __future__ import annotations

import time
from typing import Literal

from pose_app.domain.entities.hand_landmark_config import HandLandmarkConfig
from pose_app.domain.entities.input_cursor import InputCursor
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.pose_interaction_port import PoseInteractionPort
from pose_app.domain.services.collision_handler import (
    CentroidCollisionHandler,
    CollisionHandler,
)


class PoseInteractionFacade(PoseInteractionPort):
    """
    Fachada que gestiona múltiples cursores de interacción.

    Cada cursor tiene su propia configuración de landmarks, offset,
    radio de colisión y estilo visual. La fachada aplica suavizado EMA
    y gestiona timeout de visibilidad para persistencia ante pérdida
    temporal de landmarks.

    Attributes:
        _cursors: Diccionario de cursores activos (cursor_id → InputCursor).
        _cursor_configs: Diccionario de configuraciones de landmarks por cursor.
        _smoothed_positions: Diccionario de posiciones suavizadas por cursor.
        _collision_handler: Handler para calcular punto de colisión.
        _smoothing_factor: Factor de suavizado EMA (0.0-1.0).
        _hand_timeout: Segundos antes de considerar un cursor como perdido.
    """

    def __init__(
        self,
        smoothing_factor: float = 0.3,
        hand_timeout: float = 2.0,
        cursor_configs: dict[str, HandLandmarkConfig] | None = None,
        collision_handler: CollisionHandler | None = None,
        cursors: list[InputCursor] | None = None,  # ← NUEVO
    ) -> None:
        """
        Inicializa la fachada con configuración de cursores.

        Args:
            smoothing_factor: Factor de suavizado EMA (0.0-1.0).
                              0.3 = equilibrio, <0.2 = más lag, >0.5 = más jitter.
            hand_timeout: Segundos antes de considerar un cursor como perdido.
            cursor_configs: Diccionario de configuraciones por cursor.
                           Si es None, se usan defaults para left_hand y right_hand.
            collision_handler: Handler para calcular punto de colisión.
                             Si es None, se usa CentroidCollisionHandler.
        """
        if not (0.0 < smoothing_factor <= 1.0):
            raise ValueError("smoothing_factor must be between 0.0 (exclusive) and 1.0")

        self._smoothing_factor = smoothing_factor
        self._hand_timeout = hand_timeout
        self._collision_handler = collision_handler or CentroidCollisionHandler()

        # Configuraciones de landmarks por cursor
        if cursor_configs is None:
            self._cursor_configs = {
                "left_hand": HandLandmarkConfig(landmark_names=("left_wrist",)),
                "right_hand": HandLandmarkConfig(landmark_names=("right_wrist",)),
            }
        else:
            self._cursor_configs = cursor_configs

        # Cursores (estado mutable)
        provided = {c.cursor_id: c for c in (cursors or [])}
        self._cursors: dict[str, InputCursor] = {}
        for cursor_id in self._cursor_configs:
            self._cursors[cursor_id] = provided.get(
                cursor_id,
                InputCursor(cursor_id=cursor_id),  # fallback si no vino
            )

        # Posiciones suavizadas (estado interno)
        self._smoothed_positions: dict[str, tuple[float, float] | None] = {
            cursor_id: None for cursor_id in self._cursor_configs
        }

    def update(
        self, landmarks: list[PoseLandmark], current_time: float | None = None
    ) -> None:
        """
        Actualiza todos los cursores con los nuevos landmarks.

        Args:
            landmarks: Lista de landmarks del esqueleto.
            current_time: Timestamp actual (segundos). Si es None, usa time.monotonic().
        """
        if current_time is None:
            current_time = time.monotonic()

        for cursor_id, config in self._cursor_configs.items():
            # 1. Calcular punto crudo con el handler
            raw_point = self._collision_handler.calculate_point(landmarks, config)

            # 2. Suavizar con EMA
            smoothed = self._ema(self._smoothed_positions[cursor_id], raw_point)
            self._smoothed_positions[cursor_id] = smoothed

            # 3. Actualizar el cursor (gestiona timeout)
            cursor = self._cursors[cursor_id]
            cursor.update(smoothed, current_time, self._hand_timeout)

    def get_hand_position(
        self, hand: Literal["left", "right"], screen_w: int, screen_h: int
    ) -> tuple[float, float] | None:
        """
        Obtiene la posición de una mano específica (backward compatibility).

        Args:
            hand: "left" o "right".
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.

        Returns:
            (x, y) en píxeles, o None si el cursor no está visible.
        """
        cursor_id = f"{hand}_hand"
        cursor = self._cursors.get(cursor_id)
        if cursor is None or not cursor.is_visible:
            return None
        return cursor.get_position_pixels(screen_w, screen_h)

    def is_touching(
        self,
        target_x: float,
        target_y: float,
        radius: float,
        screen_w: int,
        screen_h: int,
        cursor_id: str | None = None,  # ← NUEVO: opcional, al final
    ) -> bool:
        """
        Verifica si algún cursor (o uno específico) está tocando un objetivo.

        Args:
            target_x: Posición X del objetivo en píxeles.
            target_y: Posición Y del objetivo en píxeles.
            radius: Radio del objetivo en píxeles.
            screen_w: Ancho de pantalla en píxeles.
            screen_h: Alto de pantalla en píxeles.
            cursor_id: Identificador del cursor específico. Si es None,
                    verifica todos los cursores activos.

        Returns:
            True si algún cursor (o el especificado) está tocando el objetivo.
        """
        if cursor_id is not None:
            # Verificar solo el cursor específico
            return self._check_cursor_touching(
                cursor_id, target_x, target_y, radius, screen_w, screen_h
            )

        # Verificar todos los cursores
        return any(
            self._check_cursor_touching(
                cid, target_x, target_y, radius, screen_w, screen_h
            )
            for cid in self._cursors
        )

    def _check_cursor_touching(
        self,
        cursor_id: str,
        target_x: float,
        target_y: float,
        target_radius: float,
        screen_w: int,
        screen_h: int,
    ) -> bool:
        """Verifica si un cursor específico está tocando un objetivo."""
        cursor = self._cursors.get(cursor_id)
        if cursor is None or not cursor.is_visible or cursor.position is None:
            return False

        cursor_pos = cursor.get_position_pixels(screen_w, screen_h)
        if cursor_pos is None:
            return False

        cursor_radius = cursor.get_collision_radius_pixels(screen_w, screen_h)
        distance = self._distance(cursor_pos, (target_x, target_y))

        return distance <= (cursor_radius + target_radius)

    def get_cursor(self, cursor_id: str) -> InputCursor | None:
        """
        Obtiene un cursor específico (útil para renderizado).

        Args:
            cursor_id: Identificador del cursor.

        Returns:
            InputCursor o None si no existe.
        """
        return self._cursors.get(cursor_id)

    def get_all_cursors(self) -> list[InputCursor]:
        """
        Obtiene todos los cursores activos.

        Returns:
            Lista de InputCursor.
        """
        return list(self._cursors.values())

    # ==========================================
    # Métodos auxiliares privados
    # ==========================================

    def _ema(
        self,
        previous: tuple[float, float] | None,
        current: tuple[float, float] | None,
    ) -> tuple[float, float] | None:
        """Exponential Moving Average para suavizado."""
        if current is None:
            return (
                None  # ← CORREGIR: propagar None para que el cursor gestione el timeout
            )

        if previous is None:
            return current  # Primer frame, sin historial

        alpha = self._smoothing_factor
        smooth_x = alpha * current[0] + (1 - alpha) * previous[0]
        smooth_y = alpha * current[1] + (1 - alpha) * previous[1]
        return (smooth_x, smooth_y)

    def _distance(self, p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Distancia euclidiana 2D."""
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
