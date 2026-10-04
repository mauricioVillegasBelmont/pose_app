"""
Tests del decorador PoseDebugOverlay con mocks.

Nota: solo verificamos la delegación; el render visual
se prueba en tests/integration con Pygame real.
"""

from unittest.mock import Mock

from adapters.render.decorators.pose_debug_overlay import PoseDebugOverlay
from domain.entities.particle import Particle
from domain.entities.pose_landmark import PoseLandmark


def test_decorator_delegates_render_to_wrapped():
    wrapped = Mock()
    wrapped.screen = Mock()
    wrapped.width = 800
    wrapped.height = 600

    decorator = PoseDebugOverlay(wrapped)

    particles = [Particle(x=10, y=10)]
    decorator.render_particles(particles)

    wrapped.render_particles.assert_called_once_with(particles)


def test_decorator_draws_overlay_when_landmarks_present():
    wrapped = Mock()
    wrapped.screen = Mock()
    wrapped.width = 800
    wrapped.height = 600

    overlay = Mock()
    decorator = PoseDebugOverlay(wrapped, pose_overlay=overlay)

    landmarks = [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose")]
    decorator.update_landmarks(landmarks)
    decorator.render_particles([])

    overlay.draw.assert_called_once()
