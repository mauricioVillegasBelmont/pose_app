# tests/unit/test_state_generic.py

from app.state import AppState


def test_state_is_generic():
    """El estado no conoce partículas ni colores."""
    state = AppState()

    # Publicar datos arbitrarios
    state.update_game_data("particles", [])
    state.update_game_data("background_color", {"r": 255, "g": 0, "b": 0})
    state.update_game_data("cualquier_cosa", 42)

    snapshot = state.get_snapshot()

    assert "game_data" in snapshot
    assert snapshot["game_data"]["cualquier_cosa"] == 42


def test_commands_are_generic():
    """Los comandos son strings + dict, sin acoplamiento."""
    state = AppState()

    state.enqueue_command("cualquier_comando", {"foo": "bar"})
    state.enqueue_command("otro_comando", {})

    commands = state.drain_commands()

    assert len(commands) == 2
    assert commands[0].action == "cualquier_comando"
    assert commands[0].payload == {"foo": "bar"}


def test_unknown_commands_dont_crash():
    """Comandos desconocidos no rompen nada (los juegos los ignoran)."""
    state = AppState()
    state.enqueue_command("comando_del_futuro", {"x": 1})

    # El juego actual simplemente no lo procesa
    commands = state.drain_commands()
    assert len(commands) == 1
    # El juego decide ignorarlo, no el estado