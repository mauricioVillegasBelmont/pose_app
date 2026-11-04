"""
Tests para los selectores de arquetipos del sistema de spawn.
"""

import random

import pytest

from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.spawn.selectors import (
    SequentialSelector,
    WeightedSelector,
)


class TestWeightedSelector:
    """WeightedSelector elige arquetipos según su peso relativo."""

    def test_selects_archetype_from_list(self) -> None:
        """El arquetipo devuelto pertenece a la lista recibida."""
        archetypes = [
            ParticleArchetype(name="spark", weight=1.0),
            ParticleArchetype(name="blood", weight=2.0),
        ]

        selected = WeightedSelector().select(archetypes, random.Random(42))

        assert selected in archetypes

    def test_respects_weight_distribution(self) -> None:
        """Con pesos 90/10, la distribución se aproxima a esa proporción."""
        common = ParticleArchetype(name="common", weight=90.0)
        rare = ParticleArchetype(name="rare", weight=10.0)
        selector = WeightedSelector()
        rng = random.Random(42)

        selections = [selector.select([common, rare], rng) for _ in range(1000)]
        common_ratio = selections.count(common) / len(selections)

        assert common_ratio == pytest.approx(0.9, abs=0.05)
        assert (1.0 - common_ratio) == pytest.approx(0.1, abs=0.05)

    def test_single_archetype_always_selected(self) -> None:
        """Con un único arquetipo, siempre se selecciona ese."""
        archetype = ParticleArchetype(name="solo")
        selector = WeightedSelector()
        rng = random.Random(42)

        selections = [selector.select([archetype], rng) for _ in range(20)]

        assert all(selected is archetype for selected in selections)

    def test_zero_weight_never_selected(self) -> None:
        """Un arquetipo con peso 0 nunca se elige si hay otro positivo."""
        never = ParticleArchetype(name="never", weight=0.0)
        always = ParticleArchetype(name="always", weight=1.0)
        selector = WeightedSelector()
        rng = random.Random(42)

        selections = [selector.select([never, always], rng) for _ in range(100)]

        assert all(selected is always for selected in selections)

    def test_rejects_empty_archetypes(self) -> None:
        """Una lista vacía no permite seleccionar nada."""
        with pytest.raises(
            ValueError,
            match="WeightedSelector requires at least one archetype",
        ):
            WeightedSelector().select([], random.Random(42))

    def test_rejects_all_zero_weights(self) -> None:
        """Si todos los pesos son 0, no hay distribución posible."""
        archetypes = [
            ParticleArchetype(name="a", weight=0.0),
            ParticleArchetype(name="b", weight=0.0),
        ]

        with pytest.raises(
            ValueError,
            match="WeightedSelector requires at least one archetype with positive weight",
        ):
            WeightedSelector().select(archetypes, random.Random(42))


class TestSequentialSelector:
    """SequentialSelector recorre una secuencia de nombres de forma cíclica."""

    def test_selects_in_sequence_order(self) -> None:
        """Los arquetipos se seleccionan en el orden declarado."""
        alpha = ParticleArchetype(name="alpha")
        beta = ParticleArchetype(name="beta")
        gamma = ParticleArchetype(name="gamma")
        selector = SequentialSelector(sequence=["alpha", "beta", "gamma"])
        rng = random.Random(42)

        selected_names = [
            selector.select([alpha, beta, gamma], rng).name for _ in range(3)
        ]

        assert selected_names == ["alpha", "beta", "gamma"]

    def test_cycles_back_to_start(self) -> None:
        """Al agotar la secuencia, vuelve al primer nombre."""
        alpha = ParticleArchetype(name="alpha")
        beta = ParticleArchetype(name="beta")
        selector = SequentialSelector(sequence=["alpha", "beta"])
        rng = random.Random(42)

        selected_names = [selector.select([alpha, beta], rng).name for _ in range(5)]

        assert selected_names == ["alpha", "beta", "alpha", "beta", "alpha"]

    def test_rejects_empty_sequence(self) -> None:
        """Una secuencia vacía no tiene ningún nombre que recorrer."""
        with pytest.raises(
            ValueError,
            match="SequentialSelector sequence must not be empty",
        ):
            SequentialSelector(sequence=[])

    def test_rejects_unknown_archetype_name(self) -> None:
        """Si el nombre de la secuencia no existe, se lanza un error."""
        selector = SequentialSelector(sequence=["missing"])

        with pytest.raises(
            ValueError,
            match="SequentialSelector: archetype 'missing' not found in archetypes list",
        ):
            selector.select(
                [ParticleArchetype(name="present")],
                random.Random(42),
            )

    def test_rejects_empty_archetypes_list(self) -> None:
        """No se puede seleccionar si no hay arquetipos candidatos."""
        selector = SequentialSelector(sequence=["alpha"])

        with pytest.raises(
            ValueError,
            match="SequentialSelector requires at least one archetype",
        ):
            selector.select([], random.Random(42))

    def test_rng_parameter_is_ignored(self) -> None:
        """La selección es determinista independientemente del rng."""
        alpha = ParticleArchetype(name="alpha")
        beta = ParticleArchetype(name="beta")
        selector = SequentialSelector(sequence=["alpha", "beta"])

        first = selector.select([alpha, beta], random.Random(1))
        second = selector.select([alpha, beta], random.Random(999))

        assert first is alpha
        assert second is beta
