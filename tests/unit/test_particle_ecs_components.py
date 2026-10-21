"""
Tests para los componentes ECS-lite y la entidad Particle.
"""

from dataclasses import replace

import pytest

from pose_app.domain.capabilities.particles.components import (
    Appearance,
    CollisionProfile,
    Lifespan,
    Position,
    SpriteConfig,
    SpriteState,
)
from pose_app.domain.entities.particle import Particle


class TestPositionComponent:
    """El componente Position es el único mutable, ya que los sistemas de física
    necesitan actualizar x, y, vx, vy en cada frame sin crear nuevos objetos."""

    def test_position_is_mutable(self) -> None:
        # Arrange
        pos = Position(x=10.0, y=20.0, vx=1.0, vy=2.0)

        # Act
        pos.x += pos.vx
        pos.y += pos.vy

        # Assert
        assert pos.x == 11.0
        assert pos.y == 22.0


class TestFrozenComponents:
    """Appearance, Lifespan y CollisionProfile deben ser inmutables (frozen)
    para prevenir efectos secundarios accidentales en la lógica de negocio."""

    def test_appearance_is_frozen(self) -> None:
        app = Appearance(size=10.0, color=(255, 0, 0))
        with pytest.raises(AttributeError):
            app.size = 20.0  # type: ignore[misc]

    def test_lifespan_initializes_current_life_to_max(self) -> None:
        # Arrange & Act: usar factory method para vida recién nacida
        life = Lifespan.fresh(5.0)

        # Assert
        assert life.max_life == 5.0
        assert life.current_life == 5.0

    def test_lifespan_accepts_explicit_current_life(self) -> None:
        # Arrange & Act: útil para tests o estados intermedios
        life = Lifespan(max_life=5.0, current_life=3.0)

        # Assert
        assert life.max_life == 5.0
        assert life.current_life == 3.0

    def test_lifespan_update_with_replace(self) -> None:
        # Arrange
        life = Lifespan.fresh(5.0)

        # Act: la forma correcta de "mutar" un dataclass frozen
        updated_life = replace(life, current_life=4.0)

        # Assert
        assert life.current_life == 5.0  # el original no cambia
        assert updated_life.current_life == 4.0  # la copia tiene el nuevo valor

    def test_lifespan_rejects_current_greater_than_max(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match=r"must be in \[0, 5\.0\]"):
            Lifespan(max_life=5.0, current_life=10.0)

    def test_collision_profile_has_behavior(self) -> None:
        # Arrange & Act
        collision = CollisionProfile(radius=30.0, behavior="bounce")

        # Assert
        assert collision.radius == 30.0
        assert collision.behavior == "bounce"
        assert collision.behavior in ("destroy", "bounce")


class TestParticleEntity:
    """La entidad Particle es un contenedor de componentes.
    Su única responsabilidad es agruparlos y ofrecer helpers de consulta."""

    def test_particle_assembly_with_optional_components(self) -> None:
        # Arrange
        pos = Position(x=100.0, y=100.0)
        app = Appearance(size=15.0, color=(0, 255, 0))

        # Act
        particle = Particle(position=pos, appearance=app)

        # Assert
        assert particle.id is not None
        assert particle.lifespan is None
        assert particle.collision is None
        assert particle.is_alive() is True  # Sin lifespan, es infinita

    def test_particle_with_lifespan_and_collision(self) -> None:
        # Arrange
        pos = Position(x=0.0, y=0.0)
        app = Appearance()
        life = Lifespan.fresh(max_life=10.0)
        collision = CollisionProfile(radius=25.0, behavior="destroy")

        # Act
        particle = Particle(
            position=pos,
            appearance=app,
            lifespan=life,
            collision=collision,
        )

        # Assert
        assert particle.is_alive() is True
        assert particle.collision.behavior == "destroy"

    def test_particle_is_alive_evaluates_current_life(self) -> None:
        # Arrange
        pos = Position(x=0.0, y=0.0)
        app = Appearance()
        # Creamos directamente con current_life bajo (más simple que replace)
        life = Lifespan(max_life=1.0, current_life=0.005)
        particle = Particle(position=pos, appearance=app, lifespan=life)

        # Act & Assert
        assert particle.is_alive() is False


