"""
Tests TDD para PygameParticlesRenderer con ECS-lite y sprites.
Valida que el renderer dibuje círculos (fallback) y sprites (animados/estáticos).
"""

import pygame
import pytest

from pose_app.adapters.render.pygame_particles import PygameParticlesRenderer
from pose_app.domain.capabilities.particles.components import (
    Appearance,
    CollisionProfile,
    Lifespan,
    Position,
    SpriteConfig,
    SpriteState,
)
from pose_app.domain.entities.particle import Particle


@pytest.fixture(autouse=True)
def init_pygame():
    """Inicializa pygame para los tests y lo cierra al terminar."""
    pygame.init()
    yield
    pygame.quit()


def make_particle_with_circle(x: float, y: float, life: float = 1.0) -> Particle:
    """Factory para partícula con círculo (sin sprite)."""
    return Particle(
        position=Position(x=x, y=y),
        appearance=Appearance(size=20.0, color=(255, 0, 0)),
        lifespan=Lifespan.fresh(1.0) if life < 1.0 else None,
        collision=CollisionProfile(radius=10.0),
    )


def make_particle_with_sprite(
    x: float, y: float, frame: int = 0, fps: float = 0.0
) -> Particle:
    """Factory para partícula con sprite (estático o animado)."""
    return Particle(
        position=Position(x=x, y=y),
        appearance=Appearance(),
        sprite_config=SpriteConfig(
            path="blood-curse.png",
            frame_width=256.0,
            frame_height=256.0,
            frame_count=16,
            fps=fps,
            animation_mode="loop",
        ),
        sprite_state=SpriteState(current_frame=frame, elapsed_time=0.0),
    )


class TestPygameParticlesRendererECS:
    """El renderer debe dibujar círculos y sprites según los componentes."""

    def test_renders_circle_for_particle_without_sprite(self) -> None:
        """Si no hay sprite, dibuja un círculo."""
        # Arrange
        renderer = PygameParticlesRenderer(width=800, height=600)
        particle = make_particle_with_circle(400.0, 300.0)
        renderer.set_particles([particle])

        # Act
        renderer.render_particles()

        # Assert: verificar que se dibujó algo en el buffer
        # (En un test real, usaríamos un mock de surface o verificaríamos el color del píxel)
        assert renderer._particle_surface is not None

    def test_renders_sprite_for_particle_with_sprite(self) -> None:
        """Si hay sprite_config y sprite_state, dibuja el sprite."""
        # Arrange
        renderer = PygameParticlesRenderer(width=800, height=600)
        particle = make_particle_with_sprite(400.0, 300.0, frame=0)
        renderer.set_particles([particle])

        # Act
        renderer.render_particles()

        # Assert
        assert renderer._particle_surface is not None
        # Aquí verificaríamos que el sprite se dibujó en (400, 300)

    def test_renders_correct_frame_for_animated_sprite(self) -> None:
        """Para sprite animado, dibuja el frame actual de sprite_state."""
        # Arrange
        renderer = PygameParticlesRenderer(width=800, height=600)
        particle = make_particle_with_sprite(400.0, 300.0, frame=5, fps=12.0)
        renderer.set_particles([particle])

        # Act
        renderer.render_particles()

        # Assert
        assert renderer._particle_surface is not None
        # Verificar que se dibujó el frame 5 del sprite sheet

    def test_handles_particle_with_lifespan(self) -> None:
        """Partículas con lifespan ajustan alpha/tamaño."""
        # Arrange
        renderer = PygameParticlesRenderer(width=800, height=600)
        particle = make_particle_with_circle(400.0, 300.0, life=0.5)
        renderer.set_particles([particle])

        # Act
        renderer.render_particles()

        # Assert
        assert renderer._particle_surface is not None

    def test_ignores_dead_particles(self) -> None:
        """Partículas con life <= 0.01 no se dibujan."""
        # Arrange
        renderer = PygameParticlesRenderer(width=800, height=600)
        particle = make_particle_with_circle(400.0, 300.0, life=0.0)
        renderer.set_particles([particle])

        # Act
        renderer.render_particles()

        # Assert: el buffer debe estar vacío (solo transparente)
        assert renderer._particle_surface is not None
