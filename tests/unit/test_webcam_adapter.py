"""
Tests unitarios de WebcamAdapter con cv2.VideoCapture mockeado.

No requiere cámara física: cv2.VideoCapture se reemplaza por un doble
configurable (FakeCapture) que simula apertura, lectura y liberación.
"""

from collections.abc import Iterator

import cv2
import numpy as np
import pytest

from pose_app.adapters.camera.webcam_adapter import WebcamAdapter


class FakeCapture:
    """Doble de cv2.VideoCapture configurable para tests."""

    def __init__(self, opened: bool = True) -> None:
        """Args:
        opened: Valor inicial de isOpened().
        """
        self._opened = opened
        self.read_results: list[tuple[bool, np.ndarray | None]] = []
        self.set_calls: list[tuple[int, float]] = []
        self.release_calls = 0

    def isOpened(self) -> bool:
        return self._opened

    def set(self, prop_id: int, value: float) -> bool:
        self.set_calls.append((prop_id, value))
        return True

    def get(self, prop_id: int) -> float:
        values = {
            cv2.CAP_PROP_FRAME_WIDTH: 640.0,
            cv2.CAP_PROP_FRAME_HEIGHT: 480.0,
            cv2.CAP_PROP_FPS: 30.0,
        }
        return values.get(prop_id, 0.0)

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self.read_results:
            return self.read_results.pop(0)
        return False, None

    def release(self) -> None:
        self.release_calls += 1
        self._opened = False

    def queue_frames(self, count: int) -> None:
        """Args:
        count: Número de frames válidos a encolar.
        """
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(count):
            self.read_results.append((True, frame.copy()))


@pytest.fixture
def capture() -> FakeCapture:
    return FakeCapture()


@pytest.fixture
def adapter(
    capture: FakeCapture, monkeypatch: pytest.MonkeyPatch
) -> Iterator[WebcamAdapter]:
    """WebcamAdapter con cv2.VideoCapture reemplazado por FakeCapture."""

    def factory(_camera_id: int) -> FakeCapture:
        return capture

    monkeypatch.setattr(cv2, "VideoCapture", factory)
    adapter = WebcamAdapter(camera_id=0, width=640, height=480, fps=30)
    yield adapter
    if adapter.is_running():
        adapter.stop()


