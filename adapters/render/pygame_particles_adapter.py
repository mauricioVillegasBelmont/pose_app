import pygame

from adapters.render.pygame_base import PygameBaseAdapter
from domain.entities.color import RGBColor
from domain.entities.particle import Particle
from domain.ports.render_port import ParticlesRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("adapters.render.pygame_particles")


class PygameParticlesAdapter(PygameBaseAdapter, ParticlesRenderPort):
    """
    Adaptador Pygame que renderiza un sistema de partículas.

    Características:
    - Alpha blending para efecto de brillo.
    - Tamaño de partícula proporcional a su vida.
    - Fondo sólido configurable.

    NOTA: No incluye overlay de pose. Si se necesita debug,
    usar el decorador `PoseDebugOverlay`.
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Particles",
        target_fps: int = 60,
        background_color: RGBColor = RGBColor(20, 20, 30),
    ):
        PygameBaseAdapter.__init__(
            self,
            width=width,
            height=height,
            title=title,
            target_fps=target_fps,
        )
        self._background_color = background_color
        self._particle_surface: pygame.Surface | None = None

    def render_particles(self, particles: list[Particle]) -> None:
        """Renderiza las partículas con alpha blending."""
        self._initialize()

        if not self.is_running:
            return

        # 1. Fondo
        self.screen.fill(self._background_color.to_rgb_tuple())

        # 2. Capa de partículas (con transparencia)
        self._ensure_particle_surface()
        self._particle_surface.fill((0, 0, 0, 0))

        self._draw_particles(particles)

        # 3. Mezcla sobre el fondo
        self.screen.blit(self._particle_surface, (0, 0))

        # 4. Actualiza pantalla + FPS
        self.flush()

        # 5. Eventos
        self._handle_events()

    def close(self) -> None:
        """Limpia el buffer y cierra Pygame."""
        self._particle_surface = None
        super().close()

    # ==========================================
    # Helpers privados
    # ==========================================

    def _ensure_particle_surface(self) -> None:
        """Crea o recrea el buffer de partículas si es necesario."""
        if (
            self._particle_surface is None
            or self._particle_surface.get_size() != (self.width, self.height)
        ):
            self._particle_surface = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )

    def _draw_particles(self, particles: list[Particle]) -> None:
        """Dibuja cada partícula en el buffer de partículas."""
        assert self._particle_surface is not None

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