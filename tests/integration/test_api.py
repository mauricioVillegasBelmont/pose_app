"""
Tests de integración de la API usando TestClient.
"""

from fastapi.testclient import TestClient

from adapters.api.fastapi_adapter import FastAPIAdapter
from app.state import AppState
from config.settings import APISettings


def test_health_endpoint():
    """Verifica que /health responda correctamente."""
    state = AppState()
    adapter = FastAPIAdapter(
        settings=APISettings(enabled=True, host="127.0.0.1", port=8001),
        state=state,
    )
    client = TestClient(adapter.app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_state_endpoint():
    """Verifica que /state devuelva el snapshot."""
    state = AppState()
    adapter = FastAPIAdapter(
        settings=APISettings(enabled=True),
        state=state,
    )
    client = TestClient(adapter.app)

    response = client.get("/api/v1/state")

    assert response.status_code == 200
    data = response.json()
    assert "pose" in data
    assert "particles" in data
    assert "stats" in data


def test_reset_particles_command():
    """Verifica que el comando de reset se encole."""
    state = AppState()
    adapter = FastAPIAdapter(
        settings=APISettings(enabled=True),
        state=state,
    )
    client = TestClient(adapter.app)

    response = client.post("/api/v1/commands/reset-particles")

    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] is True

    # Verifica que el comando esté en la cola
    commands = state.drain_commands()
    assert len(commands) == 1
    assert commands[0].action == "reset_particles"


def test_change_palette_command():
    """Verifica que cambiar paleta funcione."""
    state = AppState()
    adapter = FastAPIAdapter(
        settings=APISettings(enabled=True),
        state=state,
    )
    client = TestClient(adapter.app)

    response = client.post(
        "/api/v1/commands/change-palette",
        json={"palette": "ocean"}
    )

    assert response.status_code == 200
    assert state.get_current_palette() == "ocean"