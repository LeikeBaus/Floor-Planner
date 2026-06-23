"""Door domain model for attaching to walls."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Door:
    """Represents a door opening on a wall.

    Attributes:
        id: Unique identifier for this door.
        wall_id: ID of the wall this door is attached to.
        position: Distance in mm from wall start point along the wall.
        width: Door width in mm.
        height: Door height in mm (optional metadata for rendering).
        swing_direction: Direction the door swings ('left_out', 'right_out', 'left_in', 'right_in').
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    wall_id: str = ""
    position: float = 0.0
    width: float = 1000.0
    height: float = 2100.0
    swing_direction: str = "right_in"

    def to_dict(self) -> dict[str, object]:
        """Serialize door to dictionary."""
        return {
            "id": self.id,
            "wall_id": self.wall_id,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "swing_direction": self.swing_direction,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Door:
        """Deserialize door from dictionary."""
        id_raw = data.get("id", str(uuid4()))
        wall_id_raw = data.get("wall_id", "")
        position_raw = data.get("position", 0.0)
        width_raw = data.get("width", 1000.0)
        height_raw = data.get("height", 2100.0)
        swing_raw = data.get("swing_direction", "right_in")

        return Door(
            id=str(id_raw),
            wall_id=str(wall_id_raw),
            position=(
                float(position_raw) if isinstance(position_raw, (int, float, str)) else 0.0
            ),
            width=float(width_raw) if isinstance(width_raw, (int, float, str)) else 1000.0,
            height=float(height_raw) if isinstance(height_raw, (int, float, str)) else 2100.0,
            swing_direction=str(swing_raw),
        )
