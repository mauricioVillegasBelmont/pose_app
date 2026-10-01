# tests/integration/pose/test_mediapipe_adapter.py
"""
Tests del MediapipeAdapter.

IMPORTANTE: estos tests INICIALIZAN MEDIAPIPE REAL (no mockeado).
Por eso están marcados como @pytest.mark.slow y viven en integration.

Para correr solo estos tests:
    pytest -m slow -v

Para correrlos en subprocesos aislados (evita segfaults que maten pytest):
    pytest --forked -m slow -v
"""

import numpy as np
import pytest

from adapters.pose.mediapipe_adapter import MediapipeAdapter
from domain.entities.pose_landmark import PoseLandmark


@pytest.mark.slow
class TestMediapipeAdapterIntegration:
    """Tests de integración con Mediapipe real."""

    @pytest.fixture(autouse=True)
    def adapter(self):
        """Crea el adapter antes de cada test y lo cierra al final."""
        adapter = MediapipeAdapter(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
        )
        yield adapter
        adapter.close()

    # ==========================================
    # Validaciones de input (no llegan a Mediapipe)
    # ==========================================

    def test_estimate_returns_empty_for_none(self, adapter):
        assert adapter.estimate(None) == []

    def test_estimate_returns_empty_for_empty_array(self, adapter):
        frame = np.zeros((0, 0, 3), dtype=np.uint8)
        assert adapter.estimate(frame) == []

    def test_estimate_rejects_invalid_shape(self, adapter):
        # Grayscale (2D)
        assert adapter.estimate(np.zeros((480, 640), dtype=np.uint8)) == []
        # 4 canales
        assert adapter.estimate(np.zeros((480, 640, 4), dtype=np.uint8)) == []

    def test_estimate_rejects_too_small_frame(self, adapter):
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        assert adapter.estimate(frame) == []

    # ==========================================
    # Con Mediapipe real
    # ==========================================

    def test_estimate_returns_empty_when_no_pose(self, adapter):
        """Frame negro sin persona → []."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = adapter.estimate(frame)
        assert landmarks == []

    def test_draw_landmarks_returns_same_shape(self, adapter):
        """draw_landmarks no cambia el shape."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = [PoseLandmark(0.5, 0.5, 0.0, 1.0, "nose")]
        result = adapter.draw_landmarks(frame, landmarks)
        assert result.shape == frame.shape