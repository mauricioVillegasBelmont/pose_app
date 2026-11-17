"""Tests de PygameBaseAdapter tras refactor (surface inyectada, no owner de pygame)."""

import pygame
import pytest

from pose_app.adapters.render.pygame_base import PygameBaseAdapter


@pytest.fixture
def surface() -> pygame.Surface:
    """Surface de prueba (no requiere display real)."""
    return pygame.Surface((800, 600))


class TestPygameBaseAdapterInit:
    def test_surface_is_required(self) -> None:
        """PygameBaseAdapter no puede construirse sin surface."""
        with pytest.raises(TypeError):
            PygameBaseAdapter()  # type: ignore[call-arg]

    def test_accepts_surface(self, surface: pygame.Surface) -> None:
        adapter = PygameBaseAdapter(surface=surface)
        assert adapter.screen is surface

    def test_width_height_from_surface(self, surface: pygame.Surface) -> None:
        adapter = PygameBaseAdapter(surface=surface)
        assert adapter.width == 800
        assert adapter.height == 600


class TestPygameBaseAdapterInitialize:
    def test_initialize_is_idempotent(
        self, surface: pygame.Surface, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dos llamadas a _initialize no deben crear ventanas."""
        set_mode_calls: list[tuple] = []
        monkeypatch.setattr(
            "pygame.display.set_mode",
            lambda *args, **kwargs: set_mode_calls.append((args, kwargs)),
        )

        adapter = PygameBaseAdapter(surface=surface)
        adapter._initialize()
        adapter._initialize()

        # No debe haberse llamado set_mode NUNCA
        assert set_mode_calls == []
        assert adapter.is_running is True

    def test_initialize_calls_pygame_init(
        self, surface: pygame.Surface, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_initialize invoca pygame.init (idempotente por diseño de pygame)."""
        init_calls: list[bool] = []
        monkeypatch.setattr("pygame.init", lambda: init_calls.append(True))

        adapter = PygameBaseAdapter(surface=surface)
        adapter._initialize()

        assert init_calls == [True]


class TestPygameBaseAdapterClose:
    def test_close_does_not_call_pygame_quit(
        self, surface: pygame.Surface, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """close() NO debe llamar pygame.quit (lo hace el SceneManager)."""
        quit_calls: list[bool] = []
        monkeypatch.setattr("pygame.quit", lambda: quit_calls.append(True))

        adapter = PygameBaseAdapter(surface=surface)
        adapter._initialize()
        adapter.close()

        assert quit_calls == []
        assert adapter.is_running is False

    def test_close_is_idempotent(self, surface: pygame.Surface) -> None:
        adapter = PygameBaseAdapter(surface=surface)
        adapter._initialize()
        adapter.close()
        adapter.close()  # no debe lanzar
        assert adapter.is_running is False
