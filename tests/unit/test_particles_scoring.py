from hypothesis import given
from hypothesis import strategies as st

from domain.entities.color import RGBColor
from domain.games.particles.rules import (
    BACKGROUND_COLORS,
    color_for_score,
    is_winner,
    particles_per_round,
)


class TestColorForScore:
    """Tests de la regla color_for_score."""

    def test_score_zero_is_first_color(self) -> None:
        """Score 0 → primer color (negro)."""
        color = color_for_score(0)
        assert color == RGBColor(20, 20, 20)

    def test_negative_score_returns_first_color(self) -> None:
        """Score negativo también → primer color (robustez)."""
        color = color_for_score(-5)
        assert color == RGBColor(20, 20, 20)

    def test_score_one_and_two_share_color(self) -> None:
        """Scores 1 y 2 comparten color."""
        assert color_for_score(1) == color_for_score(2)
        assert color_for_score(1) == RGBColor(60, 60, 80)

    def test_score_three_to_five_share_color(self) -> None:
        """Scores 3, 4, 5 comparten color."""
        assert color_for_score(3) == color_for_score(4) == color_for_score(5)
        assert color_for_score(3) == RGBColor(60, 60, 120)

    def test_score_six_and_above_share_color(self) -> None:
        """Scores 6+ comparten color."""
        assert color_for_score(6) == color_for_score(100)
        assert color_for_score(6) == RGBColor(120, 60, 30)

    def test_returns_rgb_color_instance(self) -> None:
        """Retorna instancia de RGBColor, no tupla."""
        color = color_for_score(3)
        assert isinstance(color, RGBColor)

    @given(score=st.integers(min_value=-100, max_value=1000))
    def test_never_raises(self, score: int) -> None:
        """Nunca lanza excepción para ningún score."""
        color = color_for_score(score)
        assert isinstance(color, RGBColor)

    @given(score=st.integers(min_value=-100, max_value=1000))
    def test_color_is_from_palette(self, score: int) -> None:
        """El color siempre pertenece a la paleta definida."""
        color = color_for_score(score)
        assert (color.r, color.g, color.b) in BACKGROUND_COLORS


# ==========================================
# particles_per_round
# ==========================================


class TestParticlesPerRound:
    """Tests de la regla particles_per_round."""

    def test_round_one_returns_two(self) -> None:
        assert particles_per_round(1) == 2

    def test_round_two_returns_three(self) -> None:
        assert particles_per_round(2) == 3

    def test_round_three_returns_four(self) -> None:
        assert particles_per_round(3) == 4

    def test_round_four_and_above_caps_at_five(self) -> None:
        assert particles_per_round(4) == 5
        assert particles_per_round(5) == 5
        assert particles_per_round(100) == 5

    def test_zero_or_negative_rounds_return_two(self) -> None:
        """Rondas inválidas retornan el mínimo (robustez)."""
        assert particles_per_round(0) == 2
        assert particles_per_round(-5) == 2

    @given(round_number=st.integers(min_value=-100, max_value=1000))
    def test_always_between_2_and_5(self, round_number: int) -> None:
        """Siempre entre 2 y 5, sin importar la ronda."""
        result = particles_per_round(round_number)
        assert 2 <= result <= 5

    @given(round_number=st.integers(min_value=1, max_value=1000))
    def test_monotonic_non_decreasing(self, round_number: int) -> None:
        """Nunca decrece al aumentar la ronda."""
        current = particles_per_round(round_number)
        next_val = particles_per_round(round_number + 1)
        assert next_val >= current


# ==========================================
# is_winner
# ==========================================


class TestIsWinner:
    """Tests de la regla is_winner."""

    def test_score_equal_to_max_is_winner(self) -> None:
        assert is_winner(score=10, max_score=10) is True

    def test_score_above_max_is_winner(self) -> None:
        assert is_winner(score=15, max_score=10) is True

    def test_score_below_max_is_not_winner(self) -> None:
        assert is_winner(score=5, max_score=10) is False

    @given(
        score=st.integers(min_value=0, max_value=100),
        max_score=st.integers(min_value=1, max_value=100),
    )
    def test_consistent_with_comparison(self, score: int, max_score: int) -> None:
        """Coincide con la comparación directa."""
        assert is_winner(score, max_score) == (score >= max_score)
