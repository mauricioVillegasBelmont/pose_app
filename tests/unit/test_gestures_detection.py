"""
Tests unitarios de las reglas de detección de gestos.

Cada test crea landmarks sintéticos y verifica el detector.
"""

import pytest

from domain.entities.pose_landmark import PoseLandmark
from domain.games.gestures.main import GesturesGame

# ==========================================
# Helper para crear landmarks
# ==========================================


def lm(name: str, x: float, y: float, vis: float = 1.0) -> PoseLandmark:
    return PoseLandmark(x=x, y=y, z=0.0, visibility=vis, name=name)


@pytest.fixture
def game() -> GesturesGame:
    """Instancia sin dependencias reales (solo para probar detectores)."""
    return GesturesGame(
        camera=None,  # type: ignore
        pose_estimator=None,  # type: ignore
        renderer=None,  # type: ignore
        state=None,  # type: ignore
        event_bus=None,  # type: ignore
    )


# ==========================================
# HAND_UP
# ==========================================


def test_hand_up_left_wrist_above_shoulder(game: GesturesGame):
    landmarks = [
        lm("left_shoulder", 0.3, 0.5),
        lm("left_wrist", 0.3, 0.2),  # arriba
        lm("right_shoulder", 0.7, 0.5),
        lm("right_wrist", 0.7, 0.6),  # abajo
    ]
    assert game._detect_hand_up(landmarks) is True


def test_hand_up_both_wrists_below_shoulders(game: GesturesGame):
    landmarks = [
        lm("left_shoulder", 0.3, 0.5),
        lm("left_wrist", 0.3, 0.6),
        lm("right_shoulder", 0.7, 0.5),
        lm("right_wrist", 0.7, 0.6),
    ]
    assert game._detect_hand_up(landmarks) is False


def test_hand_up_ignores_invisible_wrist(game: GesturesGame):
    landmarks = [
        lm("left_shoulder", 0.3, 0.5),
        lm("left_wrist", 0.3, 0.2, vis=0.1),  # invisible
        lm("right_shoulder", 0.7, 0.5),
        lm("right_wrist", 0.7, 0.6),
    ]
    assert game._detect_hand_up(landmarks) is False


# ==========================================
# GREETING
# ==========================================


def test_greeting_wrist_near_nose(game: GesturesGame):
    landmarks = [
        lm("nose", 0.5, 0.3),
        lm("right_wrist", 0.53, 0.32),  # muy cerca
    ]
    assert game._detect_greeting(landmarks) is True


def test_greeting_wrist_far(game: GesturesGame):
    landmarks = [
        lm("nose", 0.5, 0.3),
        lm("right_wrist", 0.9, 0.9),  # lejos
    ]
    assert game._detect_greeting(landmarks) is False


# ==========================================
# ARMS_CROSSED
# ==========================================


def test_arms_crossed_valid(game: GesturesGame):
    landmarks = [
        lm("left_shoulder", 0.3, 0.5),
        lm("right_shoulder", 0.7, 0.5),
        lm("left_wrist", 0.65, 0.55),  # cerca del hombro derecho
        lm("right_wrist", 0.35, 0.55),  # cerca del hombro izquierdo
    ]
    assert game._detect_arms_crossed(landmarks) is True


def test_arms_crossed_not_valid(game: GesturesGame):
    landmarks = [
        lm("left_shoulder", 0.3, 0.5),
        lm("right_shoulder", 0.7, 0.5),
        lm("left_wrist", 0.2, 0.6),  # lejos
        lm("right_wrist", 0.8, 0.6),
    ]
    assert game._detect_arms_crossed(landmarks) is False


# ==========================================
# T_POSE
# ==========================================


def test_t_pose_valid(game: GesturesGame):
    landmarks = [
        lm("left_shoulder", 0.4, 0.5),
        lm("right_shoulder", 0.6, 0.5),
        lm("left_wrist", 0.2, 0.5),  # extendido horizontal
        lm("right_wrist", 0.8, 0.5),
    ]
    assert game._detect_t_pose(landmarks) is True


def test_t_pose_wrists_down(game: GesturesGame):
    landmarks = [
        lm("left_shoulder", 0.4, 0.5),
        lm("right_shoulder", 0.6, 0.5),
        lm("left_wrist", 0.2, 0.8),  # abajo
        lm("right_wrist", 0.8, 0.8),
    ]
    assert game._detect_t_pose(landmarks) is False


# ==========================================
# SQUAT
# ==========================================


