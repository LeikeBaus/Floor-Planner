"""Wall domain model and related enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import atan2, dist, hypot
from uuid import uuid4

from geometry.point import Point


class WallType(StrEnum):
    """Classification for wall semantics and default styling/rules."""

    EXTERIOR = "EXTERIOR"
    INTERIOR = "INTERIOR"


@dataclass(slots=True)
class Wall:
    """Represents a wall centerline with thickness in millimeters."""

    start: Point
    end: Point
    thickness: float
    wall_type: WallType
    locked: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def length(self) -> float:
        """Return wall length in millimeters."""
        return dist((self.start.x, self.start.y), (self.end.x, self.end.y))

    @property
    def angle(self) -> float:
        """Return wall angle in radians in world coordinate system."""
        return atan2(self.end.y - self.start.y, self.end.x - self.start.x)

    @property
    def center(self) -> Point:
        """Return center point of the wall segment."""
        return Point(x=(self.start.x + self.end.x) / 2.0, y=(self.start.y + self.end.y) / 2.0)
    
    @property
    def corners(self) -> list[Point]:
        """Calculate the four corner points of the wall rectangle."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        length = self.length()
        #length = hypot(dx, dy)
        if length == 0:
            return [self.start, self.start, self.start, self.start]

        offset_x = (dy / length) * (self.thickness / 2.0)
        offset_y = -(dx / length) * (self.thickness / 2.0)

        return [
            Point(x=self.start.x + offset_x, y=self.start.y + offset_y),
            Point(x=self.start.x - offset_x, y=self.start.y - offset_y),
            Point(x=self.end.x - offset_x, y=self.end.y - offset_y),
            Point(x=self.end.x + offset_x, y=self.end.y + offset_y),
        ]

    def validate(self) -> None:
        """Validate wall geometry and constraints."""
        if self.thickness <= 0:
            raise ValueError("Wall thickness must be greater than zero")

        if hypot(self.end.x - self.start.x, self.end.y - self.start.y) <= 0:
            raise ValueError("Wall length must be greater than zero")

    def to_dict(self) -> dict[str, object]:
        """Serialize wall to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "thickness": self.thickness,
            "wall_type": self.wall_type.value,
            "locked": self.locked,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Wall:
        """Create wall from JSON-compatible dictionary."""
        start_raw = data.get("start", {})
        end_raw = data.get("end", {})
        thickness_raw = data.get("thickness", 300.0)

        start = Point.from_dict(start_raw) if isinstance(start_raw, dict) else Point(0.0, 0.0)
        end = Point.from_dict(end_raw) if isinstance(end_raw, dict) else Point(0.0, 0.0)

        wall = cls(
            id=str(data.get("id", str(uuid4()))),
            start=start,
            end=end,
            thickness=_to_float(thickness_raw, 300.0),
            wall_type=WallType(str(data.get("wall_type", WallType.EXTERIOR.value))),
            locked=bool(data.get("locked", False)),
        )
        wall.validate()
        return wall


def _to_float(value: object, default: float) -> float:
    """Convert persisted number fields with fallback for invalid values."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default
