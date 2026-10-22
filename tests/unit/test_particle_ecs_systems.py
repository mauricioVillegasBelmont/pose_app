"""
Tests TDD de los sistemas ECS-lite de partículas.

Son tests puramente numéricos: no requieren pygame, cámara, pose ni render.
"""

import pytest

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.components import (
    Appearance,
    Lifespan,
    Position,
    SpriteConfig,
    SpriteState,
)
from pose_app.domain.entities.particles.systems import (
    AnimationSystem,
    LifespanSystem,
    MovementSystem,
)


def make_particle(
    *,
    x: float = 0.0,
    y: float = 0.0,
    vx: float = 0.0,
    vy: float = 0.0,
    max_life: float | None = None,
    current_life: float | None = None,
) -> Particle:
    """
    Factory de tests. max_life=None significa 'vida infinita'.

    Nota: es un helper de testing. En el paso de spawn será reemplazado
    por el factory real del dominio.
    """
    lifespan = None
    if max_life is not None:
        lifespan = (
            Lifespan.fresh(max_life)
            if current_life is None
            else Lifespan(max_life=max_life, current_life=current_life)
        )

    return Particle(
        position=Position(x=x, y=y, vx=vx, vy=vy),
        appearance=Appearance(),
        lifespan=lifespan,
    )


# ==============================================================================
# MovementSystem
# ==============================================================================


class TestMovementSystem:
    def test_particle_at_rest_stays_at_rest(self) -> None:
        # Arrange
        particle = make_particle(x=10.0, y=20.0)
        system = MovementSystem(gravity=0.0, damping=1.0)

        # Act
        system.update([particle])

        # Assert
        assert (particle.position.x, particle.position.y) == (10.0, 20.0)

    def test_velocity_translates_position(self) -> None:
        # Arrange
        particle = make_particle(vx=2.0, vy=3.0)
        system = MovementSystem(gravity=0.0, damping=1.0)

        # Act
        system.update([particle])

        # Assert
        assert (particle.position.x, particle.position.y) == (2.0, 3.0)

    def test_gravity_increases_vertical_velocity(self) -> None:
        # Arrange
        particle = make_particle()
        system = MovementSystem(gravity=0.5, damping=1.0)

        # Act
        system.update([particle])

        # Assert
        assert particle.position.vy == pytest.approx(0.5)

    def test_gravity_affects_position_in_the_same_tick(self) -> None:
        """Lock de comportamiento legacy: gravity -> vy -> y en UN solo tick."""
        # Arrange
        particle = make_particle()
        system = MovementSystem(gravity=0.1, damping=1.0)

        # Act
        system.update([particle])

        # Assert
        assert particle.position.y == pytest.approx(0.1)

    def test_damping_reduces_velocity(self) -> None:
        # Arrange
        particle = make_particle(vx=10.0)
        system = MovementSystem(gravity=0.0, damping=0.5)

        # Act
        system.update([particle])

        # Assert
        assert particle.position.vx == pytest.approx(5.0)

    def test_zero_damping_stops_horizontal_motion(self) -> None:
        # Arrange
        particle = make_particle(vx=10.0)
        system = MovementSystem(gravity=0.0, damping=0.0)

        # Act
        system.update([particle])

        # Assert
        assert particle.position.x == 0.0

    def test_two_ticks_match_legacy_order_of_operations(self) -> None:
        """
        Lock matemático del legacy (g=0.1, d=0.99, vx=1, vy=0):

        tick 1: vy=0.1   -> vx=0.99   vy=0.099   -> x=0.99   y=0.099
        tick 2: vy=0.199 -> vx=0.9801 vy=0.19701 -> x=1.9701 y=0.29601
        """
        # Arrange
        particle = make_particle(vx=1.0)
        system = MovementSystem(gravity=0.1, damping=0.99)

        # Act
        system.update([particle])
        system.update([particle])

        # Assert
        assert (particle.position.x, particle.position.y) == pytest.approx(
            (1.9701, 0.29601)
        )

    def test_system_does_not_accumulate_state_between_calls(self) -> None:
        # Arrange
        first = make_particle(vx=1.0)
        second = make_particle(vx=1.0)
        system = MovementSystem(gravity=0.0, damping=1.0)

        # Act
        system.update([first])
        system.update([second])

        # Assert
        assert first.position.x == second.position.x == 1.0


# ==============================================================================
# LifespanSystem — decaimiento
# ==============================================================================


