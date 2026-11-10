"""
Tests unitarios de los adaptadores mock de render.
Verifican:
- Que cumplan con los puertos correctos.
- Que registren el estado (spy).
- Que los contadores incrementen.
- Que close() sea idempotente.
"""

from unittest.mock import Mock

from pose_app.adapters.mock.mock_render import (
    MockColorRenderAdapter,
    MockParticlesRenderAdapter,
    MockSceneManager,
)
from pose_app.domain.entities.color import RGBColor
from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.components import Appearance, Position
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.domain.ports.render.particles_render_port import ParticlesRenderPort
from pose_app.domain.ports.render.scene_port import ScenePort

# ==========================================
# MockParticlesRenderAdapter
# ==========================================


def test_mock_particles_implements_port() -> None:
    """Verifica que implemente ParticlesRenderPort."""
    adapter = MockParticlesRenderAdapter()
    assert isinstance(adapter, ParticlesRenderPort)


def test_mock_particles_records_last_particles() -> None:
    """Verifica que registre las últimas partículas."""
    adapter = MockParticlesRenderAdapter()
    particles = [
        Particle(position=Position(x=10.0, y=20.0), appearance=Appearance()),
        Particle(position=Position(x=30.0, y=40.0), appearance=Appearance()),
    ]
    adapter.set_particles(particles)
    adapter.render_particles()
    assert len(adapter.last_particles) == 2
    assert adapter.last_particles[0].position.x == 10.0
    assert adapter.render_count == 1


def test_mock_particles_render_is_unified_entrypoint() -> None:
    """render() delega en render_particles()."""
    adapter = MockParticlesRenderAdapter()
    adapter.set_particles([])
    adapter.render()
    assert adapter.render_count == 1


def test_mock_particles_makes_defensive_copy() -> None:
    """Verifica que el mock haga copia defensiva de las partículas."""
    adapter = MockParticlesRenderAdapter()
    particles = [Particle(position=Position(x=10.0, y=20.0), appearance=Appearance())]
    adapter.set_particles(particles)
    # Modificar la lista original NO debe afectar al mock
    particles.append(
        Particle(position=Position(x=99.0, y=99.0), appearance=Appearance())
    )
    adapter.render_particles()
    assert len(adapter.last_particles) == 1  # Sigue teniendo 1


def test_mock_particles_close_is_idempotent() -> None:
    """Verifica que close() sea idempotente."""
    adapter = MockParticlesRenderAdapter()
    adapter.close()
    adapter.close()
    adapter.close()
    assert adapter.is_closed is True
    assert adapter.close_count == 3  # Cuenta las llamadas


def test_mock_particles_reset() -> None:
    """Verifica que reset() limpie el estado."""
    adapter = MockParticlesRenderAdapter()
    adapter.set_particles(
        [Particle(position=Position(x=1.0, y=1.0), appearance=Appearance())]
    )
    adapter.render_particles()
    adapter.close()
    adapter.reset()
    assert adapter.last_particles == []
    assert adapter.render_count == 0
    assert adapter.close_count == 0
    assert adapter.is_closed is False


# ==========================================
# MockColorRenderAdapter
# ==========================================


def test_mock_color_implements_port() -> None:
    """Verifica que implemente ColorRenderPort."""
    adapter = MockColorRenderAdapter()
    assert isinstance(adapter, ColorRenderPort)


def test_mock_color_records_last_color() -> None:
    """Verifica que registre el color declarado."""
    adapter = MockColorRenderAdapter()
    color = RGBColor(255, 128, 0)
    adapter.set_color(color)
    assert adapter.last_color == color


def test_mock_color_render_increments_count() -> None:
    """Verifica que render_color() incremente el contador."""
    adapter = MockColorRenderAdapter()
    adapter.set_color(RGBColor(255, 0, 0))
    adapter.render_color()
    assert adapter.render_count == 1


def test_mock_color_render_is_unified_entrypoint() -> None:
    """render() delega en render_color()."""
    adapter = MockColorRenderAdapter()
    adapter.set_color(RGBColor(255, 0, 0))
    adapter.render()
    assert adapter.render_count == 1


def test_mock_color_close_is_idempotent() -> None:
    """Verifica que close() sea idempotente."""
    adapter = MockColorRenderAdapter()
    adapter.close()
    adapter.close()
    assert adapter.is_closed is True
    assert adapter.close_count == 2


def test_mock_color_reset() -> None:
    """Verifica que reset() limpie el estado."""
    adapter = MockColorRenderAdapter()
    adapter.set_color(RGBColor(255, 0, 0))
    adapter.render_color()
    adapter.close()
    adapter.reset()
    assert adapter.last_color is None
    assert adapter.render_count == 0
    assert adapter.close_count == 0
    assert adapter.is_closed is False


# ==========================================
# MockSceneManager
# ==========================================


def test_mock_scene_implements_port() -> None:
    """Verifica que implemente ScenePort."""
    scene = MockSceneManager()
    assert isinstance(scene, ScenePort)


def test_mock_scene_renders_capabilities_and_overlays() -> None:
    """render_frame() ejecuta capacidades y overlays."""
    capability = Mock(spec=ColorRenderPort)
    overlay = Mock()
    scene = MockSceneManager(capabilities=[capability], overlays=[overlay])
    landmarks = [
        PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose"),
    ]

    scene.render_frame(landmarks)

    capability.render.assert_called_once()
    overlay.draw.assert_called_once_with(None, landmarks)
    assert scene.render_count == 1


def test_mock_scene_close_is_idempotent() -> None:
    """close() cierra capacidades/overlays una sola vez."""
    capability = Mock()
    overlay = Mock()
    scene = MockSceneManager(capabilities=[capability], overlays=[overlay])

    scene.close()
    scene.close()

    capability.close.assert_called_once()
    overlay.close.assert_called_once()
    assert scene.is_closed is True
