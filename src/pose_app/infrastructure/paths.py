"""
Constantes de rutas globales del proyecto.
Evita el anti-patrón de usar Path(__file__).parent.parent.parent...
"""

from pathlib import Path

# __file__ es la ruta de ESTE archivo: .../src/pose_app/infrastructure/paths.py
# .resolve() convierte la ruta a absoluta.
# .parents[3] sube 3 niveles:
#   [0] -> infrastructure
#   [1] -> pose_app
#   [2] -> src
#   [3] -> project_root (donde está pyproject.toml)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Directorio de assets en la raíz del proyecto
ASSETS_DIR = PROJECT_ROOT / "assets"
