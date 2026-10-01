"""
Property-based tests para PoseLandmark.
"""

from hypothesis import given
from hypothesis import strategies as st

from domain.entities.pose_landmark import PoseLandmark

# ==========================================
# Strategies
# ==========================================

# Coordenadas normalizadas
normalized_coord = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)

visibility = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)

pose_landmark = st.builds(
    PoseLandmark,
    x=normalized_coord,
    y=normalized_coord,
    z=st.floats(min_value=-1.0, max_value=1.0, allow_nan=False),
    visibility=visibility,
    name=st.sampled_from([None, "nose", "left_wrist", "right_ankle"]),
)


# ==========================================
# Propiedades
# ==========================================

class TestPoseLandmarkDistance:

    @given(lm=pose_landmark)
    def test_distance_to_self_is_zero(self, lm: PoseLandmark):
        """La distancia a sí mismo es 0."""
        assert lm.distance_to(lm) == 0.0

    @given(a=pose_landmark, b=pose_landmark)
    def test_distance_is_symmetric(self, a: PoseLandmark, b: PoseLandmark):
        """distance_to es simétrica."""
        assert a.distance_to(b) == b.distance_to(a)

    @given(a=pose_landmark, b=pose_landmark)
    def test_distance_is_non_negative(
        self, a: PoseLandmark, b: PoseLandmark
    ):
        """La distancia siempre es >= 0."""
        assert a.distance_to(b) >= 0.0

    @given(a=pose_landmark, b=pose_landmark)
    def test_distance_bounded_by_diagonal(
        self, a: PoseLandmark, b: PoseLandmark
    ):
        """
        En un espacio normalizado [0,1]x[0,1], la distancia máxima es sqrt(2).
        """
        import math
        assert a.distance_to(b) <= math.sqrt(2) + 1e-9


class TestPoseLandmarkVisibility:

    @given(
        visibility=st.floats(
            min_value=0.6, max_value=1.0, allow_nan=False
        )
    )
    def test_high_visibility_is_visible(self, visibility: float):
        """visibility > 0.5 → is_visible() == True."""
        lm = PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=visibility)
        assert lm.is_visible() is True

    @given(
        visibility=st.floats(
            min_value=0.0, max_value=0.5, allow_nan=False
        )
    )
    def test_low_visibility_is_not_visible(self, visibility: float):
        """visibility <= 0.5 → is_visible() == False."""
        lm = PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=visibility)
        assert lm.is_visible() is False