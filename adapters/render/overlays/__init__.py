"""
Paquete de overlays para render Pygame.
"""

from adapters.render.overlays.fps_overlay import FpsOverlay
from adapters.render.overlays.pose_overlay import PoseOverlay, PoseOverlayRenderer

__all__ = [
    "FpsOverlay",
    "PoseOverlay",
    "PoseOverlayRenderer",
]
