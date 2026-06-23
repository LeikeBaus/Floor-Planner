"""Floor model representing a single level in a building."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from models.dimension import Dimension
from models.door import Door
from models.height_zone import HeightZone
from models.opening import Opening
from models.overlay import Overlay
from models.roof_slope import RoofSlope
from models.room import Room
from models.stair import Stair
from models.wall import Wall
from models.window import Window


@dataclass(slots=True)
class Floor:
    """A logical building floor containing architectural elements."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Ground Floor"
    elevation: float = 0.0
    walls: list[Wall] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    dimensions: list[Dimension] = field(default_factory=list)
    windows: list[Window] = field(default_factory=list)
    doors: list[Door] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)
    stairs: list[Stair] = field(default_factory=list)
    overlays: list[Overlay] = field(default_factory=list)
    roof_slopes: list[RoofSlope] = field(default_factory=list)
    height_zones: list[HeightZone] = field(default_factory=list)
    floor_area_total: float = 0.0
    living_area_total: float = 0.0

    def to_dict(self) -> dict[str, object]:
        """Serialize floor to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "elevation": self.elevation,
            "walls": [wall.to_dict() for wall in self.walls],
            "rooms": [room.to_dict() for room in self.rooms],
            "windows": [window.to_dict() for window in self.windows],
            "doors": [door.to_dict() for door in self.doors],
            "openings": [opening.to_dict() for opening in self.openings],
            "stairs": [stair.to_dict() for stair in self.stairs],
            "overlays": [overlay.to_dict() for overlay in self.overlays],
            "roof_slopes": [roof_slope.to_dict() for roof_slope in self.roof_slopes],
            "height_zones": [height_zone.to_dict() for height_zone in self.height_zones],
            "floor_area_total": self.floor_area_total,
            "living_area_total": self.living_area_total,
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Floor:
        """Create floor from JSON-compatible dictionary."""
        elevation_raw = data.get("elevation", 0.0)
        wall_payload = data.get("walls", [])
        room_payload = data.get("rooms", [])
        dimension_payload = data.get("dimensions", [])
        window_payload = data.get("windows", [])
        door_payload = data.get("doors", [])
        opening_payload = data.get("openings", [])
        stair_payload = data.get("stairs", [])
        overlay_payload = data.get("overlays", [])
        roof_slope_payload = data.get("roof_slopes", [])
        height_zone_payload = data.get("height_zones", [])
        floor_area_total_raw = data.get("floor_area_total", 0.0)
        living_area_total_raw = data.get("living_area_total", 0.0)
        walls: list[Wall] = []
        rooms: list[Room] = []
        dimensions: list[Dimension] = []
        windows: list[Window] = []
        doors: list[Door] = []
        openings: list[Opening] = []
        stairs: list[Stair] = []
        overlays: list[Overlay] = []
        roof_slopes: list[RoofSlope] = []
        height_zones: list[HeightZone] = []
        if isinstance(wall_payload, list):
            walls = [Wall.from_dict(item) for item in wall_payload if isinstance(item, dict)]
        if isinstance(room_payload, list):
            rooms = [Room.from_dict(item) for item in room_payload if isinstance(item, dict)]
        if isinstance(dimension_payload, list):
            dimensions = [
                Dimension.from_dict(item) for item in dimension_payload if isinstance(item, dict)
            ]
        if isinstance(window_payload, list):
            windows = [Window.from_dict(item) for item in window_payload if isinstance(item, dict)]
        if isinstance(door_payload, list):
            doors = [Door.from_dict(item) for item in door_payload if isinstance(item, dict)]
        if isinstance(opening_payload, list):
            openings = [
                Opening.from_dict(item) for item in opening_payload if isinstance(item, dict)
            ]
        if isinstance(stair_payload, list):
            stairs = [Stair.from_dict(item) for item in stair_payload if isinstance(item, dict)]
        if isinstance(overlay_payload, list):
            overlays = [
                Overlay.from_dict(item) for item in overlay_payload if isinstance(item, dict)
            ]
        if isinstance(roof_slope_payload, list):
            roof_slopes = [
                RoofSlope.from_dict(item) for item in roof_slope_payload if isinstance(item, dict)
            ]
        if isinstance(height_zone_payload, list):
            height_zones = [
                HeightZone.from_dict(item) for item in height_zone_payload if isinstance(item, dict)
            ]

        return cls(
            id=str(data.get("id", str(uuid4()))),
            name=str(data.get("name", "Ground Floor")),
            elevation=float(elevation_raw) if isinstance(elevation_raw, (int, float, str)) else 0.0,
            walls=walls,
            rooms=rooms,
            dimensions=dimensions,
            windows=windows,
            doors=doors,
            openings=openings,
            stairs=stairs,
            overlays=overlays,
            roof_slopes=roof_slopes,
            height_zones=height_zones,
            floor_area_total=(
                float(floor_area_total_raw)
                if isinstance(floor_area_total_raw, (int, float, str))
                else 0.0
            ),
            living_area_total=(
                float(living_area_total_raw)
                if isinstance(living_area_total_raw, (int, float, str))
                else 0.0
            ),
        )
