"""
Adaptador Pygame para capacidad de partículas (ECS-lite + sprites).
Implementa ParticlesRenderPort con patrón set_* + render_*.
Soporta círculos (fallback) y sprites animados/estáticos.
"""

from pathlib import Path

import pygame

from pose_app.adapters.render.pygame_base import PygameBaseAdapter
from pose_app.domain.capabilities.particles.components import (
    SpriteConfig,
)
from pose_app.domain.entities.particle import Particle
from pose_app.domain.ports.render.particles_render_port import ParticlesRenderPort
from pose_app.infrastructure.assets.sprite_sheet_parser import SpriteSheetParser
from pose_app.infrastructure.logging.logger import get_logger
from pose_app.infrastructure.paths import ASSETS_DIR

logger = get_logger("adapters.render.pygame_particles")


class PygameParticlesRenderer(PygameBaseAdapter, ParticlesRenderPort):
    """Renderizador de partículas con ECS-lite y soporte de sprites."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Particles",
        target_fps: int = 60,
        mirror: bool = False,
        assets_dir: Path | None = None,
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
        self._mirror = mirror
        self._assets_dir = assets_dir or ASSETS_DIR
        self._sprite_cache: dict[str, dict] = {}  # Cache de sprites cargados
        self._parser = SpriteSheetParser()

    def set_particles(self, particles: list[Particle]) -> None:
        """Declara las partículas a dibujar."""
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
        self._sprite_cache.clear()
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

    def _load_sprite(self, config: SpriteConfig) -> dict:
        """
        Carga un sprite sheet y parsea sus frames.
        Retorna un dict con 'image' (pygame.Surface) y 'frames' (dict[int, tuple]).
        """
        if config.path in self._sprite_cache:
            return self._sprite_cache[config.path]

        # Ruta del archivo
        sprite_path = self._assets_dir / "particles" / "sprites" / config.path
        if not sprite_path.exists():
            logger.warning(f"Sprite no encontrado: {sprite_path}")
            return {"image": None, "frames": {}}

        # Cargar imagen
        try:
            image = pygame.image.load(str(sprite_path)).convert_alpha()
        except pygame.error as e:
            logger.error(f"Error cargando sprite {config.path}: {e}")
            return {"image": None, "frames": {}}

        # Parsear JSON (si existe)
        json_path = sprite_path.with_suffix(".json")
        frames = {}
        if json_path.exists():
            import json

            with open(json_path, "r") as f:
                data = json.load(f)
            frames = self._parser.parse(data)

        cache_entry = {"image": image, "frames": frames}
        self._sprite_cache[config.path] = cache_entry
        return cache_entry

    def _draw_particles(self, particles: list[Particle]) -> None:
        """Dibuja cada partícula en el buffer de partículas."""
        if self._particle_surface is None:
            return

        for particle in particles:
            # BLINDAJE: Solo dibujar sprite si AMBOS componentes existen explícitamente
            if particle.sprite_config is not None and particle.sprite_state is not None:
                self._draw_sprite(particle)
            # FALLBACK: Si no hay sprite, pero sí apariencia, dibujar círculo
            elif particle.appearance is not None:
                self._draw_circle(particle)

    def _draw_circle(self, particle: Particle) -> None:
        """Dibuja una partícula como círculo (fallback)."""

        if self._particle_surface is None:
            return

        if particle.appearance.size <= 0:
            return  # No renderizar si el tamaño base es 0

        # Calcular alpha basado en lifespan
        alpha = 255
        if particle.lifespan is not None:
            life_ratio = particle.lifespan.current_life / particle.lifespan.max_life
            alpha = int(255 * life_ratio)

        # ==========================================
        # CÁLCULO DE TAMAÑO VISUAL (incluye padding)
        # ==========================================
        visual_size = (
            particle.appearance.size
            + particle.appearance.padding_x
            + particle.appearance.padding_y
        )
        radius = int(visual_size / 2)

        if radius < 1:
            return
        color = (
            min(255, max(0, particle.appearance.color[0])),
            min(255, max(0, particle.appearance.color[1])),
            min(255, max(0, particle.appearance.color[2])),
            alpha,
        )

        x = int(particle.position.x)
        y = int(particle.position.y)

        if self._mirror:
            x = self.width - x

        # Culling (no dibujar si está fuera de pantalla)
        if (
            x < -radius
            or x > self.width + radius
            or y < -radius
            or y > self.height + radius
        ):
            return

        pygame.draw.circle(self._particle_surface, color, (x, y), radius)

    def _draw_sprite(self, particle: Particle) -> None:
        """Dibuja una partícula como sprite (estático o animado)."""

        if self._particle_surface is None:
            return

        config = particle.sprite_config
        state = particle.sprite_state

        if config is None or state is None:
            return

        # ==========================================
        # VALIDACIÓN SEMÁNTICA: size debe ser > 0
        # ==========================================
        if particle.appearance.size <= 0:
            return  # No renderizar si el tamaño base es 0

        # BLINDAJE EXTRA
        if config is None or state is None:
            return

        cache = self._load_sprite(config)
        if cache["image"] is None:
            return

        image = cache["image"]
        frames = cache["frames"]

        # Obtener coordenadas del frame actual
        frame_coords = frames.get(state.current_frame)
        if frame_coords is None:
            frame_coords = (0, 0, int(config.frame_width), int(config.frame_height))

        fx, fy, fw, fh = frame_coords

        # Crear subsurface del frame
        try:
            frame_surface = image.subsurface((fx, fy, fw, fh))
        except ValueError:
            logger.warning(
                f"Frame {state.current_frame} fuera de rango en {config.path}"
            )
            return

        # ==========================================
        # ESCALADO VISUAL (tamaño base + padding)
        # ==========================================
        target_width = int(particle.appearance.size + particle.appearance.padding_x)
        target_height = int(particle.appearance.size + particle.appearance.padding_y)

        if target_width < 1 or target_height < 1:
            return

        if fw != target_width or fh != target_height:
            frame_surface = pygame.transform.scale(
                frame_surface, (target_width, target_height)
            )

        # ==========================================
        # POSICIÓN: Centrar en las coordenadas de la partícula
        # ==========================================
        x = int(particle.position.x - target_width / 2)
        y = int(particle.position.y - target_height / 2)

        if self._mirror:
            x = self.width - x - target_width

        # Alpha basado en lifespan
        if particle.lifespan is not None:
            life_ratio = particle.lifespan.current_life / particle.lifespan.max_life
            frame_surface.set_alpha(int(255 * life_ratio))

        # Dibujar
        self._particle_surface.blit(frame_surface, (x, y))

    def _on_resize(self, new_size: tuple[int, int]) -> None:
        """Recrea el buffer de partículas al redimensionar."""
        super()._on_resize(new_size)
        self._particle_surface = None
