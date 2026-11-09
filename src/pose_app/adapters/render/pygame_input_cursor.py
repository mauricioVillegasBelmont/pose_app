"""
Adaptador Pygame para renderizar cursores de interacción.

Implementa InputCursorRenderPort usando Pygame. Soporta:
- Cursores circulares con borde y relleno translúcido
- Cursores con sprite animado
- Cache de sprites para evitar recargas
"""

from __future__ import annotations

import pygame

from pose_app.adapters.render.pygame_base import PygameBaseAdapter
from pose_app.domain.entities.input_cursor import InputCursor
from pose_app.domain.ports.render.input_cursor_render_port import InputCursorRenderPort


class PygameInputCursorRenderer(PygameBaseAdapter, InputCursorRenderPort):
    """
    Renderer Pygame para cursores de interacción.

    Dibuja cursores como círculos o sprites animados según la configuración
    del cursor. Los sprites se cachean para evitar recargas en cada frame.
    """

    def __init__(
        self,
        surface: pygame.Surface,
        target_fps: int = 60,
        title: str = "cursors",
        mirror: bool = False,
    ) -> None:
        """
        Inicializa el renderer.

        Args:
            surface: Superficie de Pygame donde dibujar (inyectada por el
                bootstrap del plugin).
            target_fps: FPS objetivo.
            title: Nombre legible para logs.
            mirror: Si se debe espejar el cursor.
        """
        PygameBaseAdapter.__init__(
            self,
            surface=surface,
            target_fps=target_fps,
            title=title,
        )
        self._buffer: pygame.Surface | None = None
        self._cursors: list[InputCursor] = []
        self._sprite_cache: dict[str, pygame.Surface] = {}
        self._mirror = mirror

    def set_cursors(self, cursors: list[InputCursor]) -> None:
        """Declara los cursores a renderizar."""
        self._cursors = cursors

    def render_cursors(self) -> None:
        """Renderiza los cursores visibles declarados."""
        self._initialize()
        if not self.is_running:
            return

        buffer = self._ensure_buffer()
        buffer.fill((0, 0, 0, 0))

        for cursor in self._cursors:
            if not cursor.is_visible or cursor.position is None:
                continue

            pos_pixels = cursor.get_position_pixels(self.width, self.height)
            if pos_pixels is None:
                continue

            x, y = pos_pixels

            if self._mirror:
                x = self.width - x

            if cursor.sprite_config is not None and cursor.sprite_state is not None:
                self._draw_sprite(cursor, x, y)
            else:
                self._draw_circle(cursor, x, y)

        self.screen.blit(buffer, (0, 0))

    def render(self) -> None:
        """Método unificado de RenderCapability.
        Delega al método específico del puerto.
        """
        self.render_cursors()

    def close(self) -> None:
        """Limpia recursos del renderer. NO cierra pygame (lo hace el SceneManager)."""
        self._sprite_cache.clear()
        self._buffer = None
        super().close()

    # ==========================================
    # Helpers privados
    # ==========================================

    def _ensure_buffer(self) -> pygame.Surface:
        """Crea o recrea el buffer interno SRCALPHA si es necesario."""
        if self._buffer is None or self._buffer.get_size() != (
            self.width,
            self.height,
        ):
            self._buffer = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
        return self._buffer

    def _draw_circle(self, cursor: InputCursor, x: float, y: float) -> None:
        """Dibuja el cursor como un círculo con borde y relleno translúcido."""
        if self._buffer is None:
            return

        appearance = cursor.appearance
        visual_size = appearance.size + appearance.padding_x + appearance.padding_y
        radius = int(visual_size / 2)

        if radius <= 0:
            return

        pygame.draw.circle(
            self._buffer,
            appearance.color,
            (int(x), int(y)),
            radius,
            width=3,
        )

        inner_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            inner_surface,
            (*appearance.color, 80),
            (radius, radius),
            radius,
        )
        self._buffer.blit(inner_surface, (int(x - radius), int(y - radius)))

    def _draw_sprite(self, cursor: InputCursor, x: float, y: float) -> None:
        """Dibuja el cursor como un sprite animado."""
        if self._buffer is None:
            return

        if cursor.sprite_config is None or cursor.sprite_state is None:
            return

        config = cursor.sprite_config
        state = cursor.sprite_state

        cache_key = config.path
        if cache_key not in self._sprite_cache:
            try:
                self._sprite_cache[cache_key] = pygame.image.load(
                    config.path
                ).convert_alpha()
            except pygame.error:
                self._draw_circle(cursor, x, y)
                return

        sprite_sheet = self._sprite_cache[cache_key]

        frame_index = state.current_frame % config.frame_count
        cols = int(sprite_sheet.get_width() / config.frame_width)
        frame_x = (frame_index % cols) * config.frame_width
        frame_y = (frame_index // cols) * config.frame_height

        frame_rect = pygame.Rect(
            int(frame_x),
            int(frame_y),
            int(config.frame_width),
            int(config.frame_height),
        )
        frame_surface = sprite_sheet.subsurface(frame_rect)

        appearance = cursor.appearance
        target_width = int(appearance.size + appearance.padding_x)
        target_height = int(appearance.size + appearance.padding_y)

        if target_width > 0 and target_height > 0:
            frame_surface = pygame.transform.scale(
                frame_surface, (target_width, target_height)
            )

            blit_x = int(x - target_width / 2)
            blit_y = int(y - target_height / 2)
            self._buffer.blit(frame_surface, (blit_x, blit_y))
