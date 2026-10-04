# debug_mediapipe_tasks.py (en la raíz del proyecto)
"""
Reproduce el segfault fuera de pytest para ver dónde ocurre.
"""

import numpy as np

from adapters.pose.mediapipe_adapter import MediapipeAdapter

print("1. Creando adapter...")
adapter = MediapipeAdapter(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1,
)
print("   ✅ OK")

print("2. Frame negro 480x640...")
frame_negro = np.zeros((480, 640, 3), dtype=np.uint8)
try:
    landmarks = adapter.estimate(frame_negro)
    print(f"   ✅ OK, landmarks={len(landmarks)}")
except Exception as e:
    print(f"   ❌ Excepción: {e}")

print("3. Frame gris 480x640...")
frame_gris = np.full((480, 640, 3), 128, dtype=np.uint8)
try:
    landmarks = adapter.estimate(frame_gris)
    print(f"   ✅ OK, landmarks={len(landmarks)}")
except Exception as e:
    print(f"   ❌ Excepción: {e}")

print("4. Cerrando adapter...")
adapter.close()
print("   ✅ OK")
