"""Window domain model for attaching to walls."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Window:
    """Represents a window opening on a wall.

    Attributes:
        id: Unique identifier for this window.
        wall_id: ID of the wall this window is attached to.
        position: Distance in mm from wall start point along the wall.
        width: Window width in mm.
        height: Window height in mm (optional metadata for rendering).
        swing_direction: Direction the window swings ('left' or 'right' for future doors).
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    wall_id: str = ""
    position: float = 0.0
    width: float = 1000.0
    height: float = 1200.0
    swing_direction: str = "left"

    def to_dict(self) -> dict[str, object]:
        """Serialize window to dictionary."""
        return {
            "id": self.id,
            "wall_id": self.wall_id,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "swing_direction": self.swing_direction,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Window:
        """Deserialize window from dictionary."""
        raw_id = data.get("id", str(uuid4()))
        raw_wall_id = data.get("wall_id", "")
        raw_position = data.get("position", 0.0)
        raw_width = data.get("width", 1000.0)
        raw_height = data.get("height", 1200.0)
        raw_swing = data.get("swing_direction", "left")
        position = float(raw_position) if isinstance(raw_position, (int, float, str)) else 0.0
        width = float(raw_width) if isinstance(raw_width, (int, float, str)) else 1000.0
        height = float(raw_height) if isinstance(raw_height, (int, float, str)) else 1200.0

        return Window(
            id=str(raw_id),
            wall_id=str(raw_wall_id),
            position=position,
            width=width,
            height=height,
            swing_direction=str(raw_swing),
        )