class TestStart:
    """Tests de WebcamAdapter.start()."""

    def test_start_raises_when_camera_cannot_be_opened(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Si isOpened() es False, start() lanza RuntimeError."""
        closed = FakeCapture(opened=False)
        monkeypatch.setattr(cv2, "VideoCapture", lambda _id: closed)
        adapter = WebcamAdapter()

        with pytest.raises(RuntimeError, match="No se pudo abrir la cámara"):
            adapter.start()

    def test_start_configures_resolution_and_fps(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """start() aplica width, height y fps al dispositivo."""
        capture.queue_frames(1)

        adapter.start()

        props = [prop for prop, _value in capture.set_calls]
        assert props == [
            cv2.CAP_PROP_FRAME_WIDTH,
            cv2.CAP_PROP_FRAME_HEIGHT,
            cv2.CAP_PROP_FPS,
        ]

    def test_start_is_idempotent(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Un segundo start() no reabre la cámara."""
        capture.queue_frames(2)

        adapter.start()
        adapter.start()

        assert len(capture.set_calls) == 3

    def test_start_captures_initial_frame(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """start() deja un frame inicial en el buffer."""
        capture.queue_frames(1)

        adapter.start()

        assert adapter._latest_frame is not None

    def test_start_leaves_adapter_running(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Tras start(), is_running() es True."""
        capture.queue_frames(1)

        adapter.start()

        assert adapter.is_running() is True


class TestStop:
    """Tests de WebcamAdapter.stop()."""

    def test_stop_before_start_is_noop(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """stop() sin start() no lanza ni libera nada."""
        adapter.stop()

        assert capture.release_calls == 0

    def test_stop_releases_capture(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """stop() libera el dispositivo y desactiva el estado."""
        capture.queue_frames(1)
        adapter.start()

        adapter.stop()

        assert capture.release_calls == 1
        assert adapter.is_running() is False
        assert adapter._cap is None
        assert adapter._latest_frame is None

    def test_stop_is_idempotent(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Un segundo stop() no vuelve a liberar el dispositivo."""
        capture.queue_frames(1)
        adapter.start()

        adapter.stop()
        adapter.stop()

        assert capture.release_calls == 1


class TestGetFrame:
    """Tests de WebcamAdapter.get_frame()."""

    def test_get_frame_returns_none_when_not_running(
        self, adapter: WebcamAdapter
    ) -> None:
        """Sin start(), get_frame() devuelve None."""
        assert adapter.get_frame() is None

    def test_get_frame_returns_frame_when_running(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Con cámara activa, get_frame() devuelve el buffer."""
        capture.queue_frames(2)
        adapter.start()

        frame = adapter.get_frame()

        assert frame is not None
        assert frame.shape == (480, 640, 3)

    def test_get_frame_returns_copy_of_buffer(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """El frame devuelto es una copia: modificarlo no afecta el buffer."""
        capture.queue_frames(2)
        adapter.start()
        original = adapter._latest_frame.copy()

        result = adapter.get_frame()
        assert result is not None
        result[:] = 255

        np.testing.assert_array_equal(adapter._latest_frame, original)

    def test_get_frame_returns_none_when_no_frame_ever_read(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Si la lectura siempre falla, get_frame() devuelve None."""
        adapter.start()

        assert adapter.get_frame() is None

    def test_get_frame_keeps_last_valid_frame_on_read_failure(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Un fallo de lectura posterior conserva el último frame válido."""
        capture.queue_frames(2)
        adapter.start()
        first = adapter.get_frame()
        assert first is not None

        # read_results vacío → la siguiente lectura falla
        result = adapter.get_frame()

        np.testing.assert_array_equal(result, first)

    def test_camera_disconnect_stops_running(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Si la cámara se desconecta, is_running() pasa a False."""
        capture.queue_frames(2)
        adapter.start()
        capture._opened = False

        adapter.get_frame()

        assert adapter.is_running() is False
        assert adapter.get_frame() is None


class TestGetFps:
    """Tests de WebcamAdapter.get_fps()."""

    def test_get_fps_zero_with_insufficient_frames(
        self, adapter: WebcamAdapter
    ) -> None:
        """Con menos de 2 frames, get_fps() devuelve 0.0."""
        assert adapter.get_fps() == 0.0

    def test_get_fps_computes_frames_over_elapsed(self, adapter: WebcamAdapter) -> None:
        """get_fps() = frame_count / tiempo transcurrido."""
        import time

        adapter._frame_count = 10
        adapter._last_read_time = time.time() - 2.0

        fps = adapter.get_fps()

        assert 4.0 < fps < 6.0

    def test_get_fps_zero_when_no_time_elapsed(self, adapter: WebcamAdapter) -> None:
        """Si no transcurrió tiempo (reloj en el futuro), get_fps() es 0.0."""
        import time

        adapter._frame_count = 10
        adapter._last_read_time = time.time() + 100.0

        assert adapter.get_fps() == 0.0


class TestReadFrameInternals:
    """Tests de WebcamAdapter._read_frame() y logging de FPS."""

    def test_read_frame_noop_when_not_running(self, adapter: WebcamAdapter) -> None:
        """_read_frame() sin start() no hace nada ni lanza."""
        adapter._read_frame()

        assert adapter._latest_frame is None

    def test_fps_logging_every_30_frames(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Cada 30 frames se reinicia el contador y se registra el FPS."""
        capture.queue_frames(70)
        adapter.start()

        # start() ya leyó 1 frame; 29 más completan el primer ciclo de 30
        for _ in range(29):
            adapter.get_frame()
        first_cycle_time = adapter._last_read_time
        assert adapter._frame_count == 0
        assert first_cycle_time > 0

        # 30 frames más: ahora _last_read_time > 0, se calcula FPS real
        for _ in range(30):
            adapter.get_frame()

        assert adapter._frame_count == 0
        assert adapter._last_read_time >= first_cycle_time


class TestLifecycle:
    """Tests de context manager y destructor."""

    def test_context_manager_starts_and_stops(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """with WebcamAdapter() inicia al entrar y libera al salir."""
        capture.queue_frames(1)

        with adapter as cam:
            assert cam is adapter
            assert adapter.is_running() is True

        assert adapter.is_running() is False
        assert capture.release_calls == 1

    def test_del_stops_running_adapter(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """__del__() libera recursos si seguía corriendo."""
        capture.queue_frames(1)
        adapter.start()

        adapter.__del__()

        assert adapter.is_running() is False
        assert capture.release_calls == 1

    def test_del_noop_when_not_running(self, adapter: WebcamAdapter) -> None:
        """__del__() sin start() no hace nada."""
        adapter.__del__()

        assert adapter.is_running() is False
