import sys
from pathlib import Path

# Agrega la raíz del proyecto a sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
import time

import cv2

from adapters.camera.webcam_adapter import WebcamAdapter
from adapters.pose.mediapipe_adapter import MediapipeAdapter


def test_webcam_with_mediapipe():
    """
    Prueba de integración: cámara real + Mediapipe real.
    Visualiza los landmarks detectados en tiempo real.
    """
    # Arrange
    camera = WebcamAdapter(camera_id=0, width=640, height=480)
    pose_estimator = MediapipeAdapter(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1  # Balance entre velocidad y precisión
    )

    # Act: captura y estima por 10 segundos
    camera.start()

    start_time = time.time()
    frame_count = 0

    try:
        while time.time() - start_time < 10.0:
            frame = camera.get_frame()
            if frame is None:
                continue

            # Estima pose
            landmarks = pose_estimator.estimate(frame)

            # Dibuja landmarks en el frame
            debug_frame = pose_estimator.draw_landmarks(frame, landmarks)

            # Muestra FPS
            frame_count += 1
            if frame_count % 10 == 0:
                fps = camera.get_fps()
                cv2.putText(
                    debug_frame, f"FPS: {fps:.1f} | Landmarks: {len(landmarks)}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
                )

            # Muestra el frame
            cv2.imshow("Webcam + Mediapipe", debug_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nInterrupción por usuario")

    finally:
        # Cleanup
        camera.stop()
        pose_estimator.close()
        cv2.destroyAllWindows()

    print(f"✅ Prueba completada: {frame_count} frames procesados")

    # Assert básico
    assert frame_count > 0, "No se procesaron frames"


if __name__ == "__main__":
    test_webcam_with_mediapipe()