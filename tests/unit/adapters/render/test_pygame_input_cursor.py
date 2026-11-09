"""
Tests unitarios para PygameInputCursorRenderer.
Validan el renderizado de cursores (círculo y sprite).
"""

from collections.abc import Iterator
from unittest.mock import MagicMock, Mock, patch

import pygame
import pytest

from pose_app.adapters.render.pygame_input_cursor import PygameInputCursorRenderer
from pose_app.domain.entities.input_cursor import (
    CursorAppearance,
    InputCursor,
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


@pytest.fixture
def renderer(surface: pygame.Surface) -> Iterator[PygameInputCursorRenderer]:
    """Renderer con `_initialize` mockeado para no abrir ventana.

    - `_initialize` mockeado: no abre ventana (idempotente, no-op en tests).
    - `_running = True`: evita el early return de `render_cursors`.
    - No se mockea `_buffer` ni `_ensure_buffer`: el buffer SRCALPHA real
      funciona con `screen` real (ambas son `pygame.Surface`), y los tests
      spy patchean `_draw_*` (no el buffer).
    """
    r = PygameInputCursorRenderer(surface=surface)
    r._initialize = MagicMock()  # type: ignore[method-assign]
    r._running = True  # type: ignore[attr-defined]
    yield r


class TestPygameInputCursorRenderer:
    def test_set_cursors_stores_list(self, surface: pygame.Surface) -> None:
        """set_cursors debe almacenar la lista de cursores."""
        renderer = PygameInputCursorRenderer(surface=surface)
        cursors = [InputCursor(cursor_id="test")]

        renderer.set_cursors(cursors)

        assert renderer._cursors == cursors

    def test_render_cursors_skips_invisible(
        self, renderer: PygameInputCursorRenderer
    ) -> None:
        """render_cursors no debe dibujar cursores invisibles."""
        cursor = InputCursor(cursor_id="test")
        cursor.is_visible = False
        cursor.position = (0.5, 0.5)

        renderer.set_cursors([cursor])

        with (
            patch.object(renderer, "_draw_circle") as draw_circle,
            patch.object(renderer, "_draw_sprite") as draw_sprite,
        ):
            renderer.render_cursors()

        draw_circle.assert_not_called()
        draw_sprite.assert_not_called()

    def test_render_cursors_skips_cursor_without_position(
        self,
        renderer: PygameInputCursorRenderer,
    ) -> None:
        """Aunque sea visible, sin posición no debe dibujarse."""
        cursor = InputCursor(cursor_id="test")
        cursor.is_visible = True
        cursor.position = None

        renderer.set_cursors([cursor])

        with (
            patch.object(renderer, "_draw_circle") as draw_circle,
            patch.object(renderer, "_draw_sprite") as draw_sprite,
        ):
            renderer.render_cursors()

        draw_circle.assert_not_called()
        draw_sprite.assert_not_called()

    def test_render_cursors_draws_visible_cursor(
        self, renderer: PygameInputCursorRenderer
    ) -> None:
        """Un cursor visible con posición SÍ debe dibujarse."""
        cursor = InputCursor(cursor_id="test")
        cursor.is_visible = True
        cursor.position = (0.5, 0.5)

        renderer.set_cursors([cursor])

        with (
            patch.object(renderer, "_draw_circle") as draw_circle,
            patch.object(renderer, "_draw_sprite") as draw_sprite,
        ):
            renderer.render_cursors()

        draw_circle.assert_called_once()
        draw_sprite.assert_not_called()

    @patch("pose_app.adapters.render.pygame_input_cursor.pygame.draw.circle")
    def test_render_cursors_draws_circle(
        self, mock_circle: Mock, surface: pygame.Surface
    ) -> None:
        """render_cursors debe dibujar círculo para cursor sin sprite."""
        renderer = PygameInputCursorRenderer(surface=surface)
        renderer._initialize = MagicMock()  # type: ignore[method-assign]
        renderer._running = True  # type: ignore[attr-defined]

        cursor = InputCursor(
            cursor_id="test",
            appearance=CursorAppearance(size=40.0, color=(255, 255, 0)),
        )
        cursor.is_visible = True
        cursor.position = (0.5, 0.5)

        renderer.set_cursors([cursor])
        renderer.render_cursors()

        assert mock_circle.called

    def test_render_cursors_converts_coordinates(self) -> None:
        """get_position_pixels convierte coordenadas normalizadas a píxeles."""
        cursor = InputCursor(cursor_id="test")
        cursor.is_visible = True
        cursor.position = (0.25, 0.75)

        pos = cursor.get_position_pixels(800, 600)
        assert pos == (200.0, 450.0)

    def test_close_clears_cache(self, surface: pygame.Surface) -> None:
        """close debe limpiar el cache de sprites."""
        renderer = PygameInputCursorRenderer(surface=surface)
        renderer._sprite_cache["test.png"] = Mock()

        renderer.close()

        assert len(renderer._sprite_cache) == 0

    def test_multiple_cursors_rendered(
        self, renderer: PygameInputCursorRenderer
    ) -> None:
        """render_cursors debe renderizar solo los cursores visibles."""
        cursor1 = InputCursor(cursor_id="left")
        cursor1.is_visible = True
        cursor1.position = (0.3, 0.5)

        cursor2 = InputCursor(cursor_id="right")
        cursor2.is_visible = True
        cursor2.position = (0.7, 0.5)

        cursor3 = InputCursor(cursor_id="hidden")
        cursor3.is_visible = False
        cursor3.position = (0.5, 0.5)

        renderer.set_cursors([cursor1, cursor2, cursor3])

        with (
            patch.object(renderer, "_draw_circle") as draw_circle,
            patch.object(renderer, "_draw_sprite") as draw_sprite,
        ):
            renderer.render_cursors()

        assert draw_circle.call_count == 2
        draw_sprite.assert_not_called()
        assert len(renderer._cursors) == 3
