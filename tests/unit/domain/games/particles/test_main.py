# tests/unit/test_particles_game.py

"""
Tests unitarios de ParticlesGame con la nueva arquitectura.
"""

import random
from unittest.mock import Mock

import pytest

from pose_app.domain.entities.particles.archetype import ParticleArchetype
from pose_app.domain.entities.particles.components import (
    Appearance,
    Position,
)
from pose_app.domain.entities.particles.spawn.positions import RandomPositionStrategy
from pose_app.domain.entities.particles.spawn.selectors import WeightedSelector
from pose_app.domain.entities.particles.spawn.strategies import ComposedSpawnStrategy
from pose_app.domain.games.particles.main import ParticlesGame
from pose_app.domain.games.particles.state import ParticlesState
from pose_app.domain.ports.pose_interaction_port import PoseInteractionPort
from pose_app.domain.ports.render.color_render_port import ColorRenderPort
from pose_app.domain.ports.render.hud_render_port import HudRenderPort
from pose_app.domain.ports.render.particles_render_port import ParticlesRenderPort
from pose_app.infrastructure.events.async_event_bus import AsyncEventBus


class MockScene:
    """Mock de ScenePort."""

    def __init__(self) -> None:
        self.render_count = 0
        self.closed = False

    def add_capability(self, cap):
        pass

    def add_overlay(self, ov):
        pass

    def render_frame(self, landmarks):
        self.render_count += 1

    def close(self):
        self.closed = True


@pytest.fixture
def game() -> ParticlesGame:
    """Game con mocks."""
    spawn_strategy = ComposedSpawnStrategy(
        archetype_selector=WeightedSelector(),
        position_strategy=RandomPositionStrategy(min_distance=0.15),
    )

    archetypes = [
        ParticleArchetype(
            name="test",
            appearance=Appearance(size=20.0, color=(255, 200, 50)),
        )
    ]

    return ParticlesGame(
        camera=Mock(),
        pose_estimator=Mock(),
        scene=MockScene(),
        pose_interaction=Mock(spec=PoseInteractionPort),
        particles_capability=Mock(spec=ParticlesRenderPort),
        color_capability=Mock(spec=ColorRenderPort),
        hud_capability=Mock(spec=HudRenderPort),
        state=ParticlesState(),
        event_bus=AsyncEventBus(),
        spawn_strategy=spawn_strategy,
        archetypes=archetypes,
        rng=random.Random(42),
    )


class TestParticlesGameInit:
    def test_game_creates_particles_on_start(self, game: ParticlesGame):
        """Al iniciar ronda, se generan partículas."""
        game._start_new_round()
        assert len(game._particles) > 0

    def test_first_round_has_2_particles(self, game: ParticlesGame):
        """Ronda 1 → 2 partículas."""
        game._start_new_round()
        assert len(game._particles) == 2

    def test_state_reflects_particles(self, game: ParticlesGame):
        """El estado refleja el número de partículas."""
        game._start_new_round()
        snapshot = game.state.snapshot()
        assert snapshot["particles_count"] == len(game._particles)


class TestParticlesGameCompleteRound:
    def test_complete_round_increments_score(self, game: ParticlesGame):
        """Completar ronda suma 1 punto."""
        game._start_new_round()
        game._particles.clear()  # simula que todas fueron tocadas
        game._complete_round()
        assert game.state.get_score() == 1

    def test_complete_round_starts_new_round(self, game: ParticlesGame):
        """Completar ronda inicia la siguiente."""
        game._start_new_round()
        game._particles.clear()
        game._complete_round()
        assert len(game._particles) > 0  # nueva ronda tiene partículas
        assert game._current_round == 2

    def test_winning_condition(self, game: ParticlesGame):
        """Alcanzar max_score → game over."""
        game._max_score = 2
        # Ronda 1
        game._start_new_round()
        game._particles.clear()
        game._complete_round()
        # Ronda 2
        game._particles.clear()
        game._complete_round()
        assert game.state.is_game_over() is True
        assert game.state.is_winner() is True


# tests/unit/test_particles_game.py


class TestParticlesGameLogic:
    def test_landmarks_hit_particles(self, game: ParticlesGame) -> None:
        """Un landmark visible toca partículas cercanas."""
        from pose_app.domain.entities.particle import Particle
        from pose_app.domain.entities.pose_landmark import PoseLandmark

        game._start_new_round()
        initial_score = game.state.get_score()
        initial_round = game._current_round

        # Coloca una partícula en el centro
        game._particles = [
            Particle(
                position=Position(x=400, y=300),
                appearance=Appearance(size=20.0),
            )
        ]

        landmarks = [
            PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="left_wrist")
        ]

        # 1. Alimentar la fachada (simula lo que hace el bucle principal)
        game._pose_interaction.update(landmarks)

        # 2. Ejecutar la lógica (ahora solo recibe dt)
        game._update_logic(dt=0.016)

        # Assert: la partícula debería haber sido tocada y eliminada
        assert game.state.get_score() == initial_score + 1
        assert game._current_round == initial_round + 1


class TestParticlesGameRender:
    @pytest.mark.asyncio
    async def test_render_updates_capabilities(self, game: ParticlesGame):
        """Render llama a las capacidades con datos actualizados."""
        game._start_new_round()
        await game._render_frame(landmarks=[])

        game._color_capability.set_color.assert_called()
        game._particles_capability.set_particles.assert_called()
        game._hud_capability.set_hud.assert_called()

        # Verificar que la escena también fue renderizada
        assert game._scene.render_count > 0
