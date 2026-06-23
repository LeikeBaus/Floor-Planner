"""Roof slope model for height interpolation input."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from geometry.point import Point


@dataclass(slots=True)
class RoofSlope:
    """Represents two boundary lines with start/end heights for roof slope definition."""

    start_line_start: Point
    start_line_end: Point
    end_line_start: Point
    end_line_end: Point
    height_start: float
    height_end: float
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, object]:
        """Serialize roof slope to dictionary."""
        return {
            "id": self.id,
            "start_line_start": self.start_line_start.to_dict(),
            "start_line_end": self.start_line_end.to_dict(),
            "end_line_start": self.end_line_start.to_dict(),
            "end_line_end": self.end_line_end.to_dict(),
            "height_start": self.height_start,
            "height_end": self.height_end,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> RoofSlope:
        """Deserialize roof slope from dictionary."""
        start_line_start_raw = data.get("start_line_start", {})
        start_line_end_raw = data.get("start_line_end", {})
        end_line_start_raw = data.get("end_line_start", {})
        end_line_end_raw = data.get("end_line_end", {})
        height_start_raw = data.get("height_start", 2500.0)
        height_end_raw = data.get("height_end", 500.0)

        return cls(
            id=str(data.get("id", str(uuid4()))),
            start_line_start=(
                Point.from_dict(start_line_start_raw)
                if isinstance(start_line_start_raw, dict)
                else Point(0.0, 0.0)
            ),
            start_line_end=(
                Point.from_dict(start_line_end_raw)
                if isinstance(start_line_end_raw, dict)
                else Point(1000.0, 0.0)
            ),
            end_line_start=(
                Point.from_dict(end_line_start_raw)
                if isinstance(end_line_start_raw, dict)
                else Point(0.0, 1000.0)
            ),
            end_line_end=(
                Point.from_dict(end_line_end_raw)
                if isinstance(end_line_end_raw, dict)
                else Point(1000.0, 1000.0)
            ),
            height_start=(
                float(height_start_raw)
                if isinstance(height_start_raw, (int, float, str))
                else 2500.0
            ),
            height_end=(
                float(height_end_raw) if isinstance(height_end_raw, (int, float, str)) else 500.0
            ),
        )
