"""
Tests unitarios de MediapipeAdapter con la Tasks API mockeada.

No inicializa Mediapipe real: PoseLandmarker.create_from_options se
reemplaza por un doble (FakeLandmarker) y la descarga del modelo se
simula redirigiendo Path a un tmp_path.
"""

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from mediapipe.tasks.python import vision

import pose_app.adapters.pose.mediapipe_adapter as mediapipe_module
from pose_app.adapters.pose.mediapipe_adapter import MediapipeAdapter
from pose_app.domain.entities.pose_landmark import PoseLandmark


class FakeLandmarker:
    """Doble de vision.PoseLandmarker de la Tasks API."""

    def __init__(self) -> None:
        self.results: SimpleNamespace | None = None
        self.detect_calls: list[object] = []
        self.closed = False

    def detect(self, image: object) -> SimpleNamespace:
        """Args:
            image: Imagen mp.Image recibida (no se valida en el doble).

        Returns:
            Results simulados (pose_landmarks o vacío).
        """
        self.detect_calls.append(image)
        if self.results is not None:
            return self.results
        return SimpleNamespace(pose_landmarks=[])

    def close(self) -> None:
        self.closed = True


def _landmark(
    x: float = 0.5, y: float = 0.5, visibility: float = 0.9
) -> SimpleNamespace:
    """Crea un landmark simulado con la forma que devuelve la Tasks API."""
    return SimpleNamespace(x=x, y=y, z=0.0, visibility=visibility)


@pytest.fixture
def fake_landmarker() -> FakeLandmarker:
    return FakeLandmarker()


@pytest.fixture
def adapter(
    fake_landmarker: FakeLandmarker, monkeypatch: pytest.MonkeyPatch
) -> Iterator[MediapipeAdapter]:
    """MediapipeAdapter con PoseLandmarker.create_from_options parcheado."""
    monkeypatch.setattr(
        vision.PoseLandmarker,
        "create_from_options",
        staticmethod(lambda _options: fake_landmarker),
    )
    instance = MediapipeAdapter()
    yield instance
    instance.close()


