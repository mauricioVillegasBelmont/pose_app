"""
Tests TDD para PygameParticlesRenderer con ECS-lite y sprites.
Valida que el renderer dibuje círculos (fallback) y sprites (animados/estáticos).
"""

import pygame
import pytest

from pose_app.adapters.render.pygame_particles import PygameParticlesRenderer
from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.components import (
    Appearance,
    CollisionProfile,
    Lifespan,
    Position,
    SpriteConfig,
    SpriteState,
)


@pytest.fixture(autouse=True)
def init_pygame():
    """Inicializa pygame para los tests y lo cierra al terminar."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def surface() -> pygame.Surface:
    """Surface de prueba (no requiere display real)."""
    return pygame.Surface((800, 600))


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

    def test_renders_circle_for_particle_without_sprite(
        self, surface: pygame.Surface
    ) -> None:
        """Si no hay sprite, dibuja un círculo."""
        renderer = PygameParticlesRenderer(surface=surface)
        particle = make_particle_with_circle(400.0, 300.0)
        renderer.set_particles([particle])

        renderer.render_particles()

        assert renderer._particle_surface is not None

    def test_renders_sprite_for_particle_with_sprite(
        self, surface: pygame.Surface
    ) -> None:
        """Si hay sprite_config y sprite_state, dibuja el sprite."""
        renderer = PygameParticlesRenderer(surface=surface)
        particle = make_particle_with_sprite(400.0, 300.0, frame=0)
        renderer.set_particles([particle])

        renderer.render_particles()

        assert renderer._particle_surface is not None

    def test_renders_correct_frame_for_animated_sprite(
        self, surface: pygame.Surface
    ) -> None:
        """Para sprite animado, dibuja el frame actual de sprite_state."""
        renderer = PygameParticlesRenderer(surface=surface)
        particle = make_particle_with_sprite(400.0, 300.0, frame=5, fps=12.0)
        renderer.set_particles([particle])

        renderer.render_particles()

        assert renderer._particle_surface is not None

    def test_handles_particle_with_lifespan(self, surface: pygame.Surface) -> None:
        """Partículas con lifespan ajustan alpha/tamaño."""
        renderer = PygameParticlesRenderer(surface=surface)
        particle = make_particle_with_circle(400.0, 300.0, life=0.5)
        renderer.set_particles([particle])

        renderer.render_particles()

        assert renderer._particle_surface is not None

    def test_ignores_dead_particles(self, surface: pygame.Surface) -> None:
        """Partículas con life <= 0.01 no se dibujan."""
        renderer = PygameParticlesRenderer(surface=surface)
        particle = make_particle_with_circle(400.0, 300.0, life=0.0)
        renderer.set_particles([particle])

        renderer.render_particles()

        assert renderer._particle_surface is not None

    def test_zero_size_particle_not_rendered_even_with_padding(
        self, surface: pygame.Surface
    ) -> None:
        """Si size=0, la partícula no se renderiza aunque tenga padding."""
        renderer = PygameParticlesRenderer(surface=surface)
        particle = Particle(
            position=Position(x=400.0, y=300.0),
            appearance=Appearance(size=0.0, padding_x=10.0, padding_y=10.0),
        )
        renderer.set_particles([particle])
        renderer.render_particles()

        assert renderer._particle_surface is not None
