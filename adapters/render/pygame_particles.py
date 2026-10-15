"""
Adaptador Pygame para capacidad de partículas.

Implementa ParticlesRenderPort con patrón set_* + render_*.
Reutiliza lógica de dibujo con alpha blending y manejo de resize.
"""

import pygame

from adapters.render.pygame_base import PygameBaseAdapter
from domain.entities.particle import Particle
from domain.ports.render.particles_render_port import ParticlesRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_particles")


class PygameParticlesRenderer(PygameBaseAdapter, ParticlesRenderPort):
    """Renderizador de partículas con patrón set_* + render_*."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Particles",
        target_fps: int = 60,
    ) -> None:
        PygameBaseAdapter.__init__(
            self,
            width=width,
            height=height,
            title=title,
            target_fps=target_fps,
        )

        self._particle_surface: pygame.Surface | None = None
        self._particles: list[Particle] = []

    def set_particles(self, particles: list[Particle]) -> None:
        """
        Declara las partículas a dibujar.

        Args:
            particles: Lista de partículas a renderizar en el próximo frame.
        """
        self._particles = list(particles)

    def render_particles(self) -> None:
        """Dibuja las partículas declaradas."""
        self._initialize()

        if not self.is_running:
            return

        # 1. Capa de partículas (con transparencia)
        surface = self._ensure_particle_surface()
        surface.fill((0, 0, 0, 0))

        self._draw_particles(self._particles)

        # 2. Mezcla sobre el fondo
        self.screen.blit(surface, (0, 0))

    def close(self) -> None:
        """Limpia el buffer y cierra Pygame."""
        self._particle_surface = None
        super().close()

    # ==========================================
    # Helpers privados
    # ==========================================

    def _ensure_particle_surface(self) -> pygame.Surface:
        """Crea o recrea el buffer de partículas si es necesario."""
        if self._particle_surface is None or self._particle_surface.get_size() != (
            self.width,
            self.height,
        ):
            self._particle_surface = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
        return self._particle_surface

    def _draw_particles(self, particles: list[Particle]) -> None:
        """Dibuja cada partícula en el buffer de partículas."""
        if self._particle_surface is None:
            return

        for particle in particles:
            if particle.life <= 0.01:
                continue

            size = int(particle.size * particle.life)
            if size < 1:
                continue

            alpha = int(200 * particle.life)

            color = (
                min(255, max(0, particle.color[0])),
                min(255, max(0, particle.color[1])),
                min(255, max(0, particle.color[2])),
                alpha,
            )

            x = int(particle.x)
            y = int(particle.y)

            if x < -size or x > self.width + size:
                continue
            if y < -size or y > self.height + size:
                continue

            pygame.draw.circle(self._particle_surface, color, (x, y), size)

    def _on_resize(self, new_size: tuple[int, int]) -> None:
        """Recrea el buffer de partículas al redimensionar."""
        super()._on_resize(new_size)
        self._particle_surface = None
