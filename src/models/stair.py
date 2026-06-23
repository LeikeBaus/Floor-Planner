"""Stair domain model for inter-floor connections."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Stair:
    """Represents a staircase connecting two floors.

    Attributes:
        id: Unique identifier for this stair.
        floor_id_from: ID of the floor this stair starts from.
        floor_id_to: ID of the floor this stair connects to.
        position_x: X coordinate of stair placement in mm.
        position_y: Y coordinate of stair placement in mm.
        width: Stair width in mm.
        depth: Stair depth in mm.
        stair_type: Type of staircase ('straight', 'spiral', 'landing', 'custom').
        orientation_degrees: Clockwise orientation of ascent arrow in degrees.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    floor_id_from: str = ""
    floor_id_to: str = ""
    position_x: float = 0.0
    position_y: float = 0.0
    width: float = 1200.0
    depth: float = 1200.0
    stair_type: str = "straight"
    orientation_degrees: float = 0.0

    def to_dict(self) -> dict[str, object]:
        """Serialize stair to dictionary."""
        return {
            "id": self.id,
            "floor_id_from": self.floor_id_from,
            "floor_id_to": self.floor_id_to,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "width": self.width,
            "depth": self.depth,
            "stair_type": self.stair_type,
            "orientation_degrees": self.orientation_degrees,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Stair:
        """Deserialize stair from dictionary."""
        position_x_raw = data.get("position_x", 0.0)
        position_y_raw = data.get("position_y", 0.0)
        width_raw = data.get("width", 1200.0)
        depth_raw = data.get("depth", 1200.0)
        orientation_raw = data.get("orientation_degrees", None)

        return Stair(
            id=str(data.get("id", str(uuid4()))),
            floor_id_from=str(data.get("floor_id_from", "")),
            floor_id_to=str(data.get("floor_id_to", "")),
            position_x=(
                float(position_x_raw) if isinstance(position_x_raw, (int, float, str)) else 0.0
            ),
            position_y=(
                float(position_y_raw) if isinstance(position_y_raw, (int, float, str)) else 0.0
            ),
            width=float(width_raw) if isinstance(width_raw, (int, float, str)) else 1200.0,
            depth=float(depth_raw) if isinstance(depth_raw, (int, float, str)) else 1200.0,
            stair_type=str(data.get("stair_type", "straight")),
            orientation_degrees=(float(orientation_raw)),
        )
