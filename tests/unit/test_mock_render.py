"""
Tests unitarios de los adaptadores mock de render.

Verifican:
1. Que cumplan con los puertos correctos.
2. Que registren el estado (spy).
3. Que los contadores incrementen.
4. Que close() sea idempotente.
"""

from pose_app.adapters.mock.mock_render import (
    MockColorRenderAdapter,
    MockParticlesRenderAdapter,
)
from pose_app.domain.entities.color import RGBColor
from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render_port import (
    ColorRenderPort,
    LandmarkAwareRenderPort,
    ParticlesRenderPort,
)

# ==========================================
# MockParticlesRenderAdapter
# ==========================================


def test_mock_particles_implements_ports():
    """Verifica que implemente los puertos correctos."""
    adapter = MockParticlesRenderAdapter()

    assert isinstance(adapter, ParticlesRenderPort)
    assert isinstance(adapter, LandmarkAwareRenderPort)


def test_mock_particles_records_last_particles():
    """Verifica que registre las últimas partículas."""
    adapter = MockParticlesRenderAdapter()

    particles = [
        Particle(x=10.0, y=20.0),
        Particle(x=30.0, y=40.0),
    ]
    adapter.render_particles(particles)

    assert len(adapter.last_particles) == 2
    assert adapter.last_particles[0].x == 10.0
    assert adapter.render_count == 1


def test_mock_particles_records_landmarks():
    """Verifica que registre landmarks (LandmarkAwareRenderPort)."""
    adapter = MockParticlesRenderAdapter()

    landmarks = [
        PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose"),
    ]
    adapter.update_landmarks(landmarks)

    assert len(adapter.last_landmarks) == 1
    assert adapter.last_landmarks[0].name == "nose"
    assert adapter.update_landmarks_count == 1


def test_mock_particles_makes_defensive_copy():
    """Verifica que el mock haga copia defensiva de las partículas."""
    adapter = MockParticlesRenderAdapter()

    particles = [Particle(x=10.0, y=20.0)]
    adapter.render_particles(particles)

    # Modificar la lista original NO debe afectar al mock
    particles.append(Particle(x=99.0, y=99.0))

    assert len(adapter.last_particles) == 1  # Sigue teniendo 1


def test_mock_particles_close_is_idempotent():
    """Verifica que close() sea idempotente."""
    adapter = MockParticlesRenderAdapter()

    adapter.close()
    adapter.close()
    adapter.close()

    assert adapter.is_closed is True
    assert adapter.close_count == 3  # Cuenta las llamadas


def test_mock_particles_reset():
    """Verifica que reset() limpie el estado."""
    adapter = MockParticlesRenderAdapter()

    adapter.render_particles([Particle(x=1.0, y=1.0)])
    adapter.update_landmarks([])
    adapter.show()
    adapter.close()

    adapter.reset()

    assert adapter.last_particles == []
    assert adapter.last_landmarks == []
    assert adapter.render_count == 0
    assert adapter.update_landmarks_count == 0
    assert adapter.show_count == 0
    assert adapter.close_count == 0
    assert adapter.is_closed is False


# ==========================================
# MockColorRenderAdapter
# ==========================================


def test_mock_color_implements_ports():
    """Verifica que implemente los puertos correctos."""
    adapter = MockColorRenderAdapter()

    assert isinstance(adapter, ColorRenderPort)
    assert isinstance(adapter, LandmarkAwareRenderPort)


def test_mock_color_records_last_color_and_landmarks():
    """Verifica que registre color y landmarks."""
    adapter = MockColorRenderAdapter()

    color = RGBColor(255, 128, 0)
    landmarks = [
        PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose"),
    ]

    adapter.render_background(color, landmarks)

    assert adapter.last_color == color
    assert len(adapter.last_landmarks) == 1
    assert adapter.render_count == 1


def test_mock_color_reset():
    """Verifica que reset() limpie el estado."""
    adapter = MockColorRenderAdapter()

    adapter.render_background(RGBColor(255, 0, 0), [])
    adapter.reset()

    assert adapter.last_color is None
    assert adapter.last_landmarks == []
    assert adapter.render_count == 0
