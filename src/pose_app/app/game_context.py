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
from typing import TYPE_CHECKING

from pose_app.config.settings import Settings
from pose_app.domain.ports.camera_port import CameraPort
from pose_app.domain.ports.event_bus_port import EventBusPort
from pose_app.domain.ports.pose_estimator_port import PoseEstimatorPort

if TYPE_CHECKING:
    from pose_app.config.game_profile import GameProfileConfig


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
    gameplay_config: "GameProfileConfig"
