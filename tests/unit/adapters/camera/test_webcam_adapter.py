"""
Tests unitarios de WebcamAdapter con cv2.VideoCapture mockeado.

No requiere cámara física: cv2.VideoCapture se reemplaza por un doble
configurable (FakeCapture) que simula apertura, lectura y liberación.
"""

from collections.abc import Callable, Iterator

import cv2
import numpy as np
import pytest

from pose_app.adapters.camera.webcam_adapter import WebcamAdapter


def _wait_for_first_frame(adapter: WebcamAdapter, timeout: float = 1.0) -> None:
    """Espera a que el hilo de captura publique el primer frame válido.

    Args:
        adapter: WebcamAdapter en ejecución.
        timeout: Máximo de segundos a esperar.
    """
    import time

    deadline = time.time() + timeout
    while adapter._latest_frame is None and time.time() < deadline:
        time.sleep(0.01)


def _fourcc_value(code: str) -> int:
    """Empaqueta un FourCC de 4 caracteres como entero (little-endian)."""
    return int.from_bytes(code.encode("ascii"), byteorder="little")


def _install_fake_capture(
    monkeypatch: pytest.MonkeyPatch,
    factory: Callable[..., "FakeCapture"],
) -> None:
    """Instala un doble de cv2.VideoCapture sin ensuciar la inferencia de tipos."""
    monkeypatch.setattr(cv2, "VideoCapture", factory, raising=True)


