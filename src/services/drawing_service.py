"""Drawing-domain business operations."""

from __future__ import annotations

from collections.abc import Sequence

from geometry.dimension_engine import DimensionEngine
from geometry.living_area_engine import LivingAreaEngine
from geometry.roof_slope_engine import RoofSlopeEngine
from geometry.room_detector import RoomDetector
from models.floor import Floor
from models.project_settings import ProjectSettings
from models.room import Room


class DrawingService:
    """Encapsulates non-UI drawing calculations and derived model updates."""

    def __init__(
        self,
        room_detector: RoomDetector | None = None,
        roof_slope_engine: RoofSlopeEngine | None = None,
        living_area_engine: LivingAreaEngine | None = None,
        dimension_engine: DimensionEngine | None = None,
    ) -> None:
        self._room_detector = room_detector or RoomDetector()
        self._roof_slope_engine = roof_slope_engine or RoofSlopeEngine()
        self._living_area_engine = living_area_engine or LivingAreaEngine()
        self._dimension_engine = dimension_engine or DimensionEngine()

    def recalculate_floor(self, floor: Floor, settings: ProjectSettings) -> None:
        """Recompute rooms, zones, areas, and auto dimensions from floor geometry."""
        previous_rooms = list(floor.rooms)
        floor.rooms = self._room_detector.detect_rooms(floor.walls)
        self._preserve_room_metadata(previous_rooms, floor.rooms)
        floor.height_zones = self._roof_slope_engine.generate_height_zones(
            roof_slopes=floor.roof_slopes,
            rooms=floor.rooms,
        )

        for room in floor.rooms:
            if not room.include_in_living_area:
                room.living_area = 0.0
                continue

            room_zones = [zone for zone in floor.height_zones if zone.room_id == room.id]
            if room_zones:
                room.living_area = self._living_area_engine.calculate_living_area(room_zones)
            else:
                room.living_area = room.floor_area

        floor.floor_area_total = sum(room.floor_area for room in floor.rooms)
        floor.living_area_total = sum(room.living_area for room in floor.rooms)

        manual_dimensions = [dimension for dimension in floor.dimensions if dimension.is_manual]
        auto_offset_by_wall: dict[str, float] = {}
        for dimension in floor.dimensions:
            if dimension.is_manual or dimension.wall_id is None:
                continue
            if dimension.display_start is None:
                continue
            base_dx = dimension.end.x - dimension.start.x
            base_dy = dimension.end.y - dimension.start.y
            base_length = (base_dx * base_dx + base_dy * base_dy) ** 0.5
            if base_length <= 1e-6:
                continue

            normal_x = -base_dy / base_length
            normal_y = base_dx / base_length
            dx = dimension.display_start.x - dimension.start.x
            dy = dimension.display_start.y - dimension.start.y
            offset = dx * normal_x + dy * normal_y
            auto_offset_by_wall[dimension.wall_id] = offset

        auto_dimensions = self._dimension_engine.generate_wall_dimensions(
            walls=floor.walls,
            visible=settings.show_dimensions,
            opacity=settings.dimension_opacity,
            offset_by_wall_id=auto_offset_by_wall,
        )
        floor.dimensions = manual_dimensions + auto_dimensions

    def _preserve_room_metadata(self, previous: Sequence[Room], current: Sequence[Room]) -> None:
        """Carry room names/labels over when room geometry remains near-identical."""
        prev_rooms = list(previous)
        for room in current:
            polygon = room.polygon
            if not polygon:
                continue

            cx = sum(point.x for point in polygon) / len(polygon)
            cy = sum(point.y for point in polygon) / len(polygon)

            best = None
            best_dist = float("inf")
            for old in prev_rooms:
                old_polygon = old.polygon
                if not old_polygon:
                    continue
                ox = sum(point.x for point in old_polygon) / len(old_polygon)
                oy = sum(point.y for point in old_polygon) / len(old_polygon)
                dist = ((cx - ox) ** 2 + (cy - oy) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best = old

            if best is not None and best_dist <= 500.0:
                room.name = best.name
                room.include_in_living_area = best.include_in_living_area
                room.label_offset_x = best.label_offset_x
                room.label_offset_y = best.label_offset_y