class TestAppearanceComponents:
    """El componente Appearance define la representación visual."""

    def test_appearance_is_frozen(self) -> None:
        """Appearance es inmutable."""
        app = Appearance(size=10.0, color=(255, 0, 0))
        with pytest.raises(AttributeError):
            app.size = 20.0  # type: ignore[misc]

    def test_appearance_accepts_padding(self) -> None:
        """Appearance puede tener padding_x y padding_y para margen visual."""
        app = Appearance(size=20.0, color=(255, 0, 0), padding_x=5.0, padding_y=10.0)
        assert app.padding_x == 5.0
        assert app.padding_y == 10.0

    def test_appearance_padding_defaults_to_zero(self) -> None:
        """Por defecto, padding es 0 para mantener retrocompatibilidad."""
        app = Appearance()
        assert app.padding_x == 0.0
        assert app.padding_y == 0.0


class TestLifespanInvariants:
    """El contrato del componente debe ser imposible de violar."""

    def test_fresh_starts_at_max_life(self) -> None:
        # Arrange & Act
        life = Lifespan.fresh(8.0)

        # Assert
        assert life.current_life == life.max_life == 8.0

    def test_zero_current_life_is_valid(self) -> None:
        # Una partícula muerta debe ser representable (la usa cull).
        assert Lifespan(max_life=1.0, current_life=0.0).current_life == 0.0

    def test_negative_current_life_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            Lifespan(max_life=1.0, current_life=-0.1)

    def test_non_positive_max_life_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="greater than 0"):
            Lifespan.fresh(0.0)


class TestSpriteComponents:
    """Los componentes de sprite permiten renderizar imágenes y animaciones."""

    def test_sprite_config_is_frozen(self) -> None:
        """SpriteConfig es inmutable (solo lectura)."""
        config = SpriteConfig(
            path="blood-curse.png",
            frame_width=128.0,
            frame_height=128.0,
            frame_count=16,
            fps=12.0,
            animation_mode="loop",
        )
        with pytest.raises(AttributeError):
            config.frame_width = 256.0  # type: ignore[misc]

    def test_sprite_state_is_mutable(self) -> None:
        """
        SpriteState es mutable para permitir actualizaciones in-place
        por el AnimationSystem (rendimiento en tiempo real).
        """
        state = SpriteState(current_frame=0, elapsed_time=0.0)

        # Act
        state.current_frame = 5
        state.elapsed_time = 0.083

        # Assert
        assert state.current_frame == 5
        assert state.elapsed_time == pytest.approx(0.083)

    def test_sprite_config_validates_frame_count(self) -> None:
        """No se pueden tener 0 o menos frames."""
        with pytest.raises(ValueError, match="frame_count"):
            SpriteConfig(
                path="test.png",
                frame_width=128.0,
                frame_height=128.0,
                frame_count=0,
            )

    def test_sprite_config_validates_fps(self) -> None:
        """FPS negativos no tienen sentido."""
        with pytest.raises(ValueError, match="fps"):
            SpriteConfig(
                path="test.png",
                frame_width=128.0,
                frame_height=128.0,
                frame_count=1,
                fps=-5.0,
            )

    def test_sprite_config_validates_animation_mode(self) -> None:
        """Solo se permiten modos 'loop' y 'one_shot'."""
        with pytest.raises(ValueError, match="animation_mode"):
            SpriteConfig(
                path="test.png",
                frame_width=128.0,
                frame_height=128.0,
                frame_count=1,
                animation_mode="ping_pong",  # type: ignore[arg-type]
            )


class TestParticleWithSprites:
    """La entidad Particle puede tener componentes de sprite opcionales."""

    def test_particle_with_static_sprite(self) -> None:
        """Partícula con sprite estático (1 frame, 0 FPS)."""
        pos = Position(x=100.0, y=100.0)
        app = Appearance()
        config = SpriteConfig(
            path="icon.png",
            frame_width=64.0,
            frame_height=64.0,
            frame_count=1,
            fps=0.0,
            animation_mode="loop",
        )
        state = SpriteState(current_frame=0, elapsed_time=0.0)

        particle = Particle(
            position=pos,
            appearance=app,
            sprite_config=config,
            sprite_state=state,
        )

        assert particle.sprite_config is not None
        assert particle.sprite_config.frame_count == 1
        assert particle.sprite_state.current_frame == 0

    def test_particle_with_animated_sprite(self) -> None:
        """Partícula con sprite animado (16 frames, 12 FPS, loop)."""
        pos = Position(x=200.0, y=200.0)
        app = Appearance()
        config = SpriteConfig(
            path="blood-curse.png",
            frame_width=256.0,
            frame_height=256.0,
            frame_count=16,
            fps=12.0,
            animation_mode="loop",
        )
        state = SpriteState(current_frame=0, elapsed_time=0.0)

        particle = Particle(
            position=pos,
            appearance=app,
            sprite_config=config,
            sprite_state=state,
        )

        assert particle.sprite_config.fps == 12.0
        assert particle.sprite_config.animation_mode == "loop"
