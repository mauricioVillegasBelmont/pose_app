"""
Tests para ParticleArchetype, el Value Object que define el ADN de un tipo
de partícula.
"""

import pytest

from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.components import SpriteConfig


def test_archetype_creation_with_defaults() -> None:
    """Crea un arquetipo con solo el nombre y aplica los valores por defecto."""
    archetype = ParticleArchetype(name="spark")

    assert archetype.name == "spark"
    assert archetype.weight == 1.0
    assert archetype.size == 20.0
    assert archetype.color == (255, 200, 50)
    assert archetype.sprite_config is None


def test_archetype_creation_with_custom_values() -> None:
    """Crea un arquetipo con todos los campos escalares personalizados."""
    archetype = ParticleArchetype(
        name="blood",
        weight=2.5,
        size=64.0,
        color=(200, 0, 0),
    )

    assert archetype.name == "blood"
    assert archetype.weight == 2.5
    assert archetype.size == 64.0
    assert archetype.color == (200, 0, 0)


def test_archetype_with_sprite_config() -> None:
    """Un arquetipo puede referenciar una configuración de sprite compartida."""
    sprite_config = SpriteConfig(
        path="blood-curse.png",
        frame_width=128.0,
        frame_height=128.0,
        frame_count=16,
        fps=12.0,
    )

    archetype = ParticleArchetype(name="blood", sprite_config=sprite_config)

    assert archetype.sprite_config is sprite_config
    assert archetype.sprite_config.frame_count == 16


def test_archetype_rejects_empty_name() -> None:
    """Un arquetipo sin nombre no es identificable."""
    with pytest.raises(ValueError, match="name must not be empty"):
        ParticleArchetype(name="")


def test_archetype_rejects_negative_weight() -> None:
    """Un peso negativo rompería el spawn aleatorio."""
    with pytest.raises(ValueError, match="weight must be non-negative"):
        ParticleArchetype(name="spark", weight=-0.1)


def test_archetype_rejects_zero_size() -> None:
    """Un tamaño cero no es renderizable."""
    with pytest.raises(ValueError, match="size must be positive"):
        ParticleArchetype(name="spark", size=0.0)


def test_archetype_rejects_negative_size() -> None:
    """Un tamaño negativo no tiene sentido físico."""
    with pytest.raises(ValueError, match="size must be positive"):
        ParticleArchetype(name="spark", size=-10.0)


def test_archetype_rejects_invalid_color_length() -> None:
    """El color debe tener exactamente tres componentes."""
    with pytest.raises(
        ValueError, match="color must be a tuple of 3 integers in range 0-255"
    ):
        ParticleArchetype(name="spark", color=(255, 255))  # type: ignore[arg-type]


@pytest.mark.parametrize("color", [(256, 0, 0), (-1, 0, 0)])
def test_archetype_rejects_color_out_of_range(
    color: tuple[int, int, int],
) -> None:
    """Cada componente RGB debe estar en el rango 0-255."""
    with pytest.raises(
        ValueError, match="color must be a tuple of 3 integers in range 0-255"
    ):
        ParticleArchetype(name="spark", color=color)


def test_archetype_is_immutable() -> None:
    """ParticleArchetype es un Value Object frozen."""
    archetype = ParticleArchetype(name="spark")

    with pytest.raises(AttributeError):
        archetype.name = "other"  # type: ignore[misc]
