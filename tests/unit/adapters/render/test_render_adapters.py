"""
Tests básicos de los adaptadores de render.

Nota: no verifican el render visual (eso requiere pygame.display),
solo que se pueden instanciar y que implementan correctamente.
"""

from pose_app.adapters.render.pygame_color_adapter import PygameColorAdapter
from pose_app.domain.entities.pose_landmark import PoseLandmark
from pose_app.domain.ports.render_port import ColorRenderPort


def test_pygame_color_adapter_implements_port():
    """Verifica que PygameColorAdapter cumpla ColorRenderPort."""
    adapter = PygameColorAdapter(width=320, height=240, title="Test")

    assert isinstance(adapter, ColorRenderPort)
    assert callable(adapter.render_background)
    assert callable(adapter.show)
    assert callable(adapter.close)


def test_pose_overlay_converts_normalized_to_pixels():
    """El overlay convierte coords normalizadas a píxeles."""
    from pose_app.adapters.render.overlays.pose_overlay import PoseOverlayRenderer

    lm = PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose")
    px, py = PoseOverlayRenderer._to_pixels(lm, width=800, height=600)

    assert px == 400
    assert py == 300
