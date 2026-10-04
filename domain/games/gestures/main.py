"""
Juego de reconocimiento de gestos.

Reconoce 6 gestos a partir de landmarks de pose y, cuando un gesto
se mantiene durante N frames consecutivos, lo marca como "activado"
y loguea "<pose_name> done!".

Cuando el gesto deja de detectarse, se "desactiva" (permite re-disparar
si el usuario lo vuelve a hacer).
"""

import asyncio
from collections.abc import Callable

from domain.entities.gesture import Gesture
from domain.entities.pose_landmark import PoseLandmark
from domain.games.gestures.state import GesturesState
from domain.ports.camera_port import CameraPort
from domain.ports.event_bus_port import EventBusPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import ColorRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("use_cases.gestures")


class GesturesGame:
    """
    Juego que detecta gestos y loguea cuando se completan.

    Detección por reglas simples sobre landmarks de Mediapipe.
    """

    # ==========================================
    # Parámetros de detección (reglas de negocio)
    # ==========================================

    # Cuántos frames consecutivos debe mantenerse un gesto para activarse.
    # A 30 FPS, 8 frames ~ 0.27s. Evita falsos positivos por ruido.
    MIN_FRAMES_TO_ACTIVATE = 8

    # Margen vertical (en coords normalizadas) para considerar algo "arriba"
    UP_MARGIN = 0.05

    # Umbral de distancia para "mano cerca de la cabeza"
    GREETING_MAX_DISTANCE = 0.15

    # Umbral de distancia para "brazos cruzados"
    CROSSED_ARMS_MAX_DISTANCE = 0.2

    # Ángulo máximo de rodilla para considerar "cuclillas" (en grados)
    SQUAT_MAX_KNEE_ANGLE = 130.0

    # Margen para considerar "un tobillo elevado"
    ONE_LEG_MARGIN = 0.03

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        renderer: ColorRenderPort,
        state: GesturesState,
        event_bus: EventBusPort,
    ):
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._renderer = renderer
        self._state = state
        self._event_bus = event_bus

        self._frame_count = 0

        # Contadores consecutivos por gesto (para activación)
        self._consecutive_frames: dict[Gesture, int] = {g: 0 for g in Gesture}

        # Qué gestos están activos AHORA (ya disparados)
        self._active: set[Gesture] = set()

    @property
    def state(self) -> GesturesState:
        return self._state

    # ==========================================
    # Loop principal
    # ==========================================

    async def run_async(self, should_stop: Callable[[], bool] | None = None) -> None:
        should_stop = should_stop or (lambda: False)

        await asyncio.to_thread(self._camera.start)
        logger.info("Juego de gestures iniciado")

        try:
            while not should_stop():
                frame = await asyncio.to_thread(self._camera.get_frame)
                if frame is None:
                    await asyncio.sleep(0.001)
                    continue

                try:
                    landmarks = await asyncio.to_thread(
                        self._pose_estimator.estimate, frame
                    )
                except Exception as e:
                    logger.warning(f"Error estimando pose: {e}")
                    continue

                # Procesa gestos y actualiza estado
                self._process_frame(landmarks)
                self._state.increment_frames()

                # Render (fondo + esqueleto)
                try:
                    from domain.entities.color import RGBColor

                    await asyncio.to_thread(
                        self._renderer.render_background,
                        RGBColor(20, 20, 30),
                        landmarks,
                    )
                except Exception as e:
                    logger.error(f"Error renderizando: {e}")
                    break

                self._frame_count += 1
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info("Juego de gestures cancelado")
            raise
        finally:
            try:
                self._renderer.close()
            except Exception as e:
                logger.error(f"Error cerrando renderer: {e}")
            try:
                await asyncio.to_thread(self._camera.stop)
            except Exception as e:
                logger.error(f"Error cerrando cámara: {e}")
            logger.info(f"Juego gestures terminado. Frames: {self._frame_count}")

    # ==========================================
    # Procesamiento por frame
    # ==========================================

    def _process_frame(self, landmarks: list[PoseLandmark]) -> None:
        """Detecta gestos y actualiza contadores/estado."""
        # 1. Detección pura: ¿qué gestos se ven AHORA?
        detected: set[Gesture] = set()
        for gesture, detector in self._detectors().items():
            try:
                if detector(landmarks):
                    detected.add(gesture)
            except Exception as e:
                logger.debug(f"Error detectando {gesture.value}: {e}")

        # 2. Actualiza contadores consecutivos y detecta activaciones nuevas
        newly_activated: set[Gesture] = set()

        for gesture in Gesture:
            if gesture in detected:
                self._consecutive_frames[gesture] += 1

                # Umbral alcanzado y aún no activado → activar
                if (
                    self._consecutive_frames[gesture] >= self.MIN_FRAMES_TO_ACTIVATE
                    and gesture not in self._active
                ):
                    self._active.add(gesture)
                    newly_activated.add(gesture)
                    self._on_gesture_activated(gesture)
            else:
                # Gesto no detectado → resetear contador y desactivar
                if gesture in self._active:
                    self._on_gesture_deactivated(gesture)
                    self._active.discard(gesture)
                self._consecutive_frames[gesture] = 0

        # 3. Publica al estado
        self._state.update_active_gestures(
            newly_activated=newly_activated,
            currently_active=self._active,
        )

    def _on_gesture_activated(self, gesture: Gesture) -> None:
        """Log + hook para futuras acciones (puntos, eventos, etc.)."""
        logger.info(f"✅ {gesture.display_name} done!")

    def _on_gesture_deactivated(self, gesture: Gesture) -> None:
        """Log de desactivación (útil para debug)."""
        logger.debug(f"⏹️  {gesture.display_name} released")

    # ==========================================
    # Detectores (reglas de negocio puras)
    # ==========================================

    def _detectors(self) -> dict[Gesture, Callable[[list[PoseLandmark]], bool]]:
        """Mapa gesto → función de detección."""
        return {
            Gesture.HAND_UP: self._detect_hand_up,
            Gesture.GREETING: self._detect_greeting,
            Gesture.ARMS_CROSSED: self._detect_arms_crossed,
            Gesture.T_POSE: self._detect_t_pose,
            Gesture.SQUAT: self._detect_squat,
            Gesture.ONE_LEG_BALANCE: self._detect_one_leg_balance,
        }

    def _detect_hand_up(self, landmarks: list[PoseLandmark]) -> bool:
        """
        Mano arriba: al menos una muñeca está por encima de su hombro.
        """
        left_wrist = self._find(landmarks, "left_wrist")
        left_shoulder = self._find(landmarks, "left_shoulder")
        right_wrist = self._find(landmarks, "right_wrist")
        right_shoulder = self._find(landmarks, "right_shoulder")

        left_up = (
            left_wrist
            and left_shoulder
            and left_wrist.is_visible()
            and left_shoulder.is_visible()
            and left_wrist.y < left_shoulder.y - self.UP_MARGIN
        )
        right_up = (
            right_wrist
            and right_shoulder
            and right_wrist.is_visible()
            and right_shoulder.is_visible()
            and right_wrist.y < right_shoulder.y - self.UP_MARGIN
        )

        return bool(left_up or right_up)

    def _detect_greeting(self, landmarks: list[PoseLandmark]) -> bool:
        """Saludo: alguna muñeca está cerca de la nariz."""
        nose = self._find(landmarks, "nose")
        if not nose or not nose.is_visible():
            return False

        for side in ("left", "right"):
            wrist = self._find(landmarks, f"{side}_wrist")
            if wrist and wrist.is_visible():
                if wrist.distance_to(nose) < self.GREETING_MAX_DISTANCE:
                    return True
        return False

    def _detect_arms_crossed(self, landmarks: list[PoseLandmark]) -> bool:
        """
        Brazos cruzados: cada muñeca está cerca del hombro OPUESTO.
        """
        left_wrist = self._find(landmarks, "left_wrist")
        right_wrist = self._find(landmarks, "right_wrist")
        left_shoulder = self._find(landmarks, "left_shoulder")
        right_shoulder = self._find(landmarks, "right_shoulder")

        if not all(
            lm and lm.is_visible()
            for lm in (left_wrist, right_wrist, left_shoulder, right_shoulder)
        ):
            return False

        assert left_wrist and right_wrist and left_shoulder and right_shoulder
        left_to_right_shoulder = left_wrist.distance_to(right_shoulder)
        right_to_left_shoulder = right_wrist.distance_to(left_shoulder)

        return (
            left_to_right_shoulder < self.CROSSED_ARMS_MAX_DISTANCE
            and right_to_left_shoulder < self.CROSSED_ARMS_MAX_DISTANCE
        )

    def _detect_t_pose(self, landmarks: list[PoseLandmark]) -> bool:
        """
        Pose de T: ambas muñecas extendidas horizontalmente a la altura
        de los hombros, alejadas del torso.
        """
        left_wrist = self._find(landmarks, "left_wrist")
        right_wrist = self._find(landmarks, "right_wrist")
        left_shoulder = self._find(landmarks, "left_shoulder")
        right_shoulder = self._find(landmarks, "right_shoulder")

        if not all(
            lm and lm.is_visible()
            for lm in (left_wrist, right_wrist, left_shoulder, right_shoulder)
        ):
            return False

        assert left_wrist and right_wrist and left_shoulder and right_shoulder

        # Verticalmente alineadas (y similar a hombros)
        margin_y = 0.1
        left_aligned = abs(left_wrist.y - left_shoulder.y) < margin_y
        right_aligned = abs(right_wrist.y - right_shoulder.y) < margin_y

        # Horizontalmente extendidas (fuera del torso)
        left_extended = left_wrist.x < left_shoulder.x - 0.1
        right_extended = right_wrist.x > right_shoulder.x + 0.1

        return bool(left_aligned and right_aligned and left_extended and right_extended)

    def _detect_squat(self, landmarks: list[PoseLandmark]) -> bool:
        """
        Cuclillas: al menos una rodilla doblada con ángulo < umbral.
        """
        for side in ("left", "right"):
            hip = self._find(landmarks, f"{side}_hip")
            knee = self._find(landmarks, f"{side}_knee")
            ankle = self._find(landmarks, f"{side}_ankle")

            if not (hip and knee and ankle):
                continue
            if not (hip.is_visible() and knee.is_visible() and ankle.is_visible()):
                continue

            angle = self._angle_at(hip, knee, ankle)
            if angle < self.SQUAT_MAX_KNEE_ANGLE:
                return True

        return False

    def _detect_one_leg_balance(self, landmarks: list[PoseLandmark]) -> bool:
        """
        Equilibrio en un pie: un tobillo elevado (más arriba que su rodilla),
        el otro en el suelo.
        """
        results: dict[str, bool] = {}

        for side in ("left", "right"):
            knee = self._find(landmarks, f"{side}_knee")
            ankle = self._find(landmarks, f"{side}_ankle")

            if not (knee and ankle):
                results[side] = False
                continue
            if not (knee.is_visible() and ankle.is_visible()):
                results[side] = False
                continue

            # Tobillo elevado: su y es MENOR que la rodilla - margen
            results[side] = ankle.y < knee.y - self.ONE_LEG_MARGIN

        # Exactamente uno elevado
        return results["left"] != results["right"]

    # ==========================================
    # Helpers geométricos
    # ==========================================

    def _find(self, landmarks: list[PoseLandmark], name: str) -> PoseLandmark | None:
        for lm in landmarks:
            if lm.name and lm.name.lower() == name.lower():
                return lm
        return None

    @staticmethod
    def _angle_at(a: PoseLandmark, vertex: PoseLandmark, b: PoseLandmark) -> float:
        """
        Ángulo en grados en el vértice `vertex`, formado por a-vertex-b.
        Usa solo coordenadas x,y (ignora z, que suele ser ruidoso).
        """
        import math

        v1x, v1y = a.x - vertex.x, a.y - vertex.y
        v2x, v2y = b.x - vertex.x, b.y - vertex.y

        dot = v1x * v2x + v1y * v2y
        mag1 = math.hypot(v1x, v1y)
        mag2 = math.hypot(v2x, v2y)

        if mag1 == 0 or mag2 == 0:
            return 0.0

        cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        return math.degrees(math.acos(cos_angle))
