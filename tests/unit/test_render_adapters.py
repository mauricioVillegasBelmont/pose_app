"""
Tests básicos de los adaptadores de render.

Nota: no verifican el render visual (eso requiere pygame.display),
solo que se pueden instanciar y que implementan correctamente.
"""

from adapters.render.pygame_color_adapter import PygameColorAdapter
from adapters.render.pygame_particles_adapter import PygameParticlesAdapter
from domain.entities.pose_landmark import PoseLandmark
from domain.ports.render_port import ColorRenderPort, ParticlesRenderPort


def test_pygame_particles_adapter_implements_port():
    """Verifica que PygameParticlesAdapter cumpla ParticlesRenderPort."""
    adapter = PygameParticlesAdapter(width=320, height=240, title="Test")

    assert isinstance(adapter, ParticlesRenderPort)
    assert callable(adapter.render_particles)
    assert callable(adapter.show)
    assert callable(adapter.close)

    # NO llamamos a close() aquí porque inicializaría Pygame


def test_pygame_color_adapter_implements_port():
    """Verifica que PygameColorAdapter cumpla ColorRenderPort."""
    adapter = PygameColorAdapter(width=320, height=240, title="Test")

    assert isinstance(adapter, ColorRenderPort)
    assert callable(adapter.render_background)
    assert callable(adapter.show)
    assert callable(adapter.close)


def test_pygame_color_adapter_converts_normalized_to_pixels():
    """Verifica la conversión de coordenadas normalizadas a píxeles."""
    adapter = PygameColorAdapter(width=800, height=600)

    lm = PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose")
    px, py = adapter._to_pixels(lm)

    assert px == 400
    assert py == 300

    lm_corner = PoseLandmark(x=0.0, y=1.0, z=0.0, visibility=1.0, name="left_ankle")
    px, py = adapter._to_pixels(lm_corner)

    assert px == 0
    assert py == 600