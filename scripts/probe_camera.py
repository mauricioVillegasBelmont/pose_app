# scripts/probe_camera.py
import time

import cv2

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# Verificar el formato realmente obtenido
actual_fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
fcc_str = "".join([chr((actual_fourcc >> (8 * i)) & 0xFF) for i in range(4)])
print(f"Formato real: {fcc_str}")  # Esperado: MJPG

frames = 0
t_start = time.perf_counter()
while time.perf_counter() - t_start < 5.0:
    ok, _ = cap.read()
    if ok:
        frames += 1
elapsed = time.perf_counter() - t_start
print(f"Captura pura: {frames / elapsed:.1f} FPS ({frames} frames en {elapsed:.2f}s)")
cap.release()
