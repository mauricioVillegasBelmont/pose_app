# domain/events/pose_events.py

from dataclasses import dataclass

from domain.entities.pose_landmark import PoseLandmark
from domain.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class PoseUpdated(DomainEvent):
    landmarks: tuple[PoseLandmark, ...]
    frame_id: int = 0


@dataclass(frozen=True, kw_only=True)
class PoseLost(DomainEvent):
    frame_id: int = 0
