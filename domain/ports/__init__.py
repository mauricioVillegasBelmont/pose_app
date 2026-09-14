"""
Paquete de puertos (interfaces) del dominio.
Los puertos definen los contratos que los adaptadores deben cumplir.
"""

from domain.ports.camera_port import CameraPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import RenderPort

__all__ = [
    'CameraPort',
    'PoseEstimatorPort',
    'RenderPort',
]