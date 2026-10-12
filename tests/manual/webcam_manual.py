# test_webcam.py
import cv2

from adapters.camera.webcam_adapter import WebcamAdapter

cam = WebcamAdapter()
cam.start()

for _ in range(100):
    frame = cam.get_frame()
    if frame is not None:
        cv2.imshow("Webcam Test", frame)
        cv2.waitKey(30)

cam.stop()
cv2.destroyAllWindows()
