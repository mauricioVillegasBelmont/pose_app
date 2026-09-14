import numpy as np

from domain.entities.pose_landmark import PoseLandmark
from domain.ports.pose_estimator_port import PoseEstimatorPort


class MockPoseAdapter(PoseEstimatorPort):
    """Mock que devuelve landmarks predefinidos (para testing)."""

    def __init__(self):
        # Crea un esqueleto simulado en posición de "T"
        self._mock_landmarks = self._create_t_pose()

    def estimate(self, frame: np.ndarray) -> list[PoseLandmark]:
        # En un mock real, podrías variar ligeramente según el frame
        # pero aquí devolvemos siempre la misma pose
        return self._mock_landmarks.copy()

    def get_landmark_names(self) -> list[str]:
        return [lm.name for lm in self._mock_landmarks if lm.name]

    def _create_t_pose(self) -> list[PoseLandmark]:
        """Crea landmarks en pose de 'T' para testing."""
        # Solo algunos puntos clave para simplicidad
        return [
            PoseLandmark(0.5, 0.2, 0.0, 1.0, 'nose'),
            PoseLandmark(0.3, 0.3, 0.0, 1.0, 'left_shoulder'),
            PoseLandmark(0.7, 0.3, 0.0, 1.0, 'right_shoulder'),
            PoseLandmark(0.1, 0.5, 0.0, 1.0, 'left_wrist'),
            PoseLandmark(0.9, 0.5, 0.0, 1.0, 'right_wrist'),
            PoseLandmark(0.3, 0.7, 0.0, 1.0, 'left_hip'),
            PoseLandmark(0.7, 0.7, 0.0, 1.0, 'right_hip'),
        ]