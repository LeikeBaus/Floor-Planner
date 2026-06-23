"""Room domain model produced by wall-based detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from geometry.point import Point


@dataclass(slots=True)
class Room:
    """Represents a detected enclosed area on a floor."""

    polygon: list[Point]
    floor_area: float
    name: str = "Room"
    living_area: float = 0.0
    include_in_living_area: bool = True
    color: str = "#DDEEFF"
    label_offset_x: float = 0.0
    label_offset_y: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, object]:
        """Serialize room to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "include_in_living_area": self.include_in_living_area,
            "label_offset_x": self.label_offset_x,
            "label_offset_y": self.label_offset_y,
            "polygon": [point.to_dict() for point in self.polygon],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Room:
        """Create room from JSON-compatible dictionary."""
        polygon_raw = data.get("polygon", [])
        polygon: list[Point] = []
        if isinstance(polygon_raw, list):
            polygon = [Point.from_dict(item) for item in polygon_raw if isinstance(item, dict)]

        area = _polygon_area(polygon)
        label_offset_x_raw = data.get("label_offset_x", 0.0)
        label_offset_y_raw = data.get("label_offset_y", 0.0)
        include_raw = data.get("include_in_living_area", True)
        if isinstance(include_raw, bool):
            include_in_living_area = include_raw
        elif isinstance(include_raw, str):
            include_in_living_area = include_raw.lower() in {"1", "true", "yes", "on"}
        else:
            include_in_living_area = bool(include_raw)
        return cls(
            id=str(data.get("id", str(uuid4()))),
            name=str(data.get("name", "Room")),
            color=str(data.get("color", "#DDEEFF")),
            polygon=polygon,
            floor_area=area,
            living_area=0.0,
            include_in_living_area=include_in_living_area,
            label_offset_x=(
                float(label_offset_x_raw)
                if isinstance(label_offset_x_raw, (int, float, str))
                else 0.0
            ),
            label_offset_y=(
                float(label_offset_y_raw)
                if isinstance(label_offset_y_raw, (int, float, str))
                else 0.0
            ),
        )


def _polygon_area(polygon: list[Point]) -> float:
    """Compute polygon area using shoelace formula in mm^2."""
    if len(polygon) < 3:
        return 0.0

    area = 0.0
    for index, point in enumerate(polygon):
        next_point = polygon[(index + 1) % len(polygon)]
        area += point.x * next_point.y
        area -= next_point.x * point.y

    return abs(area) * 0.5
