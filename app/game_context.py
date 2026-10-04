"""
Contexto de construcción de un juego.

Contiene las dependencias COMPARTIDAS que el Container provee al plugin.
El plugin decide cómo usarlas para construir su juego.

Motivación:
- Evita firmas largas (create_game(camera, pose, bus, settings, ...)).
- Extensible: añadir un campo no rompe plugins existentes.
- Explícito: el plugin ve claramente qué puede usar.
"""

from dataclasses import dataclass

from config.settings import Settings
from domain.ports.camera_port import CameraPort
from domain.ports.event_bus_port import EventBusPort
from domain.ports.pose_estimator_port import PoseEstimatorPort


@dataclass(frozen=True)
class GameContext:
    """
    Dependencias compartidas que el Container pasa al plugin.

    El plugin NO debe guardar referencias globales a esto;
    solo lo usa durante `create_game()`.
    """

    camera: CameraPort
    pose_estimator: PoseEstimatorPort
    event_bus: EventBusPort
    settings: Settings
