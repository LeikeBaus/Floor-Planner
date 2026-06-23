"""Dimension model for wall and annotation measurements."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from geometry.point import Point


@dataclass(slots=True)
class Dimension:
    """Represents a linear measurement annotation."""

    start: Point
    end: Point
    value: float
    display_start: Point | None = None
    display_end: Point | None = None
    is_manual: bool = False
    wall_id: str | None = None
    visible: bool = True
    opacity: float = 0.3
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, object]:
        """Serialize dimension to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "value": self.value,
            "display_start": self.display_start.to_dict() if self.display_start else None,
            "display_end": self.display_end.to_dict() if self.display_end else None,
            "is_manual": self.is_manual,
            "wall_id": self.wall_id,
            "visible": self.visible,
            "opacity": self.opacity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Dimension:
        """Create dimension from JSON-compatible dictionary."""
        start_raw = data.get("start", {})
        end_raw = data.get("end", {})
        display_start_raw = data.get("display_start")
        display_end_raw = data.get("display_end")

        start = Point.from_dict(start_raw) if isinstance(start_raw, dict) else Point(0.0, 0.0)
        end = Point.from_dict(end_raw) if isinstance(end_raw, dict) else Point(0.0, 0.0)
        display_start = (
            Point.from_dict(display_start_raw)
            if isinstance(display_start_raw, dict)
            else None
        )
        display_end = (
            Point.from_dict(display_end_raw)
            if isinstance(display_end_raw, dict)
            else None
        )

        value_raw = data.get("value", 0.0)
        opacity_raw = data.get("opacity", 0.3)

        return cls(
            id=str(data.get("id", str(uuid4()))),
            start=start,
            end=end,
            value=float(value_raw) if isinstance(value_raw, (int, float, str)) else 0.0,
            display_start=display_start,
            display_end=display_end,
            is_manual=bool(data.get("is_manual", False)),
            wall_id=(str(data.get("wall_id")) if data.get("wall_id") is not None else None),
            visible=bool(data.get("visible", True)),
            opacity=float(opacity_raw) if isinstance(opacity_raw, (int, float, str)) else 0.3,
        )
