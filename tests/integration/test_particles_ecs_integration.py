"""
Test de integración: simula un frame completo con sprite animado.
"""

import pygame

from pose_app.adapters.render.pygame_particles import PygameParticlesRenderer
from pose_app.domain.capabilities.particles.components import (
    Appearance,
    CollisionProfile,
    Position,
    SpriteConfig,
    SpriteState,
)
from pose_app.domain.capabilities.particles.systems import AnimationSystem
from pose_app.domain.entities.particle import Particle


def test_frame_with_animated_sprite() -> None:
    """Simula un frame: animar -> renderizar."""
    pygame.init()

    # 1. Crear partícula con sprite
    sprite_config = SpriteConfig(
        path="blood-curse.png",
        frame_width=256.0,
        frame_height=256.0,
        frame_count=16,
        fps=12.0,
        animation_mode="loop",
    )
    particle = Particle(
        position=Position(x=400.0, y=300.0),
        appearance=Appearance(),
        collision=CollisionProfile(radius=128.0),
        sprite_config=sprite_config,
        sprite_state=SpriteState(current_frame=0, elapsed_time=0.0),
    )

    # 2. Animar
    animation_system = AnimationSystem()
    animation_system.update([particle], dt=0.1)  # 0.1s > 1/12s → avanza frame

    assert particle.sprite_state.current_frame == 1  # Debería avanzar

    # 3. Renderizar
    renderer = PygameParticlesRenderer(width=800, height=600)
    renderer.set_particles([particle])
    renderer.render_particles()

    # 4. Verificar que se dibujó algo (básico)
    assert renderer._particle_surface is not None

    pygame.quit()
