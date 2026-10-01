"""
Property-based tests para RGBColor.

Verifican invariantes matemáticas del color.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.entities.color import RGBColor

# ==========================================
# Strategies (generadores reutilizables)
# ==========================================

# Estrategia para generar canales de color válidos
color_channel = st.integers(min_value=0, max_value=255)

# Estrategia para generar un RGBColor válido
rgb_color = st.builds(
    RGBColor,
    r=color_channel,
    g=color_channel,
    b=color_channel,
)

# Estrategia para t (factor de interpolación) válido
interpolation_factor = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)


# ==========================================
# Propiedades
# ==========================================

class TestRGBColorInvariants:

    @given(r=color_channel, g=color_channel, b=color_channel)
    def test_any_valid_channel_accepted(self, r: int, g: int, b: int):
        """Cualquier canal válido [0, 255] se acepta sin error."""
        color = RGBColor(r, g, b)
        assert color.r == r
        assert color.g == g
        assert color.b == b

    @given(r=st.integers(min_value=256), g=color_channel, b=color_channel)
    def test_channel_above_255_rejected(self, r: int, g: int, b: int):
        """Un canal > 255 debe lanzar ValueError."""
        with pytest.raises(ValueError):
            RGBColor(r, g, b)

    @given(r=st.integers(max_value=-1), g=color_channel, b=color_channel)
    def test_channel_below_0_rejected(self, r: int, g: int, b: int):
        """Un canal < 0 debe lanzar ValueError."""
        with pytest.raises(ValueError):
            RGBColor(r, g, b)

    @given(color=rgb_color)
    def test_hex_is_always_7_chars(self, color: RGBColor):
        """El hex siempre tiene 7 caracteres (#RRGGBB)."""
        hex_str = color.to_hex()
        assert len(hex_str) == 7
        assert hex_str.startswith("#")

    @given(color=rgb_color)
    def test_rgb_tuple_preserves_values(self, color: RGBColor):
        """to_rgb_tuple() preserva los valores exactos."""
        r, g, b = color.to_rgb_tuple()
        assert r == color.r
        assert g == color.g
        assert b == color.b


class TestRGBColorInterpolation:

    @given(c1=rgb_color, c2=rgb_color)
    def test_interpolate_at_0_returns_c1(self, c1: RGBColor, c2: RGBColor):
        """t=0 devuelve el primer color."""
        result = RGBColor.interpolate(c1, c2, 0.0)
        assert result == c1

    @given(c1=rgb_color, c2=rgb_color)
    def test_interpolate_at_1_returns_c2(self, c1: RGBColor, c2: RGBColor):
        """t=1 devuelve el segundo color."""
        result = RGBColor.interpolate(c1, c2, 1.0)
        assert result == c2

    @given(c1=rgb_color, c2=rgb_color, t=interpolation_factor)
    def test_interpolate_channels_within_bounds(
        self, c1: RGBColor, c2: RGBColor, t: float
    ):
        """Cualquier canal del resultado está en [0, 255]."""
        result = RGBColor.interpolate(c1, c2, t)
        assert 0 <= result.r <= 255
        assert 0 <= result.g <= 255
        assert 0 <= result.b <= 255

    @given(c1=rgb_color, c2=rgb_color, t=interpolation_factor)
    def test_interpolate_is_between_c1_and_c2(
        self, c1: RGBColor, c2: RGBColor, t: float
    ):
        """Cada canal está entre los valores de c1 y c2."""
        result = RGBColor.interpolate(c1, c2, t)

        for channel_r, a, b in [
            (result.r, c1.r, c2.r),
            (result.g, c1.g, c2.g),
            (result.b, c1.b, c2.b),
        ]:
            low, high = min(a, b), max(a, b)
            # Margen por redondeo
            assert low - 1 <= channel_r <= high + 1

    @given(c1=rgb_color, c2=rgb_color, t=interpolation_factor)
    def test_interpolate_is_symmetric_in_direction(
        self, c1: RGBColor, c2: RGBColor, t: float
    ):
        """
        Interpolar c1→c2 con t equivale a interpolar c2→c1 con (1-t).
        """
        forward = RGBColor.interpolate(c1, c2, t)
        backward = RGBColor.interpolate(c2, c1, 1.0 - t)

        # Margen por redondeo int()
        assert abs(forward.r - backward.r) <= 1
        assert abs(forward.g - backward.g) <= 1
        assert abs(forward.b - backward.b) <= 1