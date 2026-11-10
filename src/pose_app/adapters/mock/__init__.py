"""
Adaptadores mock para testing.
"""

from pose_app.adapters.mock.mock_camera import MockCameraAdapter
from pose_app.adapters.mock.mock_pose import MockPoseAdapter
from pose_app.adapters.mock.mock_render import (
    MockColorRenderAdapter,
    MockParticlesRenderAdapter,
    MockSceneManager,
)

__all__ = [
    "MockCameraAdapter",
    "MockColorRenderAdapter",
    "MockParticlesRenderAdapter",
    "MockPoseAdapter",
    "MockSceneManager",
]