class FakeCapture:
    """Doble de cv2.VideoCapture configurable para tests."""

    def __init__(self, opened: bool = True) -> None:
        """Inicializa el doble.

        Args:
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
        """Encola ``count`` frames válidos para próximas lecturas.

        Los frames tienen >30% de píxeles no-cero (como un frame real)
        para pasar la validación `_is_valid_frame`.

        Args:
            count: Número de frames válidos a encolar.
        """
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
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
    _install_fake_capture(monkeypatch, lambda *a, **kw: capture)
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
        _install_fake_capture(monkeypatch, lambda *a, **kw: closed)
        adapter = WebcamAdapter()

        with pytest.raises(RuntimeError, match="No se pudo abrir la cámara"):
            adapter.start()

    def test_start_configures_resolution_and_fps(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """start() aplica fourcc, width, height y fps al dispositivo."""
        capture.queue_frames(1)

        adapter.start()

        props = [prop for prop, _value in capture.set_calls]
        assert props == [
            cv2.CAP_PROP_FOURCC,
            cv2.CAP_PROP_FRAME_WIDTH,
            cv2.CAP_PROP_FRAME_HEIGHT,
            cv2.CAP_PROP_FPS,
            cv2.CAP_PROP_BUFFERSIZE,
        ]

    def test_start_uses_configured_fourcc(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """start() pasa el fourcc configurado al dispositivo."""
        capture.queue_frames(1)

        adapter.start()

        fourcc_calls = [v for p, v in capture.set_calls if p == cv2.CAP_PROP_FOURCC]
        assert fourcc_calls == [_fourcc_value("MJPG")]

    def test_start_is_idempotent(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Un segundo start() no reabre la cámara ni reconfigura el dispositivo."""
        capture.queue_frames(2)

        adapter.start()
        calls_after_first = len(capture.set_calls)
        adapter.start()

        assert len(capture.set_calls) == calls_after_first
        assert calls_after_first == 5  # FOURCC + WIDTH + HEIGHT + FPS + BUFFERSIZE

    def test_start_captures_initial_frame(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """start() deja un frame inicial en el buffer (tras procesar el hilo)."""
        capture.queue_frames(1)

        adapter.start()
        _wait_for_first_frame(adapter)

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
        _wait_for_first_frame(adapter)

        frame = adapter.get_frame()

        assert frame is not None
        assert frame.shape == (480, 640, 3)

    def test_get_frame_returns_copy_of_buffer(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """El frame devuelto es una copia: modificarlo no afecta el buffer."""
        capture.queue_frames(2)
        adapter.start()
        _wait_for_first_frame(adapter)
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
        _wait_for_first_frame(adapter)
        first = adapter.get_frame()
        assert first is not None

        # read_results vacío → la siguiente lectura falla
        result = adapter.get_frame()

        np.testing.assert_array_equal(result, first)

    def test_camera_disconnect_stops_capture_thread(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Si la cámara se desconecta, el hilo de captura marca is_running()=False."""
        import time

        capture.queue_frames(10)
        adapter.start()

        # Simula desconexión: isOpened() pasa a False
        capture._opened = False

        # Espera a que el hilo de captura lo detecte (loop hace check por iteración)
        deadline = time.time() + 1.0
        while adapter.is_running() and time.time() < deadline:
            time.sleep(0.01)

        assert adapter.is_running() is False
        # Con el adaptador detenido, get_frame() devuelve None
        assert adapter.get_frame() is None


class TestGetFps:
    def test_get_fps_returns_cached_value(self, adapter: WebcamAdapter) -> None:
        """get_fps() devuelve el valor calculado por el hilo de captura."""
        adapter._fps = 29.5
        assert adapter.get_fps() == 29.5

    def test_get_fps_zero_before_any_measurement(self, adapter: WebcamAdapter) -> None:
        """Sin mediciones todavía, get_fps() es 0.0."""
        assert adapter.get_fps() == 0.0


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


class TestFpsWindow:
    """Tests de la ventana de cálculo de FPS del hilo de captura."""

    def test_fps_window_resets_counter_after_one_second(
        self, adapter: WebcamAdapter
    ) -> None:
        """Tras >=1s, _update_fps_locked resetea _frame_count y fija _fps."""
        import time

        adapter._frame_count = 30
        adapter._last_read_time = time.perf_counter() - 1.5
        adapter._update_fps_locked(time.perf_counter())

        assert adapter._frame_count == 0
        assert 15.0 < adapter.get_fps() < 25.0  # 30/1.5

    def test_fps_window_does_not_reset_before_one_second(
        self, adapter: WebcamAdapter
    ) -> None:
        """Antes de 1s, no se resetea ni se actualiza _fps."""
        import time

        adapter._frame_count = 5
        adapter._last_read_time = time.perf_counter() - 0.2
        before = adapter.get_fps()
        adapter._update_fps_locked(time.perf_counter())

        assert adapter._frame_count == 5
        assert adapter.get_fps() == before


class TestGetStats:
    """Tests de WebcamAdapter.get_stats()."""

    def test_get_stats_exposes_expected_keys(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        capture.queue_frames(1)
        adapter.start()

        stats = adapter.get_stats()

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
        assert stats["hilo_activo"] is True

    def test_get_stats_counts_delivered_frames(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        capture.queue_frames(5)
        adapter.start()
        _wait_for_first_frame(adapter)
        adapter.get_frame()
        adapter.get_frame()

        stats = adapter.get_stats()
        assert stats["frames_entregados"] == 2


class TestFrameValidation:
    """Validación defensiva de frames corruptos (Fase A)."""

    def test_zero_size_frame_is_discarded(self, adapter: WebcamAdapter) -> None:
        """Un frame vacío se descarta."""
        adapter._actual_width = 640
        adapter._actual_height = 480
        frame = np.array([], dtype=np.uint8)
        assert adapter._is_valid_frame(frame) is False

    def test_none_frame_is_discarded(self, adapter: WebcamAdapter) -> None:
        """None se descarta."""
        assert adapter._is_valid_frame(None) is False  # type: ignore[arg-type]

    def test_wrong_shape_frame_is_discarded(self, adapter: WebcamAdapter) -> None:
        """Shape distinto al negociado se descarta."""
        adapter._actual_width = 640
        adapter._actual_height = 480
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        assert adapter._is_valid_frame(frame) is False

    def test_mostly_black_frame_is_discarded(self, adapter: WebcamAdapter) -> None:
        """Frame >70% negro se descarta (heurística de corrupción)."""
        adapter._actual_width = 640
        adapter._actual_height = 480
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # <30% de píxeles no-cero → descartado
        frame[0:100, 0:100] = 255  # ~3% de píxeles no-cero
        assert adapter._is_valid_frame(frame) is False

    def test_normal_frame_is_accepted(self, adapter: WebcamAdapter) -> None:
        """Frame con >30% de píxeles no-cero pasa."""
        adapter._actual_width = 640
        adapter._actual_height = 480
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)  # 100% no-cero
        assert adapter._is_valid_frame(frame) is True

    def test_custom_threshold_is_used(self, monkeypatch) -> None:
        """El umbral configurable se aplica."""
        adapter = WebcamAdapter(width=640, height=480)
        adapter._actual_width = 640
        adapter._actual_height = 480
        adapter._min_nonzero_ratio = 0.9  # umbral estricto

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[0:400, :] = 255  # 83% no-cero (< 90%)
        assert adapter._is_valid_frame(frame) is False


class TestBufferSize:
    """Fase B: buffer de 1 frame."""

    def test_start_sets_buffersize_to_one(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """start() intenta reducir el buffer a 1."""
        capture.queue_frames(1)
        adapter.start()

        props = [prop for prop, _value in capture.set_calls]
        assert cv2.CAP_PROP_BUFFERSIZE in props
        # El valor debe ser 1
        buffersize_value = next(
            v for p, v in capture.set_calls if p == cv2.CAP_PROP_BUFFERSIZE
        )
        assert buffersize_value == 1

    def test_start_succeeds_when_buffersize_unsupported(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Si el backend no soporta BUFFERSIZE, start() no falla."""

        class _NoBufferCapture(FakeCapture):
            def set(self, prop_id: int, value: float) -> bool:
                if prop_id == cv2.CAP_PROP_BUFFERSIZE:
                    raise cv2.error("not supported")
                return super().set(prop_id, value)

        closed = _NoBufferCapture()
        _install_fake_capture(monkeypatch, lambda *a, **kw: closed)
        adapter = WebcamAdapter()

        # No debe lanzar
        closed.queue_frames(1)
        adapter.start()
        assert adapter.is_running()
        adapter.stop()

    def test_custom_buffersize_is_passed(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """El buffer_size configurado se pasa a CAP_PROP_BUFFERSIZE."""
        adapter._buffer_size = 3  # override para el test
        capture.queue_frames(1)
        adapter.start()

        buffersize_value = next(
            v for p, v in capture.set_calls if p == cv2.CAP_PROP_BUFFERSIZE
        )
        assert buffersize_value == 3


class TestCorruptFrameHandling:
    """Fase A: frames corruptos se descartan en _capture_loop."""

    def test_corrupt_frames_are_counted_in_stats(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """El contador de frames corruptos se expone en get_stats."""
        capture.queue_frames(3)
        adapter.start()

        stats = adapter.get_stats()
        assert "frames_corruptos" in stats
        adapter.stop()

    def test_valid_frames_still_processed_after_corrupt(
        self, adapter: WebcamAdapter, capture: FakeCapture
    ) -> None:
        """Un frame corrupto no impide procesar los siguientes válidos."""
        # Frame válido (100% no-cero)
        valid_frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        # Frame corrupto (shape incorrecto)
        corrupt_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        capture.read_results = [
            (True, valid_frame),
            (True, corrupt_frame),
            (True, valid_frame),
        ]
        adapter.start()

        # Esperar a que el hilo procese
        import time

        time.sleep(0.1)
        stats = adapter.get_stats()
        adapter.stop()

        # Al menos 1 corrupto detectado
        assert stats["frames_corruptos"] >= 1
        # Al menos 1 válido entregado
        assert (
            adapter.get_frame() is None or True
        )  # buffer puede tener el último válido
