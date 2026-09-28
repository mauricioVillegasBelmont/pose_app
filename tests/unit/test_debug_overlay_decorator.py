# tests/unit/test_debug_overlay_decorator.py

from unittest.mock import Mock

from adapters.render.decorators.debug_overlay_decorator import (
    PygameDebugOverlayDecorator,
)
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark


def test_decorator_delegates_render_to_wrapped():
    """El decorador debe delegar el render al wrapped."""
    wrapped = Mock()
    wrapped.screen = Mock()  # Fake surface
    wrapped.width = 800
    wrapped.height = 600

    decorator = PygameDebugOverlayDecorator(wrapped)

    particles = [Particle(x=10, y=10)]
    decorator.render_particles(particles)

    # Verifica que delegó al wrapped
    wrapped.render_particles.assert_called_once_with(particles)


def test_decorator_draws_overlay_when_landmarks_present():
    """El decorador dibuja el overlay si hay landmarks."""
    wrapped = Mock()
    wrapped.screen = Mock()
    wrapped.width = 800
    wrapped.height = 600

    overlay = Mock()
    decorator = PygameDebugOverlayDecorator(wrapped, pose_overlay=overlay)

    landmarks = [PoseLandmark(0.5, 0.5, 0.0, 1.0, "nose")]
    decorator.update_landmarks(landmarks)
    decorator.render_particles([])

    # Verifica que dibujó el overlay
    overlay.draw.assert_called_once()
    call_args = overlay.draw.call_args
    assert call_args.kwargs["landmarks"] == landmarks
    assert call_args.kwargs["window_size"] == (800, 600)


def test_decorator_skips_overlay_when_no_landmarks():
    """El decorador no debe dibujar si no hay landmarks."""
    wrapped = Mock()
    wrapped.screen = Mock()
    wrapped.width = 800
    wrapped.height = 600

    overlay = Mock()
    decorator = PygameDebugOverlayDecorator(wrapped, pose_overlay=overlay)

    decorator.render_particles([])  # Sin update_landmarks previo

    overlay.draw.assert_not_called()