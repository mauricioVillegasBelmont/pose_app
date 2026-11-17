"""Tests de ParticleArchetype (refactor: compone Appearance)."""

from dataclasses import FrozenInstanceError

import pytest

from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.components import Appearance, SpriteConfig


class TestParticleArchetypeComposition:
    """El archetype compone un Appearance completo."""

    def test_archetype_creation_with_defaults(self) -> None:
        """Defaults: appearance con size=20, color=(255,200,50), weight=1.0."""
        arch = ParticleArchetype(name="default")

        assert arch.name == "default"
        assert arch.weight == 1.0
        assert arch.appearance.size == 20.0
        assert arch.appearance.color == (255, 200, 50)
        assert arch.appearance.padding_x == 0.0
        assert arch.appearance.padding_y == 0.0
        assert arch.sprite_config is None

    def test_archetype_creation_with_custom_appearance(self) -> None:
        """Acepta un Appearance custom (frozen, compartible)."""
        appearance = Appearance(
            size=32.0,
            color=(255, 80, 0),
            padding_x=4.0,
            padding_y=4.0,
        )
        arch = ParticleArchetype(name="fire", appearance=appearance, weight=3.0)

        assert arch.appearance is appearance  # misma instancia (frozen, seguro)
        assert arch.appearance.size == 32.0
        assert arch.appearance.color == (255, 80, 0)
        assert arch.appearance.padding_x == 4.0
        assert arch.appearance.padding_y == 4.0

    def test_archetype_with_sprite_config(self) -> None:
        """Acepta sprite_config opcional."""
        sprite = SpriteConfig(
            path="demo.png",
            frame_width=32,
            frame_height=32,
            frame_count=4,
            fps=12.0,
            animation_mode="loop",
        )
        arch = ParticleArchetype(name="bomb", sprite_config=sprite)

        assert arch.sprite_config is sprite


class TestParticleArchetypeValidation:
    """Validaciones de invariantes."""

    def test_archetype_rejects_empty_name(self) -> None:
        """name vacío lanza ValueError."""
        with pytest.raises(ValueError, match="name must not be empty"):
            ParticleArchetype(name="")

    def test_archetype_rejects_negative_weight(self) -> None:
        """weight negativo lanza ValueError."""
        with pytest.raises(ValueError, match="weight must be non-negative"):
            ParticleArchetype(name="x", weight=-1.0)

    def test_archetype_is_immutable(self) -> None:
        """ParticleArchetype es frozen."""
        arch = ParticleArchetype(name="x")
        with pytest.raises(FrozenInstanceError):
            arch.name = "y"  # type: ignore[misc]

    def test_archetype_appearance_is_shared_and_frozen(self) -> None:
        """Dos archetypes pueden compartir el mismo Appearance (frozen)."""
        shared = Appearance(size=20.0, color=(255, 0, 0))
        arch1 = ParticleArchetype(name="a", appearance=shared)
        arch2 = ParticleArchetype(name="b", appearance=shared)

        assert arch1.appearance is arch2.appearance
        # Appearance es frozen → no se puede mutar desde un archetype
        with pytest.raises(FrozenInstanceError):
            arch1.appearance.size = 30.0  # type: ignore[misc]
