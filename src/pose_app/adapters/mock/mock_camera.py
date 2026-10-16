import numpy as np

from pose_app.domain.ports.camera_port import CameraPort


class MockCameraAdapter(CameraPort):
    """Adaptador mock que genera frames sintéticos (círculos en movimiento)."""

    def __init__(self, width: int = 640, height: int = 480):
        self._width = width
        self._height = height
        self._running = False
        self._frame_count = 0

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def get_frame(self) -> np.ndarray | None:
        if not self._running:
            return None

        # Crea frame negro
        frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)

        # Dibuja un círculo que se mueve
        center_x = int(self._width * (0.5 + 0.4 * np.sin(self._frame_count * 0.01)))
        center_y = int(self._height * (0.5 + 0.4 * np.cos(self._frame_count * 0.015)))

        # Círculo blanco simulando "persona"
        cv2.circle(frame, (center_x, center_y), 50, (255, 255, 255), -1)

        # Puntos clave simulados (para testing)
        # (En un mock más avanzado, generarías landmarks también)

        self._frame_count += 1
        return frame

    def is_running(self) -> bool:
        return self._running


# Nota: necesitas importar cv2 para el mock, pero es una dependencia de prueba
# En producción, este mock solo se usa en tests.
try:
    import cv2
except ImportError:
    # Si no hay cv2, el mock no funcionará, pero es solo para tests
    pass
