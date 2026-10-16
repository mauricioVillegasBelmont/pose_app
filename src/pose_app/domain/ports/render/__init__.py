"""
Paquete de puertos de render (nueva arquitectura).

Define capacidades componibles (color, particles, hud) y elementos
de composición (overlay, scene). Los puertos aquí definidos siguen
el patrón set_* + render_* y son compatibles con SceneManager.
"""

from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.domain.ports.render.hud_render_port import HudRenderPort
from pose_app.domain.ports.render.overlay_port import OverlayPort
from pose_app.domain.ports.render.particles_render_port import ParticlesRenderPort
from pose_app.domain.ports.render.scene_port import ScenePort

__all__ = [
    "ColorRenderPort",
    "HudRenderPort",
    "OverlayPort",
    "ParticlesRenderPort",
    "ScenePort",
]
