import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np

from pose_app.adapters.camera.webcam_adapter import WebcamAdapter


def _make_fake_cap(frames_to_emit: int, frame_delay: float = 0.001):
    """Fake que emite frames sintéticos a ritmo controlado."""
    fake = MagicMock()
    fake.isOpened.return_value = True
    fake.get.side_effect = lambda prop: {
        3: 640,
        4: 480,
        5: 30.0,
        6: 0,
    }.get(prop, 0)

    _emitted = {"n": 0}
    _lock = threading.Lock()

    def _read():
        with _lock:
            if _emitted["n"] >= frames_to_emit:
                return False, None
            _emitted["n"] += 1
        time.sleep(frame_delay)
        # Frame con >30% de píxeles no-cero para pasar la validación defensiva.
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        frame[0, 0, 0] = _emitted["n"] % 255
        return True, frame

    fake.read.side_effect = _read
    fake.release = MagicMock()
    return fake


@patch("pose_app.adapters.camera.webcam_adapter.cv2.VideoCapture")
def test_start_arranca_hilo_de_captura(mock_vc):
    mock_vc.return_value = _make_fake_cap(frames_to_emit=1000)
    cam = WebcamAdapter()
    cam.start()
    assert cam._capture_thread is not None
    assert cam._capture_thread.is_alive()
    cam.stop()


@patch("pose_app.adapters.camera.webcam_adapter.cv2.VideoCapture")
def test_get_frame_devuelve_ultimo_sin_bloquear(mock_vc):
    mock_vc.return_value = _make_fake_cap(frames_to_emit=1000, frame_delay=0.01)
    cam = WebcamAdapter()
    cam.start()
    time.sleep(0.05)  # deja que el hilo llene el buffer

    t0 = time.perf_counter()
    frame = cam.get_frame()
    elapsed = time.perf_counter() - t0

    assert frame is not None
    assert frame.shape == (480, 640, 3)
    assert elapsed < 0.01, "get_frame() no debe bloquear en read()"
    cam.stop()


@patch("pose_app.adapters.camera.webcam_adapter.cv2.VideoCapture")
def test_stop_detiene_hilo(mock_vc):
    mock_vc.return_value = _make_fake_cap(frames_to_emit=10_000, frame_delay=0.005)
    cam = WebcamAdapter()
    cam.start()
    time.sleep(0.02)
    cam.stop()
    assert cam._capture_thread is None
    assert not cam.is_running()


@patch("pose_app.adapters.camera.webcam_adapter.cv2.VideoCapture")
def test_stop_es_idempotente(mock_vc):
    mock_vc.return_value = _make_fake_cap(frames_to_emit=1000)
    cam = WebcamAdapter()
    cam.start()
    cam.stop()
    cam.stop()  # no debe lanzar


@patch("pose_app.adapters.camera.webcam_adapter.cv2.VideoCapture")
def test_get_stats_expone_metricas(mock_vc):
    mock_vc.return_value = _make_fake_cap(frames_to_emit=1000, frame_delay=0.001)
    cam = WebcamAdapter()
    cam.start()
    time.sleep(0.05)
    stats = cam.get_stats()
    cam.stop()

    assert set(stats) >= {
        "fps_captura",
        "fps_declarado",
        "frames_leidos",
        "frames_entregados",
        "width",
        "height",
        "fourcc",
        "hilo_activo",
    }
    assert stats["width"] == 640
    assert stats["height"] == 480
    assert stats["frames_leidos"] > 0


@patch("pose_app.adapters.camera.webcam_adapter.cv2.VideoCapture")
def test_get_frame_sin_running_devuelve_none(mock_vc):
    cam = WebcamAdapter()
    assert cam.get_frame() is None


@patch("pose_app.adapters.camera.webcam_adapter.cv2.VideoCapture")
def test_stop_espera_al_hilo(mock_vc):
    mock_vc.return_value = _make_fake_cap(frames_to_emit=100_000, frame_delay=0.001)
    cam = WebcamAdapter()
    cam.start()
    time.sleep(0.02)
    t0 = time.perf_counter()
    cam.stop()
    # debe unirse al hilo; no debe colgarse más de 2 s
    assert time.perf_counter() - t0 < 2.5
