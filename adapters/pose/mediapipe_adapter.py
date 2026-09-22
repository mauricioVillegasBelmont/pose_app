import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from domain.entities.pose_landmark import PoseLandmark
from domain.ports.pose_estimator_port import PoseEstimatorPort


class MediapipeAdapter(PoseEstimatorPort):
    """
    Adaptador para Pose Landmarker de mediapipe==1.0.1 (Tasks API).
    La primera ejecución descargará automáticamente el archivo de modelo pose_landmarker_full.task.
    """

    # Dirección de descarga del modelo (versión full, equilibra precisión y velocidad)
    MODEL_URL = (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
    )

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
        model_complexity: int = 1
    ):
        """
        Args:
            min_detection_confidence: Umbral de confianza de detección.
            min_tracking_confidence: Umbral de confianza de seguimiento (tracking).
            model_complexity: Se mantiene el parámetro por compatibilidad con llamadas antiguas
                              (en la Tasks API el modelo se define por el archivo .task).
        """
        self._min_detection_confidence = min_detection_confidence
        self._min_tracking_confidence = min_tracking_confidence
        self._model_complexity = model_complexity

        # 1. Asegurar que el archivo del modelo exista
        model_path = self._ensure_model()

        # 2. Inicializar PoseLandmarker de la Tasks API
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        # 3. Cachear nombres
        self._landmark_name_cache = self.LANDMARK_NAMES.copy()

        print(f"🦾 Mediapipe Tasks API inicializado (complejidad del modelo={model_complexity})")

    def _ensure_model(self) -> str:
        """Verifica si el archivo del modelo existe; si no, lo descarga automáticamente."""
        model_dir = Path(__file__).parent / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "pose_landmarker_full.task"

        if not model_path.exists():
            print(f"📥 Descargando modelo de MediaPipe en {model_path} …")
            try:
                urllib.request.urlretrieve(self.MODEL_URL, str(model_path))
                print("✅ Descarga del modelo completada")
            except Exception as e:
                raise RuntimeError(
                    f"No se pudo descargar el archivo del modelo. Por favor, descárgalo manualmente desde {self.MODEL_URL} "
                    f"y guárdalo en {model_path}"
                ) from e
        return str(model_path)

    def estimate(self, frame: np.ndarray) -> list[PoseLandmark]:
        """Estima la postura y devuelve una lista de PoseLandmark que sean visibles."""
        if frame is None or frame.size == 0:
            return []

        # 1. BGR -> RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 2. Construir mp.Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # 3. Llamar a detect (la Tasks API ya no utiliza .process)
        results = self._landmarker.detect(mp_image)

        if not results.pose_landmarks:
            return []

        # 4. La nueva API devuelve una lista (puede haber múltiples posturas por imagen), se toma la primera
        first_pose_landmarks = results.pose_landmarks[0]

        landmarks = []
        for idx, landmark in enumerate(first_pose_landmarks):
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

        return landmarks

    def get_landmark_names(self) -> list[str]:
        return list(self.LANDMARK_NAMES.values())

    def draw_landmarks(self, frame: np.ndarray, landmarks: list[PoseLandmark]) -> np.ndarray:
        """Dibuja manualmente los puntos de referencia (mantiene la lógica original sin depender del obsoleto drawing_utils)."""
        if not landmarks:
            return frame

        height, width = frame.shape[:2]

        for lm in landmarks:
            if not lm.is_visible():
                continue

            x = int(lm.x * width)
            y = int(lm.y * height)

            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            if lm.name:
                cv2.putText(
                    frame, lm.name, (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1
                )

        return frame

    def close(self) -> None:
        if hasattr(self, '_landmarker') and self._landmarker:
            self._landmarker.close()
            print("🦾 Mediapipe ha sido cerrado")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()