class TestInit:
    """Tests de MediapipeAdapter.__init__()."""

    def test_init_uses_default_thresholds(self, adapter: MediapipeAdapter) -> None:
        """Los defaults del puerto se aplican al adaptador."""
        assert adapter._min_detection_confidence == 0.5
        assert adapter._min_tracking_confidence == 0.5
        assert adapter._model_complexity == 1

    def test_init_injects_fake_landmarker(self, adapter: MediapipeAdapter) -> None:
        """create_from_options() se usa para construir el landmarker."""
        assert isinstance(adapter._landmarker, FakeLandmarker)

    def test_init_passes_confidence_thresholds(
        self, fake_landmarker: FakeLandmarker, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Los umbrales custom llegan a PoseLandmarkerOptions."""
        captured: list[object] = []

        def factory(options: object) -> FakeLandmarker:
            captured.append(options)
            return fake_landmarker

        monkeypatch.setattr(
            vision.PoseLandmarker,
            "create_from_options",
            staticmethod(factory),
        )

        MediapipeAdapter(
            min_detection_confidence=0.8,
            min_tracking_confidence=0.7,
            model_complexity=2,
        ).close()

        options = captured[0]
        assert options.min_pose_detection_confidence == 0.8
        assert options.min_tracking_confidence == 0.7


class TestEnsureModel:
    """Tests de MediapipeAdapter._ensure_model()."""

    @pytest.fixture
    def bare(self) -> MediapipeAdapter:
        """Instancia sin __init__ (para aislar _ensure_model)."""
        return MediapipeAdapter.__new__(MediapipeAdapter)

    def test_ensure_model_returns_existing_path(
        self, bare: MediapipeAdapter, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Si el modelo ya existe, no intenta descargarlo."""
        # 1. Redirigimos PROJECT_ROOT al directorio temporal del test
        monkeypatch.setattr(mediapipe_module, "PROJECT_ROOT", tmp_path)

        # 2. Pre-creamos la estructura y el archivo falso para simular que ya existe
        model_dir = tmp_path / "src/pose_app/adapters/pose/models"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "pose_landmarker_full.task").write_bytes(b"fake-model")

        def fail_download(_url: str, _filename: str) -> None:
            raise AssertionError("no debería descargar")

        monkeypatch.setattr(
            mediapipe_module.urllib.request, "urlretrieve", fail_download
        )
        path = bare._ensure_model()
        assert path.endswith("pose_landmarker_full.task")
        assert Path(path).exists()

    def test_ensure_model_downloads_when_missing(
        self, bare: MediapipeAdapter, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Si el modelo falta, lo descarga desde MODEL_URL."""
        # Redirigimos PROJECT_ROOT al directorio temporal del test
        monkeypatch.setattr(mediapipe_module, "PROJECT_ROOT", tmp_path)

        downloads: list[tuple[str, str]] = []

        def fake_urlretrieve(url: str, filename: str) -> None:
            downloads.append((url, filename))
            Path(filename).write_bytes(b"fake-model")

        monkeypatch.setattr(
            mediapipe_module.urllib.request, "urlretrieve", fake_urlretrieve
        )
        path = bare._ensure_model()
        assert Path(path).exists()
        assert downloads[0][0] == MediapipeAdapter.MODEL_URL

    def test_ensure_model_raises_on_download_error(
        self, bare: MediapipeAdapter, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Un fallo de red produce RuntimeError con contexto de descarga."""
        # Redirigimos PROJECT_ROOT al directorio temporal del test
        monkeypatch.setattr(mediapipe_module, "PROJECT_ROOT", tmp_path)

        def fail_download(_url: str, _filename: str) -> None:
            raise OSError("network down")

        monkeypatch.setattr(
            mediapipe_module.urllib.request, "urlretrieve", fail_download
        )
        with pytest.raises(RuntimeError, match="No se pudo descargar"):
            bare._ensure_model()


class TestEstimate:
    """Tests de MediapipeAdapter.estimate()."""

    def test_estimate_returns_empty_for_none(self, adapter: MediapipeAdapter) -> None:
        """Frame None → []."""
        assert adapter.estimate(None) == []  # type: ignore[arg-type]

    def test_estimate_returns_empty_for_empty_array(
        self, adapter: MediapipeAdapter
    ) -> None:
        """Array sin píxeles → []."""
        frame = np.zeros((0, 0, 3), dtype=np.uint8)
        assert adapter.estimate(frame) == []

    def test_estimate_rejects_grayscale_frame(self, adapter: MediapipeAdapter) -> None:
        """Frame 2D (sin canal BGR) → []."""
        frame = np.zeros((480, 640), dtype=np.uint8)
        assert adapter.estimate(frame) == []

    def test_estimate_rejects_four_channel_frame(
        self, adapter: MediapipeAdapter
    ) -> None:
        """Frame con 4 canales → []."""
        frame = np.zeros((480, 640, 4), dtype=np.uint8)
        assert adapter.estimate(frame) == []

    def test_estimate_rejects_too_small_frame(self, adapter: MediapipeAdapter) -> None:
        """Frames menores a 64x64 → []."""
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        assert adapter.estimate(frame) == []

    def test_estimate_returns_empty_when_no_pose(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """Sin pose detectada → []."""
        fake_landmarker.results = SimpleNamespace(pose_landmarks=[])

        result = adapter.estimate(np.zeros((480, 640, 3), dtype=np.uint8))

        assert result == []
        assert len(fake_landmarker.detect_calls) == 1

    def test_estimate_returns_empty_when_pose_landmarks_none(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """pose_landmarks None → []."""
        fake_landmarker.results = SimpleNamespace(pose_landmarks=None)

        result = adapter.estimate(np.zeros((480, 640, 3), dtype=np.uint8))

        assert result == []

    def test_estimate_maps_names_and_filters_low_visibility(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """Mapea nombres por índice y omite visibility < 0.5."""
        fake_landmarker.results = SimpleNamespace(
            pose_landmarks=[
                [
                    _landmark(0.1, 0.1, 0.9),  # idx 0 → nose
                    _landmark(0.2, 0.2, 0.4),  # descartado
                    _landmark(0.3, 0.3, 0.8),  # idx 2 → left_eye
                    _landmark(0.4, 0.4, 0.9),  # idx 3 → left_eye_outer
                ]
            ]
        )

        result = adapter.estimate(np.zeros((480, 640, 3), dtype=np.uint8))

        assert len(result) == 3
        assert result[0].name == "nose"
        assert result[1].name == "left_eye"
        assert result[2].name == "left_eye_outer"
        assert all(lm.visibility >= 0.5 for lm in result)

    def test_estimate_uses_fallback_name_for_unknown_index(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """Un índice fuera de LANDMARK_NAMES recibe nombre genérico."""
        padding = [_landmark(0.0, 0.0, 0.0) for _ in range(33)]
        fake_landmarker.results = SimpleNamespace(
            pose_landmarks=[padding + [_landmark(0.4, 0.4, 0.9)]]
        )

        result = adapter.estimate(np.zeros((480, 640, 3), dtype=np.uint8))

        assert len(result) == 1
        assert result[0].name == "landmark_33"

    def test_estimate_keeps_landmarks_at_visibility_threshold(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """visibility == 0.5 exacto se conserva (el filtro es estricto)."""
        fake_landmarker.results = SimpleNamespace(
            pose_landmarks=[[_landmark(0.5, 0.5, 0.5)]]
        )

        result = adapter.estimate(np.zeros((480, 640, 3), dtype=np.uint8))

        assert len(result) == 1
        assert result[0].visibility == 0.5

    def test_estimate_handles_non_contiguous_frame(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """Un frame con strides no contiguos se convierte antes de detectar."""
        fake_landmarker.results = SimpleNamespace(
            pose_landmarks=[[_landmark(0.5, 0.5, 0.9)]]
        )
        base = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = base[:, ::-1]  # negativo en el eje ancho
        assert not frame.flags["C_CONTIGUOUS"]

        result = adapter.estimate(frame)

        assert len(result) == 1


class TestDrawLandmarks:
    """Tests de MediapipeAdapter.draw_landmarks()."""

    def test_draw_landmarks_returns_same_frame_when_empty(
        self, adapter: MediapipeAdapter
    ) -> None:
        """Con lista vacía devuelve el mismo objeto sin dibujar."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = adapter.draw_landmarks(frame, [])

        assert result is frame

    def test_draw_landmarks_skips_invisible(
        self, adapter: MediapipeAdapter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Los landmarks invisibles no dibujan círculos."""
        drawn: list[object] = []
        monkeypatch.setattr(cv2, "circle", lambda *args, **_kw: drawn.append(args))

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = [PoseLandmark(0.5, 0.5, 0.0, 0.3, "nose")]

        adapter.draw_landmarks(frame, landmarks)

        assert drawn == []

    def test_draw_landmarks_draws_visible_with_name(
        self, adapter: MediapipeAdapter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un landmark visible dibuja círculo y etiqueta de nombre."""
        circles: list[object] = []
        texts: list[object] = []
        monkeypatch.setattr(cv2, "circle", lambda *args, **_kw: circles.append(args))
        monkeypatch.setattr(cv2, "putText", lambda *args, **_kw: texts.append(args))

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = [PoseLandmark(0.5, 0.5, 0.0, 1.0, "nose")]

        result = adapter.draw_landmarks(frame, landmarks)

        assert result is frame
        assert len(circles) == 1
        assert circles[0][1] == (320, 240)  # centro convertido a píxeles
        assert len(texts) == 1

    def test_draw_landmarks_skips_text_when_name_is_none(
        self, adapter: MediapipeAdapter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sin nombre no se dibuja putText, solo el círculo."""
        circles: list[object] = []
        texts: list[object] = []
        monkeypatch.setattr(cv2, "circle", lambda *args, **_kw: circles.append(args))
        monkeypatch.setattr(cv2, "putText", lambda *args, **_kw: texts.append(args))

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = [PoseLandmark(0.5, 0.5, 0.0, 1.0, None)]

        adapter.draw_landmarks(frame, landmarks)

        assert len(circles) == 1
        assert texts == []


class TestNamesAndLifecycle:
    """Tests de get_landmark_names(), close() y ciclo de vida."""

    def test_get_landmark_names_returns_mediapipe_names(
        self, adapter: MediapipeAdapter
    ) -> None:
        """Devuelve los 33 nombres del esqueleto de Mediapipe."""
        names = adapter.get_landmark_names()

        assert len(names) == 33
        assert names[0] == "nose"
        assert "left_shoulder" in names

    def test_close_releases_landmarker(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """close() cierra el landmarker inyectado."""
        adapter.close()

        assert fake_landmarker.closed is True

    def test_close_without_landmarker_is_noop(self) -> None:
        """close() sin landmarker (init fallido) no lanza."""
        bare = MediapipeAdapter.__new__(MediapipeAdapter)

        bare.close()  # no debe lanzar

    def test_context_manager_closes_on_exit(
        self, fake_landmarker: FakeLandmarker, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """with cierra el adaptador al salir del bloque."""
        monkeypatch.setattr(
            vision.PoseLandmarker,
            "create_from_options",
            staticmethod(lambda _options: fake_landmarker),
        )

        with MediapipeAdapter() as instance:
            assert isinstance(instance._landmarker, FakeLandmarker)
            assert fake_landmarker.closed is False

        assert fake_landmarker.closed is True

    def test_del_closes_landmarker(
        self, adapter: MediapipeAdapter, fake_landmarker: FakeLandmarker
    ) -> None:
        """__del__() cierra el landmarker si existe."""
        adapter.__del__()

        assert fake_landmarker.closed is True

    def test_del_without_landmarker_is_noop(self) -> None:
        """__del__() sin landmarker no lanza."""
        bare = MediapipeAdapter.__new__(MediapipeAdapter)

        bare.__del__()  # no debe lanzar
