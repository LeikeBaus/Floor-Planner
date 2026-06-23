"""Height zone model for calculated room-height regions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4

from shapely.geometry import Polygon

from geometry.point import Point


class HeightZoneType(StrEnum):
    """Discrete height categories used by living-area rules."""

    UNDER_1M = "UNDER_1M"
    BETWEEN_1M_AND_2M = "BETWEEN_1M_AND_2M"
    ABOVE_2M = "ABOVE_2M"


@dataclass(slots=True)
class HeightZone:
    """Represents one polygon area with a bounded vertical range."""

    polygon: list[Point]
    min_height: float
    max_height: float
    zone_type: HeightZoneType
    room_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, object]:
        """Serialize height zone to dictionary."""
        return {
            "id": self.id,
            "polygon": [point.to_dict() for point in self.polygon],
            "min_height": self.min_height,
            "max_height": self.max_height,
            "zone_type": self.zone_type.value,
            "room_id": self.room_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> HeightZone:
        """Deserialize height zone from dictionary."""
        polygon_raw = data.get("polygon", [])
        min_height_raw = data.get("min_height", 0.0)
        max_height_raw = data.get("max_height", 1000.0)

        polygon: list[Point] = []
        if isinstance(polygon_raw, list):
            polygon = [Point.from_dict(item) for item in polygon_raw if isinstance(item, dict)]

        zone_type_raw = str(data.get("zone_type", HeightZoneType.UNDER_1M.value))
        zone_type = HeightZoneType(zone_type_raw)

        return cls(
            id=str(data.get("id", str(uuid4()))),
            polygon=polygon,
            min_height=(
                float(min_height_raw) if isinstance(min_height_raw, (int, float, str)) else 0.0
            ),
            max_height=(
                float(max_height_raw) if isinstance(max_height_raw, (int, float, str)) else 1000.0
            ),
            zone_type=zone_type,
            room_id=str(data.get("room_id", "")),
        )

    def get_area(self) -> float:
        """Calculate polygon area in mm²."""
        if len(self.polygon) < 3:
            return 0.0

        coords = [(point.x, point.y) for point in self.polygon]
        polygon = Polygon(coords)
        return float(polygon.area)
