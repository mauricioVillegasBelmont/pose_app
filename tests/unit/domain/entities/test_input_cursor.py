"""
Tests unitarios para InputCursor.
Validan la creación, estado, timeout y conversión a píxeles.
"""

import pytest

from pose_app.domain.entities.input_cursor import (
    CursorAppearance,
    CursorCollision,
    InputCursor,
)
from pose_app.domain.entities.particles.components import SpriteConfig, SpriteState


class TestCursorAppearance:
    def test_creation_with_defaults(self) -> None:
        """CursorAppearance con defaults válidos."""
        appearance = CursorAppearance()

        assert appearance.size == 40.0
        assert appearance.color == (255, 255, 0)
        assert appearance.padding_x == 0.0
        assert appearance.padding_y == 0.0

    def test_creation_with_custom_values(self) -> None:
        """CursorAppearance con valores personalizados."""
        appearance = CursorAppearance(
            size=60.0,
            color=(255, 0, 0),
            padding_x=5.0,
            padding_y=5.0,
        )

        assert appearance.size == 60.0
        assert appearance.color == (255, 0, 0)
        assert appearance.padding_x == 5.0
        assert appearance.padding_y == 5.0

    def test_rejects_invalid_size(self) -> None:
        """Size debe ser positivo."""
        with pytest.raises(ValueError, match="size"):
            CursorAppearance(size=0.0)

        with pytest.raises(ValueError, match="size"):
            CursorAppearance(size=-10.0)

    def test_rejects_invalid_color(self) -> None:
        """Color debe ser RGB válido (0-255)."""
        with pytest.raises(ValueError, match="color"):
            CursorAppearance(color=(256, 0, 0))

        with pytest.raises(ValueError, match="color"):
            CursorAppearance(color=(-1, 0, 0))

    def test_is_immutable(self) -> None:
        """CursorAppearance es inmutable."""
        appearance = CursorAppearance()

        with pytest.raises(AttributeError):
            appearance.size = 100.0  # type: ignore


class TestCursorCollision:
    def test_creation_with_default(self) -> None:
        """CursorCollision con default válido."""
        collision = CursorCollision()
        assert collision.radius == 20.0

    def test_creation_with_custom_radius(self) -> None:
        """CursorCollision con radio personalizado."""
        collision = CursorCollision(radius=30.0)
        assert collision.radius == 30.0

    def test_rejects_invalid_radius(self) -> None:
        """Radius debe ser positivo."""
        with pytest.raises(ValueError, match="radius"):
            CursorCollision(radius=0.0)

        with pytest.raises(ValueError, match="radius"):
            CursorCollision(radius=-5.0)

    def test_is_immutable(self) -> None:
        """CursorCollision es inmutable."""
        collision = CursorCollision()

        with pytest.raises(AttributeError):
            collision.radius = 50.0  # type: ignore


