"""
Tests para validar que las rutas globales se resuelven correctamente.
"""

from pose_app.infrastructure.paths import ASSETS_DIR, PROJECT_ROOT


def test_project_root_contains_pyproject() -> None:
    """El PROJECT_ROOT debe contener el archivo pyproject.toml."""
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_assets_dir_exists() -> None:
    """El directorio de assets debe existir."""
    assert ASSETS_DIR.exists()
    assert ASSETS_DIR.is_dir()


def test_assets_dir_is_child_of_project_root() -> None:
    """ASSETS_DIR debe estar dentro de PROJECT_ROOT."""
    assert ASSETS_DIR == PROJECT_ROOT / "assets"
