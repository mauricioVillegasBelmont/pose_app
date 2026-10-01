"""
Property-based tests para Particle.
"""

from hypothesis import given, strategies as st

from domain.entities.particle import Particle


# ==========================================
# Strategies
# ==========================================

particle = st.builds(
    Particle,
    x=st.floats(min_value=-1000, max_value=1000, allow_nan=False),
    y=st.floats(min_value=-1000, max_value=1000, allow_nan=False),
    vx=st.floats(min_value=-10, max_value=10, allow_nan=False),
    vy=st.floats(min_value=-10, max_value=10, allow_nan=False),
    size=st.floats(min_value=0.1, max_value=100, allow_nan=False),
    life=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)


# ==========================================
# Propiedades
# ==========================================

class TestParticleInvariants:

    @given(p=particle)
    def test_update_decreases_life(self, p: Particle):
        """Después de update, life es estrictamente menor (o igual a 0)."""
        original_life = p.life
        p.update(gravity=0.0)

        assert p.life < original_life or p.life <= 0.01

    @given(p=particle)
    def test_update_modifies_position(self, p: Particle):
        """Con velocidad, la posición cambia."""
        original_x, original_y = p.x, p.y
        p.update(gravity=0.1)

        # Si tiene velocidad inicial, la posición cambia
        if abs(p.vx) > 1e-6 or abs(p.vy) > 1e-6:
            assert p.x != original_x or p.y != original_y

    @given(
        life=st.floats(
            min_value=0.02, max_value=1.0, allow_nan=False
        )
    )
    def test_alive_when_life_above_threshold(self, life: float):
        """life > 0.01 → is_alive() == True."""
        p = Particle(x=0, y=0, life=life)
        assert p.is_alive() is True

    @given(
        life=st.floats(
            min_value=0.0, max_value=0.01, allow_nan=False
        )
    )
    def test_dead_when_life_at_or_below_threshold(self, life: float):
        """life <= 0.01 → is_alive() == False."""
        p = Particle(x=0, y=0, life=life)
        assert p.is_alive() is False

    @given(
        x=st.floats(min_value=-1000, max_value=1000, allow_nan=False),
        y=st.floats(min_value=-1000, max_value=1000, allow_nan=False),
        count=st.integers(min_value=1, max_value=50),
    )
    def test_create_burst_produces_count_particles(
        self, x: float, y: float, count: int
    ):
        """create_burst genera exactamente `count` partículas."""
        particles = Particle.create_burst(x, y, count=count)
        assert len(particles) == count