"""
Tests del GesturesState.
"""

from pose_app.domain.entities.gesture import Gesture
from pose_app.domain.games.gestures.state import GesturesState


def test_initial_state():
    state = GesturesState()
    snapshot = state.snapshot()

    assert snapshot["active_gestures"] == []
    assert snapshot["frame_count"] == 0
    assert all(count == 0 for count in snapshot["activation_counts"].values())


def test_update_active_gestures():
    state = GesturesState()

    state.update_active_gestures(
        newly_activated={Gesture.HAND_UP},
        currently_active={Gesture.HAND_UP},
    )

    snapshot = state.snapshot()
    assert "hand_up" in snapshot["active_gestures"]
    assert snapshot["activation_counts"]["hand_up"] == 1


def test_multiple_activations():
    state = GesturesState()

    state.update_active_gestures(
        newly_activated={Gesture.HAND_UP},
        currently_active={Gesture.HAND_UP},
    )
    state.update_active_gestures(
        newly_activated={Gesture.GREETING},
        currently_active={Gesture.HAND_UP, Gesture.GREETING},
    )

    snapshot = state.snapshot()
    assert sorted(snapshot["active_gestures"]) == ["greeting", "hand_up"]
    assert snapshot["activation_counts"]["hand_up"] == 1
    assert snapshot["activation_counts"]["greeting"] == 1


def test_stats():
    state = GesturesState()
    state.update_active_gestures(
        newly_activated={Gesture.HAND_UP},
        currently_active={Gesture.HAND_UP},
    )
    state.increment_frames()

    stats = state.stats()
    assert stats["active_count"] == 1
    assert stats["total_activations"] == 1
    assert stats["frames_processed"] == 1


def test_game_id():
    state = GesturesState()
    assert state.game_id == "gestures"
