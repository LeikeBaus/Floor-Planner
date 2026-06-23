"""Drawing-domain business operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re

from shapely.geometry import Polygon

from geometry.dimension_engine import DimensionEngine
from geometry.point import Point
from geometry.living_area_engine import LivingAreaEngine
from geometry.roof_slope_engine import RoofSlopeEngine
from geometry.room_detector import RoomDetector
from models.dimension import Dimension
from models.door import Door
from models.floor import Floor
from models.opening import Opening
from models.project_settings import ProjectSettings
from models.roof_slope import RoofSlope
from models.room import Room
from models.stair import Stair
from models.wall import Wall, WallType
from models.window import Window


@dataclass(slots=True)
class PropertyUpdateResult:
    """Hints for controller orchestration after a property mutation."""

    requires_recalculation: bool
    target_kind: str


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

    def apply_object_properties(
        self,
        target: object,
        values: dict[str, float | str | bool],
        default_exterior_wall_thickness: float,
        default_interior_wall_thickness: float,
    ) -> PropertyUpdateResult:
        """Apply edited properties to one selected model object."""
        if isinstance(target, Wall):
            requested_wall_type = WallType(str(values.get("wall_type", target.wall_type.value)))
            wall_type_changed = requested_wall_type != target.wall_type
            target.wall_type = requested_wall_type
            start_x = float(values.get("start_x", target.start.x))
            start_y = float(values.get("start_y", target.start.y))
            end_x = float(values.get("end_x", target.end.x))
            end_y = float(values.get("end_y", target.end.y))
            target.start = Point(start_x, start_y)
            target.end = Point(end_x, end_y)

            if "length_mm" in values:
                dx = target.end.x - target.start.x
                dy = target.end.y - target.start.y
                current_length = (dx * dx + dy * dy) ** 0.5
                requested_length = max(1.0, float(values["length_mm"]))
                if current_length > 1e-6:
                    scale = requested_length / current_length
                    target.end = Point(target.start.x + dx * scale, target.start.y + dy * scale)

            if wall_type_changed:
                if target.wall_type == WallType.INTERIOR:
                    target.thickness = max(1.0, default_interior_wall_thickness)
                else:
                    target.thickness = max(1.0, default_exterior_wall_thickness)
            else:
                target.thickness = float(values.get("thickness_mm", target.thickness))

            return PropertyUpdateResult(requires_recalculation=True, target_kind="wall")

        if isinstance(target, (Window, Door, Opening)):
            target.position = float(values.get("position_mm", target.position))
            target.width = float(values.get("width_mm", target.width))
            target.height = float(values.get("height_mm", target.height))
            if isinstance(target, Door):
                target.swing_direction = str(values.get("swing_direction", target.swing_direction))
                return PropertyUpdateResult(requires_recalculation=False, target_kind="door")
            if isinstance(target, Window):
                return PropertyUpdateResult(requires_recalculation=False, target_kind="window")
            return PropertyUpdateResult(requires_recalculation=False, target_kind="opening")

        if isinstance(target, Stair):
            target.width = float(values.get("width_mm", target.width))
            target.depth = float(values.get("depth_mm", target.depth))
            target.position_x = float(values.get("position_x", target.position_x))
            target.position_y = float(values.get("position_y", target.position_y))
            target.orientation_degrees = float(values.get("orientation_deg", target.orientation_degrees))
            return PropertyUpdateResult(requires_recalculation=True, target_kind="stair")

        if isinstance(target, RoofSlope):
            start = Point(
                float(values.get("start_x", target.start_line_start.x)),
                float(values.get("start_y", target.start_line_start.y)),
            )
            end = Point(
                float(values.get("end_x", target.start_line_end.x)),
                float(values.get("end_y", target.start_line_end.y)),
            )
            requested_length = float(values.get("length_mm", 0.0))
            dx = end.x - start.x
            dy = end.y - start.y
            length = (dx * dx + dy * dy) ** 0.5
            if length > 1e-6:
                normal_x = -dy / length
                normal_y = dx / length
                target_end_start = Point(
                    start.x + normal_x * requested_length,
                    start.y + normal_y * requested_length,
                )
                target_end_end = Point(
                    end.x + normal_x * requested_length,
                    end.y + normal_y * requested_length,
                )
            else:
                target_end_start = target.end_line_start
                target_end_end = target.end_line_end

            target.start_line_start = start
            target.start_line_end = end
            target.end_line_start = target_end_start
            target.end_line_end = target_end_end
            target.height_start = float(values.get("height_start", target.height_start))
            target.height_end = float(values.get("height_end", target.height_end))
            return PropertyUpdateResult(requires_recalculation=True, target_kind="roof_slope")

        if isinstance(target, Dimension):
            target.opacity = float(values.get("opacity", target.opacity))
            return PropertyUpdateResult(requires_recalculation=False, target_kind="dimension")

        if isinstance(target, Room):
            target.name = str(values.get("name", target.name))
            target.include_in_living_area = bool(
                values.get("include_in_living_area", target.include_in_living_area)
            )
            return PropertyUpdateResult(requires_recalculation=True, target_kind="room")

        return PropertyUpdateResult(requires_recalculation=False, target_kind="unknown")

    def _preserve_room_metadata(self, previous: Sequence[Room], current: Sequence[Room]) -> None:
        """Preserve room metadata across topology changes with split-aware matching.

        For split rooms, the largest overlapping new room keeps the original metadata.
        Smaller split fragments receive a fresh room name.
        """
        if not previous or not current:
            return

        prev_polygons = [self._room_polygon(room) for room in previous]
        current_polygons = [self._room_polygon(room) for room in current]

        # Build overlap pairs and greedily assign strongest one-to-one matches.
        overlaps: list[tuple[float, int, int]] = []
        for old_index, old_poly in enumerate(prev_polygons):
            if old_poly is None:
                continue
            for new_index, new_poly in enumerate(current_polygons):
                if new_poly is None:
                    continue
                overlap_area = old_poly.intersection(new_poly).area
                if overlap_area > 1.0:
                    overlaps.append((overlap_area, old_index, new_index))

        overlaps.sort(reverse=True)
        assigned_old: set[int] = set()
        assigned_new: set[int] = set()
        matches: dict[int, int] = {}

        for _area, old_index, new_index in overlaps:
            if old_index in assigned_old or new_index in assigned_new:
                continue
            assigned_old.add(old_index)
            assigned_new.add(new_index)
            matches[new_index] = old_index

        used_names = {room.name for room in previous}

        for new_index, room in enumerate(current):
            old_index = matches.get(new_index)
            if old_index is None:
                room.name = self._next_generated_room_name(used_names)
                room.label_offset_x = 0.0
                room.label_offset_y = 0.0
                used_names.add(room.name)
                continue

            old_room = previous[old_index]
            room.name = old_room.name
            room.include_in_living_area = old_room.include_in_living_area

            old_poly = prev_polygons[old_index]
            new_poly = current_polygons[new_index]
            overlap_ratio = 0.0
            if old_poly is not None and new_poly is not None and old_poly.area > 1e-6:
                overlap_ratio = old_poly.intersection(new_poly).area / old_poly.area

            # Large geometry changes (for example after splitting) should recentre labels.
            if overlap_ratio >= 0.8:
                room.label_offset_x = old_room.label_offset_x
                room.label_offset_y = old_room.label_offset_y
            else:
                room.label_offset_x = 0.0
                room.label_offset_y = 0.0

            used_names.add(room.name)

    def _room_polygon(self, room: Room) -> Polygon | None:
        """Build a valid shapely polygon for overlap matching."""
        if len(room.polygon) < 3:
            return None
        polygon = Polygon([(point.x, point.y) for point in room.polygon])
        if polygon.is_empty:
            return None
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        if polygon.is_empty or polygon.area <= 1.0:
            return None
        return polygon

    def _next_generated_room_name(self, used_names: set[str]) -> str:
        """Return the next free generated room name in the Room N sequence."""
        max_index = 0
        pattern = re.compile(r"^Room\s+(\d+)$")
        for name in used_names:
            match = pattern.match(name.strip())
            if match is None:
                continue
            max_index = max(max_index, int(match.group(1)))
        return f"Room {max_index + 1}"
