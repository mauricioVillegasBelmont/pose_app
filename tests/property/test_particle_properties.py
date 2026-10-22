"""
Property-based tests para el sistema de partículas ECS-lite.
Valida invariantes de los componentes y sistemas con Hypothesis.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pose_app.domain.entities.particle import Particle
from pose_app.domain.entities.particles.components import (
    Appearance,
    Lifespan,
    Position,
)
from pose_app.domain.entities.particles.systems import (
    LifespanSystem,
    MovementSystem,
)

# ==========================================
# Strategies
# ==========================================

position_strategy = st.builds(
    Position,
    x=st.floats(min_value=-1000, max_value=1000, allow_nan=False),
    y=st.floats(min_value=-1000, max_value=1000, allow_nan=False),
    vx=st.floats(min_value=-10, max_value=10, allow_nan=False),
    vy=st.floats(min_value=-10, max_value=10, allow_nan=False),
)

appearance_strategy = st.builds(
    Appearance,
    size=st.floats(min_value=0.1, max_value=100, allow_nan=False),
    color=st.tuples(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
    ),
)

# CORRECCIÓN 1: Generar max_life y crear Lifespan directamente para evitar
# que Hypothesis intente construir con current_life aleatorio y falle la validación.
lifespan_strategy = st.floats(min_value=0.1, max_value=10.0, allow_nan=False).map(
    lambda max_life: Lifespan(max_life=max_life, current_life=max_life)
)

particle_with_life_strategy = st.builds(
    Particle,
    position=position_strategy,
    appearance=appearance_strategy,
    lifespan=lifespan_strategy,
)

particle_infinite_strategy = st.builds(
    Particle,
    position=position_strategy,
    appearance=appearance_strategy,
    lifespan=st.none(),
)

# ==========================================
# Propiedades
# ==========================================


class TestParticleECSInvariants:
    @given(p=particle_with_life_strategy)
    def test_lifespan_system_decreases_life(self, p: Particle) -> None:
        """El LifespanSystem reduce la vida actual de forma multiplicativa."""
        original_life = p.lifespan.current_life  # type: ignore
        system = LifespanSystem(decay=0.99)
        system.update([p])

        # La vida debe haber disminuido estrictamente
        assert p.lifespan.current_life < original_life  # type: ignore

    @given(p=particle_infinite_strategy)
    def test_infinite_particle_ignores_lifespan_system(self, p: Particle) -> None:
        """Partículas sin Lifespan no son afectadas por el sistema."""
        system = LifespanSystem(decay=0.5)
        system.update([p])
        assert p.lifespan is None

    @given(
        pos=position_strategy,
        gravity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        damping=st.floats(min_value=0.5, max_value=1.0, allow_nan=False),
    )
    def test_movement_system_applies_physics(
        self, pos: Position, gravity: float, damping: float
    ) -> None:
        """
        El MovementSystem aplica gravedad y amortiguación exactamente
        según la fórmula: vy = (vy + gravity) * damping
        """
        p = Particle(position=pos, appearance=Appearance())
        system = MovementSystem(gravity=gravity, damping=damping)

        original_vx = p.position.vx
        original_vy = p.position.vy

        system.update([p])

        # CORRECCIÓN 2: Verificar la fórmula exacta en lugar de asumir que "aumenta"
        expected_vy = (original_vy + gravity) * damping
        expected_vx = original_vx * damping

        assert p.position.vy == pytest.approx(expected_vy)
        assert p.position.vx == pytest.approx(expected_vx)
