import time
from threading import Lock

import cv2
import numpy as np

from domain.ports.camera_port import CameraPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.webcam")


class WebcamAdapter(CameraPort):
    """
    Adaptador de cámara web usando OpenCV.

    Características:
    - Buffer de un solo frame (si no se lee a tiempo, se sobrescribe)
    - Hilo separado para captura (no bloquea el procesamiento)
    - Manejo seguro de recursos con context manager
    """

    def __init__(
        self, camera_id: int = 0, width: int = 640, height: int = 480, fps: int = 30
    ):
        """
        Args:
            camera_id: ID de la cámara (0 para cámara por defecto)
            width: Ancho de captura
            height: Alto de captura
            fps: Frames por segundo (sugerido)
        """
        self._camera_id = camera_id
        self._width = width
        self._height = height
        self._fps = fps

        self._cap: cv2.VideoCapture | None = None
        self._running: bool = False
        self._latest_frame: np.ndarray | None = None
        self._lock = Lock()  # Para acceso seguro al frame

        self._frame_count: int = 0
        self._last_read_time: float = 0.0

    def start(self) -> None:
        """Inicia la captura de video."""
        if self._running:
            return

        # Abre la cámara
        # self._cap = cv2.VideoCapture(self._camera_id, cv2.CAP_V4L2) # <-- LINUX/WSL
        self._cap = cv2.VideoCapture(self._camera_id)

        if not self._cap.isOpened():
            logger.error(f"No se pudo abrir la cámara {self._camera_id}")
            raise RuntimeError(f"No se pudo abrir la cámara {self._camera_id}")

        # Configura resolución
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap.set(cv2.CAP_PROP_FPS, self._fps)

        # Lee la configuración real (puede diferir de la solicitada)
        actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)

        logger.info(
            f"Cámara iniciada: {actual_width}x{actual_height} " f"@ {self._fps} FPS"
        )
        print(
            f"📷 Cámara iniciada: {actual_width}x{actual_height} @ {actual_fps:.1f} FPS"
        )

        self._running = True
        self._frame_count = 0

        # Captura el primer frame para inicializar el buffer
        self._read_frame()

    def stop(self) -> None:
        """Detiene la captura y libera la cámara."""
        if not self._running:
            return

        self._running = False

        if self._cap and self._cap.isOpened():
            self._cap.release()
            print("📷 Cámara liberada")

        self._cap = None
        self._latest_frame = None

    def get_frame(self) -> np.ndarray | None:
        """
        Obtiene el último frame capturado.

        Returns:
            Frame en formato BGR (OpenCV) o None si no hay frame disponible.
        """
        if not self._running:
            return None

        # Lee un nuevo frame (actualiza el buffer)
        self._read_frame()

        # Retorna una copia para evitar modificaciones externas
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def is_running(self) -> bool:
        """Indica si la cámara está activa."""
        return self._running

    def get_fps(self) -> float:
        """Calcula el FPS real basado en el tiempo entre lecturas."""
        if self._frame_count < 2:
            return 0.0

        elapsed = time.time() - self._last_read_time
        if elapsed > 0:
            return self._frame_count / elapsed
        return 0.0

    def _read_frame(self) -> None:
        """
        Lee un frame de la cámara y actualiza el buffer.
        Si la lectura falla, mantiene el último frame válido.
        """
        if not self._running or self._cap is None:
            return

        if not self._cap.isOpened():
            print("⚠️ Cámara desconectada")
            self._running = False
            return

        # Lee el frame
        ret, frame = self._cap.read()

        if not ret or frame is None:
            print("⚠️ Error al leer frame de la cámara")
            return

        # Actualiza el buffer (thread-safe)
        with self._lock:
            self._latest_frame = frame

        self._frame_count += 1

        # Log de FPS cada 30 frames
        if self._frame_count % 30 == 0:
            current_time = time.time()
            if self._last_read_time > 0:
                elapsed = current_time - self._last_read_time
                fps = 30 / elapsed if elapsed > 0 else 0
                print(f"📹 FPS real: {fps:.1f}")
            self._last_read_time = current_time
            self._frame_count = 0

    def __enter__(self):
        """Context manager: inicia automáticamente."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: asegura liberación de recursos."""
        self.stop()

    def __del__(self):
        """Destructor: libera recursos si no se llamó a stop()."""
        if self._running:
            self.stop()
