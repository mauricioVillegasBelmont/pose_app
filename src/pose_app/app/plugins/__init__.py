"""
Registro central de plugins.

Añadir un plugin nuevo = importar y registrar aquí.
Este es el ÚNICO punto del núcleo que conoce plugins concretos.

Filosofía: "explícito + centralizado" en lugar de auto-discovery.
"""

from pose_app.app.plugin_registry import PluginRegistry
from pose_app.infrastructure.logging.logger import get_logger

logger = get_logger("app.plugins")


def register_builtin_plugins(registry: PluginRegistry) -> None:
    """
    Registra todos los plugins incluidos en el proyecto.

    Para añadir un plugin:
        1. Crear `app/plugins/<nombre>_plugin.py`
        2. Importarlo aquí (dentro de la función, para evitar ciclos)
        3. Llamar a `registry.register(<Nombre>Plugin())`
    """
    # Imports locales para evitar ciclos en startup
    from pose_app.app.plugins.color_plugin import ColorPlugin
    from pose_app.app.plugins.gestures_plugin import GesturesPlugin
    from pose_app.app.plugins.particles_plugin import ParticlesPlugin

    registry.register(ParticlesPlugin())
    registry.register(ColorPlugin())
    registry.register(GesturesPlugin())

    logger.info(f"Plugins builtin registrados: {registry.list_ids()}")
