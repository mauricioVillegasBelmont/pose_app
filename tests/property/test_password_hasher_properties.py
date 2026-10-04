"""
Property-based tests para el módulo password_hasher.

IMPORTANTE: estos tests son lentos (~250ms por bcrypt).
Bajar `max_examples` para velocidad.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from adapters.auth.password_hasher import (
    hash_password,
    verify_dummy_password,
    verify_password,
)

# Estrategia: passwords válidos (8-72 chars)
password_strategy = st.text(min_size=8, max_size=72)


class TestPasswordHasherProperties:
    @given(password=password_strategy)
    @settings(max_examples=10, deadline=None)  # bcrypt es lento
    def test_hash_verify_roundtrip(self, password: str):
        """hash_password → verify_password siempre True."""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    @given(
        password=password_strategy,
        wrong_password=password_strategy,
    )
    @settings(max_examples=10, deadline=None)
    def test_different_password_fails(self, password: str, wrong_password: str):
        """Un password distinto NO verifica."""
        # Asume que son distintos
        if password == wrong_password:
            return

        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    @given(password=password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_hash_is_unique_per_call(self, password: str):
        """Dos hashes del mismo password son distintos (salt aleatorio)."""
        h1 = hash_password(password)
        h2 = hash_password(password)
        assert h1 != h2
        # Pero ambos verifican
        assert verify_password(password, h1)
        assert verify_password(password, h2)

    @given(password=password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_verify_dummy_never_raises(self, password: str):
        """verify_dummy_password nunca lanza excepción."""
        verify_dummy_password(password)  # No debe explotar

    @given(password=st.text(min_size=100, max_size=200))
    @settings(max_examples=10, deadline=None)
    def test_hash_handles_long_passwords(self, password: str):
        """Passwords largos se truncan a 72 bytes (bcrypt limit)."""
        hashed = hash_password(password)
        # La verificación usa el mismo truncamiento
        assert verify_password(password, hashed)