class TestLifespanSystem:
    def test_infinite_particle_is_not_touched(self) -> None:
        # Arrange
        particle = make_particle()  # sin componente Lifespan
        system = LifespanSystem(decay=0.5)

        # Act
        system.update([particle])

        # Assert
        assert particle.lifespan is None

    def test_decay_reduces_current_life(self) -> None:
        # Arrange
        particle = make_particle(max_life=10.0)
        system = LifespanSystem(decay=0.5)

        # Act
        system.update([particle])

        # Assert
        assert particle.lifespan is not None  # guard de narrowing para mypy
        assert particle.lifespan.current_life == pytest.approx(5.0)

    def test_decay_preserves_max_life(self) -> None:
        # Arrange
        particle = make_particle(max_life=10.0)
        system = LifespanSystem(decay=0.5)

        # Act
        system.update([particle])

        # Assert
        assert particle.lifespan is not None
        assert particle.lifespan.max_life == 10.0

    def test_decay_replaces_the_component_instance(self) -> None:
        """Contrato frozen: el sistema NO muta el componente, lo reemplaza."""
        # Arrange
        particle = make_particle(max_life=10.0)
        original = particle.lifespan
        system = LifespanSystem(decay=0.5)

        # Act
        system.update([particle])

        # Assert
        assert particle.lifespan is not original

    def test_decay_is_multiplicative_not_linear(self) -> None:
        """Lock legacy: life *= 0.995, NO life -= dt."""
        # Arrange
        particle = make_particle(max_life=1.0)
        system = LifespanSystem(decay=0.5)

        # Act
        system.update([particle])
        system.update([particle])

        # Assert
        assert particle.lifespan is not None
        assert particle.lifespan.current_life == pytest.approx(0.25)

    def test_mixed_population_only_affects_finite_particles(self) -> None:
        # Arrange
        finite = make_particle(max_life=10.0)
        infinite = make_particle()
        system = LifespanSystem(decay=0.5)

        # Act
        system.update([finite, infinite])

        # Assert
        assert infinite.lifespan is None
        assert finite.lifespan is not None
        assert finite.lifespan.current_life == pytest.approx(5.0)

    def test_lifespan_system_does_not_touch_position(self) -> None:
        """Ortogonalidad entre sistemas."""
        # Arrange
        particle = make_particle(x=1.0, y=2.0, vx=3.0, vy=4.0, max_life=10.0)
        before = (
            particle.position.x,
            particle.position.y,
            particle.position.vx,
            particle.position.vy,
        )

        # Act
        LifespanSystem(decay=0.5).update([particle])

        # Assert
        after = (
            particle.position.x,
            particle.position.y,
            particle.position.vx,
            particle.position.vy,
        )
        assert after == before


# ==============================================================================
# LifespanSystem — retiro de entidades
# ==============================================================================


class TestLifespanCull:
    def test_cull_removes_expired_particles(self) -> None:
        # Arrange
        alive = make_particle(max_life=1.0, current_life=0.5)
        dead = make_particle(max_life=1.0, current_life=0.005)

        # Act
        result = LifespanSystem().cull([alive, dead])

        # Assert
        assert result == [alive]

    def test_cull_keeps_infinite_particles(self) -> None:
        # Arrange
        particle = make_particle()

        # Act & Assert
        assert LifespanSystem().cull([particle]) == [particle]

    def test_cull_does_not_mutate_the_input_list(self) -> None:
        # Arrange
        dead = make_particle(max_life=1.0, current_life=0.0)
        source = [dead]

        # Act
        LifespanSystem().cull(source)

        # Assert
        assert source == [dead]

    def test_cull_on_empty_list_returns_empty_list(self) -> None:
        assert LifespanSystem().cull([]) == []

    def test_threshold_is_strict(self) -> None:
        """current_life == 0.01 sigue viva; por debajo, muere."""
        # Arrange
        at_threshold = make_particle(max_life=1.0, current_life=0.01)
        below_threshold = make_particle(max_life=1.0, current_life=0.009)

        # Act
        result = LifespanSystem().cull([at_threshold, below_threshold])

        # Assert
        assert result == [at_threshold]


# ==============================================================================
# Composición: la tesis ECS completa
# ==============================================================================


