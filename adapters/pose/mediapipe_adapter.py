import cv2
import mediapipe as mp
import numpy as np

from domain.entities.pose_landmark import PoseLandmark
from domain.ports.pose_estimator_port import PoseEstimatorPort


class MediapipeAdapter(PoseEstimatorPort):
    """
    Adaptador de estimación de pose usando Mediapipe.

    Características:
    - Modelo de 33 landmarks
    - Coordenadas normalizadas (0-1)
    - Filtrado por visibilidad
    - Configurable: static_image_mode, min_detection_confidence
    """

    # Mapeo de índices de Mediapipe a nombres descriptivos
    LANDMARK_NAMES: dict[int, str] = {
        0: 'nose',
        1: 'left_eye_inner', 2: 'left_eye', 3: 'left_eye_outer',
        4: 'right_eye_inner', 5: 'right_eye', 6: 'right_eye_outer',
        7: 'left_ear', 8: 'right_ear',
        9: 'mouth_left', 10: 'mouth_right',
        11: 'left_shoulder', 12: 'right_shoulder',
        13: 'left_elbow', 14: 'right_elbow',
        15: 'left_wrist', 16: 'right_wrist',
        17: 'left_pinky', 18: 'right_pinky',
        19: 'left_index', 20: 'right_index',
        21: 'left_thumb', 22: 'right_thumb',
        23: 'left_hip', 24: 'right_hip',
        25: 'left_knee', 26: 'right_knee',
        27: 'left_ankle', 28: 'right_ankle',
        29: 'left_heel', 30: 'right_heel',
        31: 'left_foot_index', 32: 'right_foot_index'
    }

    # Nombres de landmarks que consideramos "clave" para nuestro dominio
    KEY_LANDMARKS = [
        'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist',
        'left_hip', 'right_hip',
        'left_knee', 'right_knee',
        'left_ankle', 'right_ankle',
        'nose'
    ]

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_complexity: int = 1  # 0, 1, o 2 (más complejo = más preciso pero más lento)
    ):
        """
        Args:
            min_detection_confidence: Confianza mínima para detección (0-1)
            min_tracking_confidence: Confianza mínima para tracking (0-1)
            model_complexity: Complejidad del modelo (0=ligero, 1=medio, 2=pesado)
        """
        self._min_detection_confidence = min_detection_confidence
        self._min_tracking_confidence = min_tracking_confidence
        self._model_complexity = model_complexity

        # Inicializa Mediapipe Pose
        self._mp_pose = mp.solutions.pose
        self._pose = self._mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        # Cache de nombres para conversión rápida
        self._landmark_name_cache: dict[int, str] = self.LANDMARK_NAMES.copy()

        print(f"🦾 Mediapipe inicializado (modelo complejidad={model_complexity})")

    def estimate(self, frame: np.ndarray) -> list[PoseLandmark]:
        """
        Estima la pose en un frame BGR.

        Args:
            frame: Imagen en formato BGR (numpy array)

        Returns:
            Lista de PoseLandmark (solo los visibles con confianza > 0.5)
        """
        if frame is None or frame.size == 0:
            return []

        # Mediapipe espera RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Procesa el frame
        results = self._pose.process(rgb_frame)

        if not results.pose_landmarks:
            return []

        # Convierte los landmarks de Mediapipe a nuestros objetos
        landmarks = []
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            # Solo incluye landmarks con visibilidad > 0.5 (regla de negocio)
            if landmark.visibility < 0.5:
                continue

            name = self._landmark_name_cache.get(idx, f'landmark_{idx}')

            pose_landmark = PoseLandmark(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=landmark.visibility,
                name=name
            )
            landmarks.append(pose_landmark)

        # Opcional: filtramos solo landmarks clave (para reducir ruido)
        # Descomenta si quieres solo los esenciales
        # landmarks = [lm for lm in landmarks if lm.name in self.KEY_LANDMARKS]

        return landmarks

    def get_landmark_names(self) -> list[str]:
        """Devuelve todos los nombres de landmarks soportados."""
        return list(self.LANDMARK_NAMES.values())

    def draw_landmarks(self, frame: np.ndarray, landmarks: list[PoseLandmark]) -> np.ndarray:
        """
        Dibuja los landmarks en el frame (útil para debugging).

        Args:
            frame: Imagen original (BGR)
            landmarks: Lista de PoseLandmark a dibujar

        Returns:
            Frame con landmarks dibujados
        """
        if not landmarks:
            return frame

        # Obtén dimensiones del frame
        height, width = frame.shape[:2]

        for lm in landmarks:
            if not lm.is_visible():
                continue

            # Convierte coordenadas normalizadas a píxeles
            x = int(lm.x * width)
            y = int(lm.y * height)

            # Dibuja círculo
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            # Opcional: dibuja nombre
            if lm.name:
                cv2.putText(
                    frame, lm.name, (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1
                )

        return frame

    def close(self) -> None:
        """Libera recursos de Mediapipe."""
        if hasattr(self, '_pose') and self._pose:
            self._pose.close()
            print("🦾 Mediapipe cerrado")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()