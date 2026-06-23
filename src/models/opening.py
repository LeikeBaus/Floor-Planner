"""Opening domain model for generic wall breakthroughs."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Opening:
    """Represents a generic opening (hole) in a wall.

    Attributes:
        id: Unique identifier for this opening.
        wall_id: ID of the wall this opening is in.
        position: Distance in mm from wall start point along the wall.
        width: Opening width in mm.
        height: Opening height in mm (optional metadata for rendering).
        opening_type: Type of opening ('passage', 'alcove', 'vent', 'custom').
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    wall_id: str = ""
    position: float = 0.0
    width: float = 1500.0
    height: float = 2400.0
    opening_type: str = "passage"

    def to_dict(self) -> dict[str, object]:
        """Serialize opening to dictionary."""
        return {
            "id": self.id,
            "wall_id": self.wall_id,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "opening_type": self.opening_type,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Opening:
        """Deserialize opening from dictionary."""
        position_raw = data.get("position", 0.0)
        width_raw = data.get("width", 1500.0)
        height_raw = data.get("height", 2400.0)
        
        return Opening(
            id=str(data.get("id", str(uuid4()))),
            wall_id=str(data.get("wall_id", "")),
            position=float(position_raw) if isinstance(position_raw, (int, float, str)) else 0.0,
            width=float(width_raw) if isinstance(width_raw, (int, float, str)) else 1500.0,
            height=float(height_raw) if isinstance(height_raw, (int, float, str)) else 2400.0,
            opening_type=str(data.get("opening_type", "passage")),
        )
