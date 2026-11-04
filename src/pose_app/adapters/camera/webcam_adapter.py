import threading
import time
from threading import Lock

import cv2
import numpy as np

from pose_app.domain.ports.camera_port import CameraPort
from pose_app.infrastructure.logging.logger import get_logger

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
        self,
        camera_id: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        fourcc: str = "MJPG",
    ):
        """
        Args:
            camera_id: ID de la cámara (0 para cámara por defecto)
            width: Ancho de captura
            height: Alto de captura
            fps: Frames por segundo (sugerido)
            fourcc: Código de compresión de video
        """
        self._camera_id = camera_id
        self._width = width
        self._height = height
        self._fps_target = fps
        self._fourcc = fourcc

        self._cap: cv2.VideoCapture | None = None
        self._running: bool = False
        self._latest_frame: np.ndarray | None = None
        self._lock = Lock()  # Para acceso seguro al frame

        # --- nuevo: hilo de captura ---
        self._capture_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # --- métricas ---
        self._frame_count: int = 0  # frames leídos por el hilo de captura
        self._frames_total: int = 0  # frames leídos en total (sesión)
        self._frames_delivered: int = 0  # frames que get_frame() devolvió
        self._fps: float = 0.0
        self._fps_declarado: float = 0.0
        self._actual_width: int = width
        self._actual_height: int = height
        self._actual_fourcc: str = fourcc
        self._last_read_time: float = 0.0

    def start(self) -> None:
        """Inicia la captura de video."""
        if self._running:
            return

        self._cap = cv2.VideoCapture(self._camera_id, cv2.CAP_V4L2)
        if not self._cap.isOpened():
            logger.error(f"No se pudo abrir la cámara {self._camera_id}")
            raise RuntimeError(f"No se pudo abrir la cámara {self._camera_id}")

        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*self._fourcc))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap.set(cv2.CAP_PROP_FPS, self._fps_target)

        self._actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps_declarado = self._cap.get(cv2.CAP_PROP_FPS)
        self._actual_fourcc = self._get_actual_fourcc()

        logger.info(
            f"Cámara iniciada: {self._actual_width}x{self._actual_height} "
            f"@ {self._fps_declarado:.1f} FPS / Formato: {self._actual_fourcc}"
        )
        print(
            f"📷 Cámara iniciada: {self._actual_width}x{self._actual_height} "
            f"@ {self._fps_declarado:.1f} FPS / Formato: {self._actual_fourcc}"
        )

        self._running = True
        self._stop_event.clear()
        self._frame_count = 0
        self._frames_total = 0
        self._frames_delivered = 0
        self._last_read_time = time.perf_counter()

        # Arranca el hilo de captura
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            name=f"WebcamAdapter-{self._camera_id}",
            daemon=True,
        )
        self._capture_thread.start()

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2.0)
            if self._capture_thread.is_alive():
                logger.warning("El hilo de captura no terminó en 2s")
            self._capture_thread = None

        if self._cap and self._cap.isOpened():
            self._cap.release()
            print("📷 Cámara liberada")

        self._cap = None
        self._latest_frame = None

        with self._lock:
            self._fps = 0.0
            self._frame_count = 0
            self._frames_total = 0
            self._frames_delivered = 0

    def get_frame(self) -> np.ndarray | None:
        if not self._running:
            return None

        with self._lock:
            if self._latest_frame is None:
                return None
            self._frames_delivered += 1
            return self._latest_frame.copy()

    def is_running(self) -> bool:
        """Indica si la cámara está activa."""
        return self._running

    def get_fps(self) -> float:
        with self._lock:
            return self._fps

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "fps_captura": self._fps,
                "fps_declarado": self._fps_declarado,
                "frames_leidos": self._frames_total,
                "frames_en_ventana": self._frame_count,
                "frames_entregados": self._frames_delivered,
                "width": self._actual_width,
                "height": self._actual_height,
                "fourcc": self._actual_fourcc,
                "hilo_activo": (
                    self._capture_thread.is_alive()
                    if self._capture_thread is not None
                    else False
                ),
            }

    #####################
    # Private methods
    #####################

    def _capture_loop(self) -> None:
        logger.info("Hilo de captura iniciado")
        while not self._stop_event.is_set():
            if self._cap is None or not self._cap.isOpened():
                logger.warning("Cámara desconectada; deteniendo hilo de captura")
                self._running = False
                break

            ret, frame = self._cap.read()
            if not ret or frame is None:
                if not self._cap.isOpened():
                    logger.warning("Cámara desconectada durante read()")
                    self._running = False
                    break
                time.sleep(0.001)
                continue

            now = time.perf_counter()
            with self._lock:
                self._latest_frame = frame
                self._frame_count += 1
                self._frames_total += 1
                self._update_fps_locked(now)

        logger.info("Hilo de captura detenido")

    def _update_fps_locked(self, now: float) -> None:
        """
        Actualiza la métrica de FPS con ventana de 1 segundo.

        Debe invocarse con `self._lock` tomado por el llamador.
        Si ha transcurrido >= 1s desde el inicio de la ventana actual,
        calcula `_fps = frames_en_ventana / elapsed`, resetea el contador
        y reinicia la ventana.

        Args:
            now: Marca de tiempo actual (``time.perf_counter()``).
        """
        elapsed = now - self._last_read_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_read_time = now

    def _get_actual_fourcc(self) -> str:
        """Devuelve el FourCC de 4 letras realmente negociado con el dispositivo."""
        if self._cap is None:
            return ""
        fourcc_int = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        return (
            fourcc_int.to_bytes(4, byteorder="little").decode(errors="replace").strip()
        )

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
