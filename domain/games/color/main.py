"""
Juego de color (async).
"""

import asyncio
from collections.abc import Callable
from typing import ClassVar

from domain.entities.color import RGBColor
from domain.entities.pose_landmark import PoseLandmark
from domain.events.game_events import PaletteChangeRequested
from domain.games.color.state import ColorState
from domain.ports.camera_port import CameraPort
from domain.ports.event_bus_port import EventBusPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import ColorRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("use_cases.color")


class ColorGame:
    """Juego que cambia el color de fondo según la pose (async)."""

    PALETTES: ClassVar[dict[str, list[RGBColor]]] = {
        "fire": [RGBColor(255, 0, 0), RGBColor(255, 165, 0), RGBColor(255, 255, 0)],
        "ocean": [RGBColor(0, 0, 255), RGBColor(0, 128, 255), RGBColor(0, 255, 255)],
        "forest": [RGBColor(0, 100, 0), RGBColor(34, 139, 34), RGBColor(0, 255, 127)],
        "neon": [RGBColor(255, 0, 255), RGBColor(0, 255, 255), RGBColor(255, 255, 0)],
    }

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        renderer: ColorRenderPort,
        state: ColorState,
        event_bus: EventBusPort,
        palette_name: str = "fire",
    ):
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._renderer = renderer
        self._state = state
        self._event_bus = event_bus
        self._palette_name = palette_name if palette_name in self.PALETTES else "fire"
        self._palette = self.PALETTES[self._palette_name]

        self._frame_count = 0
        self._pending_palette: str | None = None

        event_bus.subscribe(PaletteChangeRequested, self._on_palette_change)

    # ==========================================
    # Estado
    # ==========================================

    @property
    def state(self) -> ColorState:
        """Estado consultable del juego (para el StateRegistry)."""
        return self._state

    async def _on_palette_change(self, event: PaletteChangeRequested) -> None:
        """Marca cambio de paleta pendiente."""
        if event.palette_name in self.PALETTES:
            self._pending_palette = event.palette_name
        else:
            logger.warning(f"Paleta desconocida: {event.palette_name}")

    async def run_async(
        self,
        should_stop: Callable[[], bool] | None = None,
    ) -> None:
        should_stop = should_stop or (lambda: False)

        await asyncio.to_thread(self._camera.start)
        logger.info("Juego de color iniciado (async)")

        try:
            while not should_stop():
                # Aplica cambio de paleta pendiente
                if self._pending_palette is not None:
                    self._palette_name = self._pending_palette
                    self._palette = self.PALETTES[self._palette_name]
                    self._state.update_palette(self._palette_name)
                    logger.info(f"Paleta aplicada: {self._palette_name}")
                    self._pending_palette = None

                frame = await asyncio.to_thread(self._camera.get_frame)
                if frame is None:
                    await asyncio.sleep(0.001)
                    continue

                try:
                    landmarks = await asyncio.to_thread(
                        self._pose_estimator.estimate, frame
                    )
                except Exception as e:
                    logger.warning(f"Error estimando pose: {e}")
                    continue

                self._state.update_pose(landmarks)
                self._state.increment_frames()

                color = self._calculate_color(landmarks)
                self._state.update_color(color)

                try:
                    await asyncio.to_thread(
                        self._renderer.render_background, color, landmarks
                    )
                except Exception as e:
                    logger.error(f"Error renderizando: {e}")
                    break

                self._frame_count += 1
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info("Juego de color cancelado")
            raise
        finally:
            try:
                self._renderer.close()
            except Exception as e:
                logger.error(f"Error cerrando renderer: {e}")
            try:
                await asyncio.to_thread(self._camera.stop)
            except Exception as e:
                logger.error(f"Error cerrando cámara: {e}")
            logger.info(f"Juego color terminado. Frames: {self._frame_count}")

    def _calculate_color(self, landmarks: list[PoseLandmark]) -> RGBColor:
        if not landmarks:
            return self._palette[0]

        left_wrist = self._find(landmarks, "left_wrist")
        right_wrist = self._find(landmarks, "right_wrist")
        nose = self._find(landmarks, "nose")

        r = g = b = 0.0
        if left_wrist and left_wrist.is_visible():
            r = max(0, 1 - left_wrist.y * 2.5)
        if right_wrist and right_wrist.is_visible():
            b = max(0, 1 - right_wrist.y * 2.5)
        if nose and nose.is_visible():
            g = max(0, 1 - abs(nose.x - 0.5) * 3)

        total = r + g + b
        if total == 0:
            return self._palette[0]
        r, g, b = r / total, g / total, b / total

        if r >= g and r >= b:
            return RGBColor.interpolate(self._palette[0], self._palette[1], r)
        elif g >= b:
            return RGBColor.interpolate(self._palette[1], self._palette[2], g)
        else:
            return RGBColor.interpolate(self._palette[2], self._palette[0], b)

    def _find(self, landmarks: list[PoseLandmark], name: str) -> PoseLandmark | None:
        for lm in landmarks:
            if lm.name and lm.name.lower() == name.lower():
                return lm
        return None
