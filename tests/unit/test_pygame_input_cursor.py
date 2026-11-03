"""
Tests unitarios para PygameInputCursorRenderer.
Validan el renderizado de cursores (círculo y sprite).
"""

from collections.abc import Iterator
from unittest.mock import MagicMock, Mock, patch

import pytest

from pose_app.adapters.render.pygame_input_cursor import PygameInputCursorRenderer
from pose_app.domain.entities.input_cursor import (
    CursorAppearance,
    InputCursor,
)


@pytest.fixture
def renderer() -> Iterator[PygameInputCursorRenderer]:
    """Renderer con dependencias pygame mockeadas.

    - `_initialize` mockeado: no abre ventana.
    - `_running = True`: `is_running` (property que lee `_running`) devuelve True,
      evitando el early return de `render_cursors`.
    - `_screen` mockeado: `screen` devuelve un mock, evitando RuntimeError.
    - `_surface` mockeado: buffer de dibujo válido para `_draw_circle`/`_draw_sprite`.
    - `_ensure_surface` mockeado: no recrea la surface real ni pisa `_surface`.
    """
    r = PygameInputCursorRenderer(width=800, height=600)
    r._initialize = MagicMock()  # type: ignore[method-assign]
    r._running = True  # type: ignore[attr-defined]
    r._screen = MagicMock()  # type: ignore[attr-defined]
    r._surface = MagicMock()  # type: ignore[assignment]

    with patch.object(r, "_ensure_surface", return_value=MagicMock()):
        yield r


class TestPygameInputCursorRenderer:
    def test_set_cursors_stores_list(self) -> None:
        """set_cursors debe almacenar la lista de cursores."""
        renderer = PygameInputCursorRenderer(width=800, height=600)
        cursors = [InputCursor(cursor_id="test")]

        renderer.set_cursors(cursors)

        assert renderer._cursors == cursors

    # ==========================================================
    # Tests de skip: verifican que NO se dibuja el cursor
    # ==========================================================
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

    # ==========================================================
    # Control positivo: SÍ se dibuja
    # ==========================================================
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

    # ==========================================================
    # Integración ligera con pygame.draw.circle
    # ==========================================================
    @patch("pose_app.adapters.render.pygame_input_cursor.pygame.draw.circle")
    def test_render_cursors_draws_circle(self, mock_circle: Mock) -> None:
        """render_cursors debe dibujar círculo para cursor sin sprite."""
        renderer = PygameInputCursorRenderer(width=800, height=600)
        renderer._initialize = MagicMock()  # type: ignore[method-assign]
        renderer._running = True  # type: ignore[attr-defined]
        renderer._screen = MagicMock()  # type: ignore[attr-defined]
        renderer._surface = MagicMock()  # type: ignore[assignment]

        cursor = InputCursor(
            cursor_id="test",
            appearance=CursorAppearance(size=40.0, color=(255, 255, 0)),
        )
        cursor.is_visible = True
        cursor.position = (0.5, 0.5)

        renderer.set_cursors([cursor])

        with (
            patch.object(renderer, "_ensure_surface", return_value=MagicMock()),
            # Evita crear una pygame.Surface real para inner_surface
            patch(
                "pose_app.adapters.render.pygame_input_cursor.pygame.Surface",
                return_value=MagicMock(),
            ),
        ):
            renderer.render_cursors()

        assert mock_circle.called

    def test_render_cursors_converts_coordinates(self) -> None:
        """get_position_pixels convierte coordenadas normalizadas a píxeles."""
        cursor = InputCursor(cursor_id="test")
        cursor.is_visible = True
        cursor.position = (0.25, 0.75)  # 25% de 800 = 200, 75% de 600 = 450

        pos = cursor.get_position_pixels(800, 600)
        assert pos == (200.0, 450.0)

    def test_close_clears_cache(self) -> None:
        """close debe limpiar el cache de sprites."""
        renderer = PygameInputCursorRenderer(width=800, height=600)
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

        # 2 cursores visibles → 2 llamadas a _draw_circle (1 por cursor)
        assert draw_circle.call_count == 2
        draw_sprite.assert_not_called()

        # Los 3 cursores están en la lista, pero solo 2 son visibles
        assert len(renderer._cursors) == 3
