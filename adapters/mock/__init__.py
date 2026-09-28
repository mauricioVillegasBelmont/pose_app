"""
Adaptadores mock para testing.
"""

from adapters.mock.mock_camera import MockCameraAdapter
from adapters.mock.mock_pose import MockPoseAdapter
from adapters.mock.mock_render import (
    MockColorRenderAdapter,
    MockParticlesRenderAdapter,
)

__all__ = [
    "MockCameraAdapter",
    "MockColorRenderAdapter",
    "MockParticlesRenderAdapter",
    "MockPoseAdapter",
]