class TestSystemComposition:
    def test_finite_particle_eventually_dies(self) -> None:
        """
        Simula el loop de un juego real: mover -> decaer -> retirar.
        Con decay=0.995, la vida cruza el umbral alrededor del tick 919.
        """
        # Arrange
        particle = make_particle(max_life=1.0)
        movement = MovementSystem(gravity=0.1, damping=0.99)
        lifespan = LifespanSystem(decay=0.995)
        alive = [particle]

        # Act
        for _ in range(1000):
            movement.update(alive)
            lifespan.update(alive)
            alive = lifespan.cull(alive)
            if not alive:
                break

        # Assert
        assert alive == []

    def test_infinite_particle_survives_the_same_pipeline(self) -> None:
        """
        Mismos sistemas, misma configuración. La ÚNICA diferencia es
        la presencia del componente Lifespan. Eso es ECS.
        """
        # Arrange
        particle = make_particle()
        movement = MovementSystem(gravity=0.1, damping=0.99)
        lifespan = LifespanSystem(decay=0.995)
        alive = [particle]

        # Act
        for _ in range(1000):
            movement.update(alive)
            lifespan.update(alive)
            alive = lifespan.cull(alive)

        # Assert
        assert alive == [particle]


class TestAnimationSystem:
    """El AnimationSystem actualiza el estado del sprite basado en el tiempo."""

    def test_static_sprite_does_not_change(self) -> None:
        """Si fps=0, el frame no cambia."""
        # Arrange
        config = SpriteConfig(path="test.png", frame_width=64, frame_height=64, fps=0.0)
        state = SpriteState(current_frame=0, elapsed_time=0.0)
        particle = Particle(
            position=Position(0, 0),
            appearance=Appearance(),
            sprite_config=config,
            sprite_state=state,
        )
        system = AnimationSystem()

        # Act
        system.update([particle], dt=0.1)

        # Assert
        assert particle.sprite_state.current_frame == 0

    def test_animated_sprite_advances_frame(self) -> None:
        """Tras acumular suficiente tiempo, avanza al siguiente frame."""
        # Arrange
        # 10 fps = 0.1s por frame
        config = SpriteConfig(
            path="test.png",
            frame_width=64,
            frame_height=64,
            frame_count=4,
            fps=10.0,
            animation_mode="loop",
        )
        state = SpriteState(current_frame=0, elapsed_time=0.0)
        particle = Particle(
            position=Position(0, 0),
            appearance=Appearance(),
            sprite_config=config,
            sprite_state=state,
        )
        system = AnimationSystem()

        # Act: 0.15s > 0.1s (umbral de frame)
        system.update([particle], dt=0.15)

        # Assert
        assert particle.sprite_state.current_frame == 1
        assert particle.sprite_state.elapsed_time == pytest.approx(0.05)  # 0.15 - 0.10

    def test_loop_mode_wraps_around(self) -> None:
        """En modo loop, tras el último frame vuelve al 0."""
        # Arrange
        config = SpriteConfig(
            path="test.png",
            frame_width=64,
            frame_height=64,
            frame_count=2,
            fps=10.0,
            animation_mode="loop",
        )
        state = SpriteState(current_frame=1, elapsed_time=0.0)  # Último frame
        particle = Particle(
            position=Position(0, 0),
            appearance=Appearance(),
            sprite_config=config,
            sprite_state=state,
        )
        system = AnimationSystem()

        # Act
        system.update([particle], dt=0.2)  # Avanza 2 frames

        # Assert
        assert particle.sprite_state.current_frame == 1  # (1 -> 0 -> 1)

    def test_one_shot_mode_stops_at_last_frame(self) -> None:
        """En modo one_shot, se detiene en el último frame."""
        # Arrange
        config = SpriteConfig(
            path="test.png",
            frame_width=64,
            frame_height=64,
            frame_count=2,
            fps=10.0,
            animation_mode="one_shot",
        )
        state = SpriteState(current_frame=1, elapsed_time=0.0)
        particle = Particle(
            position=Position(0, 0),
            appearance=Appearance(),
            sprite_config=config,
            sprite_state=state,
        )
        system = AnimationSystem()

        # Act
        system.update([particle], dt=0.5)

        # Assert
        assert particle.sprite_state.current_frame == 1  # Se queda en el último

    def test_ignores_particles_without_sprite(self) -> None:
        """Partículas sin sprite_config no se ven afectadas."""
        # Arrange
        particle = Particle(position=Position(0, 0), appearance=Appearance())
        system = AnimationSystem()

        # Act & Assert (no debe lanzar error)
        system.update([particle], dt=0.1)
        assert particle.sprite_state is None