def test_squat_deep_knee_bend(game: GesturesGame):
    """
    Rodilla doblada en ángulo agudo.
    Hip arriba, knee adelante, ankle abajo → ángulo < 130°.
    """
    landmarks = [
        lm("left_hip", 0.5, 0.4),
        lm("left_knee", 0.55, 0.55),
        lm("left_ankle", 0.45, 0.7),  # pie "hacia atrás" respecto a rodilla
    ]
    # Calculamos: la rodilla está "adelante", el tobillo detrás
    # El ángulo hip-knee-ankle debería ser agudo
    assert game._detect_squat(landmarks) is True


def test_squat_standing_straight(game: GesturesGame):
    """
    Pierna recta vertical: hip, knee, ankle alineados.
    Ángulo cercano a 180° → no es cuclillas.
    """
    landmarks = [
        lm("left_hip", 0.5, 0.4),
        lm("left_knee", 0.5, 0.55),
        lm("left_ankle", 0.5, 0.7),
    ]
    assert game._detect_squat(landmarks) is False


# ==========================================
# ONE_LEG_BALANCE
# ==========================================


def test_one_leg_balance_left_up(game: GesturesGame):
    """Rodilla izquierda elevada (y menor), la derecha normal."""
    landmarks = [
        lm("left_knee", 0.4, 0.5),
        lm("left_ankle", 0.4, 0.4),  # tobillo arriba de rodilla
        lm("right_knee", 0.6, 0.55),
        lm("right_ankle", 0.6, 0.75),  # tobillo abajo
    ]
    assert game._detect_one_leg_balance(landmarks) is True


def test_one_leg_balance_both_down(game: GesturesGame):
    landmarks = [
        lm("left_knee", 0.4, 0.5),
        lm("left_ankle", 0.4, 0.7),
        lm("right_knee", 0.6, 0.5),
        lm("right_ankle", 0.6, 0.7),
    ]
    assert game._detect_one_leg_balance(landmarks) is False


# ==========================================
# Activación por frames consecutivos
# ==========================================


def test_gesture_activates_after_min_frames(game: GesturesGame):
    """
    Verifica que el gesto requiera MIN_FRAMES_TO_ACTIVATE frames
    para activarse.
    """
    from domain.games.gestures.state import GesturesState

    game._state = GesturesState()

    landmarks = [
        lm("left_shoulder", 0.3, 0.5),
        lm("left_wrist", 0.3, 0.2),  # mano arriba
        lm("right_shoulder", 0.7, 0.5),
        lm("right_wrist", 0.7, 0.6),
    ]

    # Procesar menos de MIN_FRAMES frames → no debe activarse
    for _ in range(GesturesGame.MIN_FRAMES_TO_ACTIVATE - 1):
        game._process_frame(landmarks)

    snapshot = game._state.snapshot()
    assert snapshot["activation_counts"]["hand_up"] == 0

    # Un frame más → debe activarse
    game._process_frame(landmarks)
    snapshot = game._state.snapshot()
    assert snapshot["activation_counts"]["hand_up"] == 1


def test_gesture_does_not_reactivate_while_held(game: GesturesGame):
    """Mientras el gesto se mantiene, no debe re-contar."""
    from domain.games.gestures.state import GesturesState

    game._state = GesturesState()

    landmarks = [
        lm("left_shoulder", 0.3, 0.5),
        lm("left_wrist", 0.3, 0.2),
        lm("right_shoulder", 0.7, 0.5),
        lm("right_wrist", 0.7, 0.6),
    ]

    # 30 frames con el gesto activo
    for _ in range(30):
        game._process_frame(landmarks)

    snapshot = game._state.snapshot()
    assert snapshot["activation_counts"]["hand_up"] == 1  # Solo una vez


def test_gesture_reactivates_after_release(game: GesturesGame):
    """Si se suelta y se vuelve a hacer, cuenta de nuevo."""
    from domain.games.gestures.state import GesturesState

    game._state = GesturesState()

    up = [
        lm("left_shoulder", 0.3, 0.5),
        lm("left_wrist", 0.3, 0.2),
        lm("right_shoulder", 0.7, 0.5),
        lm("right_wrist", 0.7, 0.6),
    ]
    down = [
        lm("left_shoulder", 0.3, 0.5),
        lm("left_wrist", 0.3, 0.6),
        lm("right_shoulder", 0.7, 0.5),
        lm("right_wrist", 0.7, 0.6),
    ]

    # Activa
    for _ in range(GesturesGame.MIN_FRAMES_TO_ACTIVATE):
        game._process_frame(up)

    # Suelta
    for _ in range(3):
        game._process_frame(down)

    # Vuelve a activar
    for _ in range(GesturesGame.MIN_FRAMES_TO_ACTIVATE):
        game._process_frame(up)

    snapshot = game._state.snapshot()
    assert snapshot["activation_counts"]["hand_up"] == 2