class TestInputCursor:
    def test_creation_with_defaults(self) -> None:
        """InputCursor con defaults válidos."""
        cursor = InputCursor(cursor_id="left_hand")

        assert cursor.cursor_id == "left_hand"
        assert cursor.position is None
        assert cursor.is_visible is False
        assert cursor.last_seen == 0.0
        assert isinstance(cursor.appearance, CursorAppearance)
        assert isinstance(cursor.collision, CursorCollision)
        assert cursor.sprite_config is None
        assert cursor.sprite_state is None

    def test_creation_with_custom_components(self) -> None:
        """InputCursor con componentes personalizados."""
        appearance = CursorAppearance(size=50.0, color=(0, 255, 0))
        collision = CursorCollision(radius=25.0)
        sprite_config = SpriteConfig(
            path="cursor.png",
            frame_width=64.0,
            frame_height=64.0,
            frame_count=4,
            fps=10.0,
        )
        sprite_state = SpriteState(current_frame=0, elapsed_time=0.0)

        cursor = InputCursor(
            cursor_id="right_hand",
            appearance=appearance,
            collision=collision,
            sprite_config=sprite_config,
            sprite_state=sprite_state,
        )

        assert cursor.cursor_id == "right_hand"
        assert cursor.appearance.size == 50.0
        assert cursor.collision.radius == 25.0
        assert cursor.sprite_config is sprite_config
        assert cursor.sprite_state is sprite_state

    def test_position_is_mutable(self) -> None:
        """Position es mutable (se actualiza cada frame)."""
        cursor = InputCursor(cursor_id="test")

        cursor.position = (0.5, 0.5)
        assert cursor.position == (0.5, 0.5)

        cursor.position = (0.7, 0.3)
        assert cursor.position == (0.7, 0.3)

    def test_visibility_is_mutable(self) -> None:
        """is_visible es mutable."""
        cursor = InputCursor(cursor_id="test")

        assert cursor.is_visible is False

        cursor.is_visible = True
        assert cursor.is_visible is True

    def test_last_seen_is_mutable(self) -> None:
        """last_seen es mutable."""
        cursor = InputCursor(cursor_id="test")

        cursor.last_seen = 10.5
        assert cursor.last_seen == 10.5

    def test_appearance_is_immutable(self) -> None:
        """Appearance es inmutable (frozen)."""
        cursor = InputCursor(cursor_id="test")

        with pytest.raises(AttributeError):
            cursor.appearance.size = 100.0  # type: ignore

    def test_update_with_new_position(self) -> None:
        """update() con nueva posición actualiza estado."""
        cursor = InputCursor(cursor_id="test")

        cursor.update(new_position=(0.5, 0.5), current_time=1.0, timeout=2.0)

        assert cursor.position == (0.5, 0.5)
        assert cursor.is_visible is True
        assert cursor.last_seen == 1.0

    def test_update_with_none_before_timeout(self) -> None:
        """update() con None antes del timeout mantiene última posición."""
        cursor = InputCursor(cursor_id="test")

        # Primera actualización: posición válida
        cursor.update(new_position=(0.5, 0.5), current_time=1.0, timeout=2.0)

        # Segunda actualización: None, pero dentro del timeout
        cursor.update(new_position=None, current_time=2.0, timeout=2.0)

        # Debe mantener la última posición
        assert cursor.position == (0.5, 0.5)
        assert cursor.is_visible is True

    def test_update_with_none_after_timeout(self) -> None:
        """update() con None después del timeout marca como invisible."""
        cursor = InputCursor(cursor_id="test")

        # Primera actualización: posición válida
        cursor.update(new_position=(0.5, 0.5), current_time=1.0, timeout=2.0)

        # Segunda actualización: None, después del timeout
        cursor.update(new_position=None, current_time=4.0, timeout=2.0)

        # Debe marcar como invisible y limpiar posición
        assert cursor.position is None
        assert cursor.is_visible is False

    def test_get_position_pixels(self) -> None:
        """get_position_pixels() convierte normalizado a píxeles."""
        cursor = InputCursor(cursor_id="test")
        cursor.position = (0.5, 0.5)

        result = cursor.get_position_pixels(screen_w=800, screen_h=600)

        assert result == (400.0, 300.0)

    def test_get_position_pixels_when_none(self) -> None:
        """get_position_pixels() retorna None si no hay posición."""
        cursor = InputCursor(cursor_id="test")

        result = cursor.get_position_pixels(screen_w=800, screen_h=600)

        assert result is None

    def test_get_collision_radius_pixels(self) -> None:
        """get_collision_radius_pixels() calcula radio en píxeles."""
        cursor = InputCursor(cursor_id="test")
        cursor.collision = CursorCollision(radius=20.0)  # 20% del mínimo

        # min(800, 600) = 600, 20% de 600 = 120
        result = cursor.get_collision_radius_pixels(screen_w=800, screen_h=600)

        assert result == 120.0
