"""
Paquete de puertos (interfaces) del dominio.
Los puertos definen los contratos que los adaptadores deben cumplir.
"""

from pose_app.domain.ports.camera_port import CameraPort
from pose_app.domain.ports.pose_estimator_port import PoseEstimatorPort
from pose_app.domain.ports.render_port import (
    BaseRenderPort,
    ColorRenderPort,
    ParticlesRenderPort,
)

__all__ = [
    "BaseRenderPort",
    "CameraPort",
    "ColorRenderPort",
    "ParticlesRenderPort",
    "PoseEstimatorPort",
]
