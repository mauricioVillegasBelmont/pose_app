"""
Property-based tests para la entidad User.

Verifican invariantes de roles, inmutabilidad y métodos with_*.
"""

from hypothesis import given
from hypothesis import strategies as st

from domain.entities.user import User

# ==========================================
# Strategies
# ==========================================

# Roles válidos
role_strategy = st.sampled_from(["user", "admin", "moderator", "guest", "editor"])

# Username válido
username_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
    min_size=1,
    max_size=20,
).filter(lambda s: s[0].isalpha())

# Email opcional
email_strategy = st.one_of(
    st.none(),
    st.emails(),
)

# Estrategia completa
user_strategy = st.builds(
    User,
    username=username_strategy,
    email=email_strategy,
    full_name=st.one_of(st.none(), st.text(max_size=50)),
    roles=st.tuples(role_strategy) | st.just(()),
    disabled=st.booleans(),
)


# ==========================================
# Propiedades
# ==========================================


class TestUserRoleInvariants:
    @given(user=user_strategy)
    def test_has_role_reflects_roles_tuple(self, user: User):
        """has_role(r) == (r in user.roles) para todo rol."""
        for role in user.roles:
            assert user.has_role(role) is True

    @given(user=user_strategy)
    def test_has_role_false_for_unknown_roles(self, user: User):
        """has_role(r) == False para roles que no están."""
        unknown_roles = {"nonexistent_role_xyz", "fake", "unknown123"}
        for role in unknown_roles - set(user.roles):
            assert user.has_role(role) is False

    @given(user=user_strategy)
    def test_is_admin_consistent_with_has_role(self, user: User):
        """is_admin() == has_role('admin')."""
        assert user.is_admin() == user.has_role("admin")


class TestUserImmutability:
    @given(user=user_strategy, new_email=st.emails())
    def test_with_email_creates_new_instance(self, user: User, new_email: str):
        """with_email devuelve una instancia nueva sin mutar la original."""
        updated = user.with_email(new_email)
        assert updated is not user
        assert updated.email == new_email
        assert user.email != new_email or user.email == new_email

    @given(user=user_strategy, new_name=st.text(max_size=50))
    def test_with_full_name_creates_new_instance(self, user: User, new_name: str):
        """with_full_name devuelve nueva instancia."""
        updated = user.with_full_name(new_name)
        assert updated is not user
        assert updated.full_name == new_name

    @given(user=user_strategy, new_roles=st.tuples(role_strategy))
    def test_with_roles_creates_new_instance(
        self, user: User, new_roles: tuple[str, ...]
    ):
        """with_roles devuelve nueva instancia."""
        updated = user.with_roles(new_roles)
        assert updated is not user
        assert updated.roles == new_roles

    @given(user=user_strategy, new_disabled=st.booleans())
    def test_with_disabled_creates_new_instance(self, user: User, new_disabled: bool):
        """with_disabled devuelve nueva instancia."""
        updated = user.with_disabled(new_disabled)
        assert updated is not user
        assert updated.disabled == new_disabled

    @given(user=user_strategy)
    def test_original_user_unchanged_after_with(self, user: User):
        """Los métodos with_* no mutan el User original."""
        original_id = user.id
        original_username = user.username
        original_roles = user.roles

        user.with_email("changed@x.com")
        user.with_full_name("Changed")
        user.with_roles(("changed_role",))
        user.with_disabled(not user.disabled)

        assert user.id == original_id
        assert user.username == original_username
        assert user.roles == original_roles


class TestUserId:
    @given(username=username_strategy)
    def test_id_is_generated_automatically(self, username: str):
        """Cada User recibe un id único por defecto."""
        u1 = User(username=username)
        u2 = User(username=username)
        assert u1.id != u2.id

    @given(username=username_strategy, custom_id=st.uuids().map(str))
    def test_id_can_be_provided(self, username: str, custom_id: str):
        """Se puede especificar un id manualmente."""
        user = User(username=username, id=custom_id)
        assert user.id == custom_id
