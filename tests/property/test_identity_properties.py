"""
Property-based tests para Identity.
"""

from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st

from domain.entities.identity import Identity

# ==========================================
# Strategies
# ==========================================

provider_strategy = st.sampled_from(["password", "google", "github", "facebook"])

identity_strategy = st.builds(
    Identity,
    user_id=st.uuids().map(str),
    provider=provider_strategy,
    provider_user_id=st.text(min_size=1, max_size=50),
    password_hash=st.one_of(st.none(), st.text(min_size=20, max_size=60)),
)


# ==========================================
# Propiedades
# ==========================================


class TestIdentityInvariants:
    @given(identity=identity_strategy)
    def test_is_password_matches_provider(self, identity: Identity):
        """is_password == (provider == 'password')."""
        assert identity.is_password == (identity.provider == "password")

    @given(identity=identity_strategy)
    def test_with_last_login_sets_timestamp(self, identity: Identity):
        """with_last_login actualiza el timestamp."""
        updated = identity.with_last_login()
        assert updated.last_login_at is not None
        assert isinstance(updated.last_login_at, datetime)
        assert updated.last_login_at.tzinfo is not None  # UTC

    @given(identity=identity_strategy)
    def test_with_last_login_preserves_immutability(self, identity: Identity):
        """with_last_login no muta la identidad original."""
        original = identity.last_login_at
        identity.with_last_login()
        assert identity.last_login_at == original

    @given(identity=identity_strategy)
    def test_with_last_login_preserves_other_fields(self, identity: Identity):
        """with_last_login solo cambia last_login_at."""
        updated = identity.with_last_login()
        assert updated.user_id == identity.user_id
        assert updated.provider == identity.provider
        assert updated.provider_user_id == identity.provider_user_id
        assert updated.password_hash == identity.password_hash
        assert updated.created_at == identity.created_at
