"""Graphics scene implementation with CAD-style grid rendering."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QCursor, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from shapely.geometry import LineString

from geometry.point import Point
from models.dimension import Dimension
from models.door import Door
from models.floor import Floor
from models.height_zone import HeightZone
from models.opening import Opening
from models.overlay import Overlay
from models.roof_slope import RoofSlope
from models.room import Room
from models.stair import Stair
from models.wall import Wall
from models.window import Window
from services.wall_rendering_service import WallRenderingService
from views.objects.dimension_graphics_item import DimensionGraphicsItem
from views.objects.door_graphics_item import DoorGraphicsItem
from views.objects.height_zone_graphics_item import HeightZoneGraphicsItem
from views.objects.opening_graphics_item import OpeningGraphicsItem
from views.objects.overlay_graphics_item import OverlayGraphicsItem
from views.objects.roof_slope_graphics_item import RoofSlopeGraphicsItem
from views.objects.room_graphics_item import RoomGraphicsItem
from views.objects.stair_graphics_item import StairGraphicsItem
from views.objects.wall_graphics_item import WallGraphicsItem
from views.objects.wall_merged_graphics_item import WallMergedGraphicsItem
from views.objects.window_graphics_item import WindowGraphicsItem


class DrawingScene(QGraphicsScene):
    """Scene responsible for rendering grid and future floorplan items."""

    def __init__(self) -> None:
        super().__init__()
        self.grid_size_mm: float = 50.0
        self.major_grid_factor: int = 10
        self.base_grid_size_mm: float = 50.0
        self.grid_line_width: float = 1.2
        self.grid_opacity: float = 0.55
        self.grid_enabled: bool = True
        self._active_floor: Floor | None = None
        self._wall_items_by_id: dict[str, WallGraphicsItem] = {}
        self._merged_wall_item: WallMergedGraphicsItem | None = None
        self._wall_rendering_service = WallRenderingService()
        self._room_items_by_id: dict[str, RoomGraphicsItem] = {}
        self._height_zone_items_by_id: dict[str, HeightZoneGraphicsItem] = {}
        self._dimension_items_by_id: dict[str, DimensionGraphicsItem] = {}
        self._window_items_by_id: dict[str, WindowGraphicsItem] = {}
        self._door_items_by_id: dict[str, DoorGraphicsItem] = {}
        self._opening_items_by_id: dict[str, OpeningGraphicsItem] = {}
        self._stair_items_by_id: dict[str, StairGraphicsItem] = {}
        self._roof_slope_items_by_id: dict[str, RoofSlopeGraphicsItem] = {}
        self._overlay_items_by_id: dict[str, OverlayGraphicsItem] = {}
        self._available_floors: list[Floor] = []
        self._show_dimensions: bool = True
        self._dimension_opacity: float = 0.3
        self._dimension_font_size: float = 48.0
        self._snap_marker_mode: str = "selected"
        self._snap_attachment_width_mm: float = 300.0
        self._debug_snap_point: Point | None = None
        self.setSceneRect(-50000.0, -50000.0, 100000.0, 100000.0)

    def set_active_floor(self, floor: Floor, available_floors: list[Floor] | None = None) -> None:
        """Bind scene to an active floor and rebuild its graphics and overlays."""
        self._active_floor = floor
        self._available_floors = available_floors or []
        self._rebuild_wall_items()
        self.refresh_windows()
        self.refresh_doors()
        self.refresh_openings()
        self.refresh_stairs()
        self.refresh_roof_slopes()
        self.refresh_height_zones()
        self.refresh_overlays()

    @property
    def active_floor(self) -> Floor | None:
        """Return currently bound floor model if set."""
        return self._active_floor

    def add_wall_item(self, wall: Wall) -> None:
        """Add or refresh a wall graphics item by model identifier."""
        self._upsert_wall_hit_item(wall)
        self._refresh_merged_wall_item()

    def _upsert_wall_hit_item(self, wall: Wall) -> None:
        """Create a selectable wall item used only for interaction/hit testing."""
        existing = self._wall_items_by_id.get(wall.id)
        if existing is not None:
            self.removeItem(existing)

        item = WallGraphicsItem(wall, interaction_only=True)
        self.addItem(item)
        self._wall_items_by_id[wall.id] = item

    def remove_wall_item(self, wall: Wall) -> None:
        """Remove wall graphics item if it exists."""
        existing = self._wall_items_by_id.pop(wall.id, None)
        if existing is not None:
            self.removeItem(existing)
        self._refresh_merged_wall_item()

    def refresh_wall_item(self, wall: Wall) -> None:
        """Refresh wall graphics to match current model geometry."""
        self._upsert_wall_hit_item(wall)
        self._refresh_merged_wall_item()

    def refresh_walls(self) -> None:
        """Refresh wall graphics and merged contour rendering."""
        self._rebuild_wall_items()

    def refresh_rooms(self) -> None:
        """Rebuild room graphics from active floor room models."""
        for item in self._room_items_by_id.values():
            self.removeItem(item)
        self._room_items_by_id.clear()

        if self._active_floor is None:
            return

        for room in self._active_floor.rooms:
            room_item = RoomGraphicsItem(room)
            self.addItem(room_item)
            self._room_items_by_id[room.id] = room_item

    def refresh_height_zones(self) -> None:
        """Rebuild height zone graphics from active floor height zone models."""
        for item in self._height_zone_items_by_id.values():
            self.removeItem(item)
        self._height_zone_items_by_id.clear()

        if self._active_floor is None:
            return

        for height_zone in self._active_floor.height_zones:
            self.add_height_zone_item(height_zone)

    def set_height_zones_visibility(self, visible: bool) -> None:
        """Set global height-zone visibility."""
        for item in self._height_zone_items_by_id.values():
            item.setVisible(visible)

    def add_height_zone_item(self, height_zone: HeightZone) -> None:
        """Add or refresh a height zone graphics item by model identifier."""
        existing = self._height_zone_items_by_id.get(height_zone.id)
        if existing is not None:
            self.removeItem(existing)

        item = HeightZoneGraphicsItem(height_zone)
        self.addItem(item)
        self._height_zone_items_by_id[height_zone.id] = item

    def remove_height_zone_item(self, height_zone: HeightZone) -> None:
        """Remove height zone graphics item if it exists."""
        existing = self._height_zone_items_by_id.pop(height_zone.id, None)
        if existing is not None:
            self.removeItem(existing)

    def refresh_dimensions(self) -> None:
        """Rebuild dimension graphics from active floor dimension models."""
        for item in self._dimension_items_by_id.values():
            self.removeItem(item)
        self._dimension_items_by_id.clear()

        if self._active_floor is None:
            return

        for dimension in self._active_floor.dimensions:
            dimension.visible = self._show_dimensions
            dimension.opacity = self._dimension_opacity
            item = DimensionGraphicsItem(dimension, font_size=self._dimension_font_size)
            self.addItem(item)
            self._dimension_items_by_id[dimension.id] = item

    def add_dimension_item(self, dimension: Dimension) -> None:
        """Add or refresh one dimension graphics item by identifier."""
        existing = self._dimension_items_by_id.get(dimension.id)
        if existing is not None:
            self.removeItem(existing)

        dimension.visible = self._show_dimensions
        dimension.opacity = self._dimension_opacity
        item = DimensionGraphicsItem(dimension, font_size=self._dimension_font_size)
        self.addItem(item)
        self._dimension_items_by_id[dimension.id] = item

    def remove_dimension_item(self, dimension: Dimension) -> None:
        """Remove one dimension graphics item by identifier."""
        existing = self._dimension_items_by_id.pop(dimension.id, None)
        if existing is not None:
            self.removeItem(existing)

    def set_dimensions_visibility(self, visible: bool) -> None:
        """Set global dimension visibility and refresh existing items."""
        self._show_dimensions = visible
        for item in self._dimension_items_by_id.values():
            item.setVisible(visible)

    def set_dimension_opacity(self, opacity: float) -> None:
        """Set global dimension opacity and refresh existing items."""
        self._dimension_opacity = max(0.0, min(1.0, opacity))
        for item in self._dimension_items_by_id.values():
            item.setOpacity(self._dimension_opacity)

    def set_dimension_font_size(self, font_size: float) -> None:
        """Set global dimension label font size and rebuild dimensions."""
        self._dimension_font_size = max(48.0, min(180.0, font_size))
        self.refresh_dimensions()

    def refresh_windows(self) -> None:
        """Rebuild window graphics from active floor window models."""
        for item in self._window_items_by_id.values():
            self.removeItem(item)
        self._window_items_by_id.clear()

        if self._active_floor is None:
            return

        # Create a mapping of wall id to wall model for geometry lookup
        walls_by_id = {wall.id: wall for wall in self._active_floor.walls}

        for window in self._active_floor.windows:
            wall = walls_by_id.get(window.wall_id)
            if wall is not None:
                self.add_window_item(window, wall)

    def add_window_item(self, window: Window, wall: Wall) -> None:
        """Add or refresh a window graphics item by model identifier."""
        existing = self._window_items_by_id.get(window.id)
        if existing is not None:
            self.removeItem(existing)

        from PyQt6.QtCore import QPointF

        item = WindowGraphicsItem(
            window,
            QPointF(wall.start.x, wall.start.y),
            QPointF(wall.end.x, wall.end.y),
            wall.thickness,
        )

        self.addItem(item)
        self._window_items_by_id[window.id] = item

    def remove_window_item(self, window: Window) -> None:
        """Remove window graphics item if it exists."""
        existing = self._window_items_by_id.pop(window.id, None)
        if existing is not None:
            self.removeItem(existing)

    def refresh_doors(self) -> None:
        """Rebuild door graphics from active floor door models."""
        for item in self._door_items_by_id.values():
            self.removeItem(item)
        self._door_items_by_id.clear()

        if self._active_floor is None:
            return

        # Create a mapping of wall id to wall model for geometry lookup
        walls_by_id = {wall.id: wall for wall in self._active_floor.walls}

        for door in self._active_floor.doors:
            wall = walls_by_id.get(door.wall_id)
            if wall is not None:
                self.add_door_item(door, wall)

    def add_door_item(self, door: Door, wall: Wall) -> None:
        """Add or refresh a door graphics item by model identifier."""
        existing = self._door_items_by_id.get(door.id)
        if existing is not None:
            self.removeItem(existing)

        from PyQt6.QtCore import QPointF

        item = DoorGraphicsItem(
            door,
            QPointF(wall.start.x, wall.start.y),
            QPointF(wall.end.x, wall.end.y),
            wall.thickness,
        )
        self.addItem(item)
        self._door_items_by_id[door.id] = item

    def remove_door_item(self, door: Door) -> None:
        """Remove door graphics item if it exists."""
        existing = self._door_items_by_id.pop(door.id, None)
        if existing is not None:
            self.removeItem(existing)

    def refresh_openings(self) -> None:
        """Rebuild opening graphics from active floor opening models."""
        for item in self._opening_items_by_id.values():
            self.removeItem(item)
        self._opening_items_by_id.clear()

        if self._active_floor is None:
            return

        # Create a mapping of wall id to wall model for geometry lookup
        walls_by_id = {wall.id: wall for wall in self._active_floor.walls}

        for opening in self._active_floor.openings:
            wall = walls_by_id.get(opening.wall_id)
            if wall is not None:
                self.add_opening_item(opening, wall)

    def add_opening_item(self, opening: Opening, wall: Wall) -> None:
        """Add or refresh an opening graphics item by model identifier."""
        existing = self._opening_items_by_id.get(opening.id)
        if existing is not None:
            self.removeItem(existing)

        from PyQt6.QtCore import QPointF

        item = OpeningGraphicsItem(
            opening,
            QPointF(wall.start.x, wall.start.y),
            QPointF(wall.end.x, wall.end.y),
            wall.thickness,
        )
        self.addItem(item)
        self._opening_items_by_id[opening.id] = item

    def remove_opening_item(self, opening: Opening) -> None:
        """Remove opening graphics item if it exists."""
        existing = self._opening_items_by_id.pop(opening.id, None)
        if existing is not None:
            self.removeItem(existing)

    def refresh_stairs(self) -> None:
        """Rebuild stair graphics from active floor stair models."""
        for item in self._stair_items_by_id.values():
            self.removeItem(item)
        self._stair_items_by_id.clear()

        if self._active_floor is None:
            return

        for stair in self._active_floor.stairs:
            self.add_stair_item(stair)

    def add_stair_item(self, stair: Stair) -> None:
        """Add or refresh a stair graphics item by model identifier."""
        existing = self._stair_items_by_id.get(stair.id)
        if existing is not None:
            self.removeItem(existing)

        item = StairGraphicsItem(stair)
        self.addItem(item)
        self._stair_items_by_id[stair.id] = item

    def remove_stair_item(self, stair: Stair) -> None:
        """Remove stair graphics item if it exists."""
        existing = self._stair_items_by_id.pop(stair.id, None)
        if existing is not None:
            self.removeItem(existing)

    def refresh_roof_slopes(self) -> None:
        """Rebuild roof slope graphics from active floor roof slope models."""
        for item in self._roof_slope_items_by_id.values():
            self.removeItem(item)
        self._roof_slope_items_by_id.clear()

        if self._active_floor is None:
            return

        for roof_slope in self._active_floor.roof_slopes:
            self.add_roof_slope_item(roof_slope)

    def add_roof_slope_item(self, roof_slope: RoofSlope) -> None:
        """Add or refresh a roof slope graphics item by model identifier."""
        existing = self._roof_slope_items_by_id.get(roof_slope.id)
        if existing is not None:
            self.removeItem(existing)

        item = RoofSlopeGraphicsItem(roof_slope)
        self.addItem(item)
        self._roof_slope_items_by_id[roof_slope.id] = item

    def remove_roof_slope_item(self, roof_slope: RoofSlope) -> None:
        """Remove roof slope graphics item if it exists."""
        existing = self._roof_slope_items_by_id.pop(roof_slope.id, None)
        if existing is not None:
            self.removeItem(existing)

    def on_wall_created(self, wall: Wall) -> None:
        """DrawingView command callback for wall creation."""
        self.add_wall_item(wall)
        self.refresh_rooms()
        self.refresh_dimensions()

    def on_wall_deleted(self, wall: Wall) -> None:
        """DrawingView command callback for wall deletion."""
        self.remove_wall_item(wall)
        self.refresh_rooms()
        self.refresh_dimensions()

    def on_wall_updated(self, wall: Wall) -> None:
        """DrawingView command callback for wall update."""
        self.refresh_wall_item(wall)
        self.refresh_windows()
        self.refresh_doors()
        self.refresh_openings()
        self.refresh_rooms()
        self.refresh_dimensions()

    def on_dimension_created(self, dimension: Dimension) -> None:
        """DrawingView command callback for dimension creation."""
        self.add_dimension_item(dimension)

    def on_dimension_deleted(self, dimension: Dimension) -> None:
        """DrawingView command callback for dimension deletion."""
        self.remove_dimension_item(dimension)

    def on_dimension_updated(self, dimension: Dimension) -> None:
        """DrawingView command callback for dimension update."""
        self.add_dimension_item(dimension)

    def on_window_created(self, window: Window) -> None:
        """DrawingView command callback for window creation."""
        self.refresh_windows()

    def on_window_deleted(self, window: Window) -> None:
        """DrawingView command callback for window deletion."""
        self.remove_window_item(window)

    def on_window_updated(self, window: Window) -> None:
        """DrawingView command callback for window update."""
        self.refresh_windows()

    def on_door_created(self, door: Door) -> None:
        """DrawingView command callback for door creation."""
        self.refresh_doors()

    def on_door_deleted(self, door: Door) -> None:
        """DrawingView command callback for door deletion."""
        self.remove_door_item(door)

    def on_door_updated(self, door: Door) -> None:
        """DrawingView command callback for door update."""
        self.refresh_doors()

    def on_opening_created(self, opening: Opening) -> None:
        """DrawingView command callback for opening creation."""
        self.refresh_openings()

    def on_opening_deleted(self, opening: Opening) -> None:
        """DrawingView command callback for opening deletion."""
        self.remove_opening_item(opening)

    def on_opening_updated(self, opening: Opening) -> None:
        """DrawingView command callback for opening update."""
        self.refresh_openings()

    def on_stair_created(self, stair: Stair) -> None:
        """DrawingView command callback for stair creation."""
        self.add_stair_item(stair)

    def on_stair_deleted(self, stair: Stair) -> None:
        """DrawingView command callback for stair deletion."""
        self.remove_stair_item(stair)

    def on_stair_updated(self, stair: Stair) -> None:
        """DrawingView command callback for stair update."""
        self.add_stair_item(stair)

    def on_roof_slope_created(self, roof_slope: RoofSlope) -> None:
        """DrawingView command callback for roof slope creation."""
        self.add_roof_slope_item(roof_slope)
        self.refresh_height_zones()

    def on_roof_slope_deleted(self, roof_slope: RoofSlope) -> None:
        """DrawingView command callback for roof slope deletion."""
        self.remove_roof_slope_item(roof_slope)
        self.refresh_height_zones()

    def on_roof_slope_updated(self, roof_slope: RoofSlope) -> None:
        """DrawingView command callback for roof slope update."""
        self.add_roof_slope_item(roof_slope)
        self.refresh_height_zones()

    def selected_walls(self) -> list[Wall]:
        """Return model walls represented by selected wall graphics items."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            wall_id = getattr(item, "wall_id", None)
            if isinstance(wall_id, str):
                selected_ids.add(wall_id)

        return [wall for wall in self._active_floor.walls if wall.id in selected_ids]

    def selected_windows(self) -> list[Window]:
        """Return model windows represented by selected graphics items."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            window_id = getattr(item, "window_id", None)
            if isinstance(window_id, str):
                selected_ids.add(window_id)

        return [window for window in self._active_floor.windows if window.id in selected_ids]

    def selected_doors(self) -> list[Door]:
        """Return model doors represented by selected graphics items."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            door_id = getattr(item, "door_id", None)
            if isinstance(door_id, str):
                selected_ids.add(door_id)

        return [door for door in self._active_floor.doors if door.id in selected_ids]

    def selected_openings(self) -> list[Opening]:
        """Return model openings represented by selected graphics items."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            opening_id = getattr(item, "opening_id", None)
            if isinstance(opening_id, str):
                selected_ids.add(opening_id)

        return [opening for opening in self._active_floor.openings if opening.id in selected_ids]

    def selected_stairs(self) -> list[Stair]:
        """Return model stairs represented by selected graphics items."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            stair_id = getattr(item, "stair_id", None)
            if isinstance(stair_id, str):
                selected_ids.add(stair_id)

        return [stair for stair in self._active_floor.stairs if stair.id in selected_ids]

    def selected_roof_slopes(self) -> list[RoofSlope]:
        """Return model roof slopes represented by selected graphics items."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            roof_slope_id = getattr(item, "roof_slope_id", None)
            if isinstance(roof_slope_id, str):
                selected_ids.add(roof_slope_id)

        return [
            slope for slope in self._active_floor.roof_slopes if slope.id in selected_ids
        ]

    def selected_rooms(self) -> list[Room]:
        """Return model rooms represented by selected graphics items."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            room_id = getattr(item, "room_id", None)
            if isinstance(room_id, str):
                selected_ids.add(room_id)

        return [room for room in self._active_floor.rooms if room.id in selected_ids]

    def selected_dimensions(self) -> list[Dimension]:
        """Return selected dimensions (manual and auto-generated)."""
        if self._active_floor is None:
            return []

        selected_ids: set[str] = set()
        for item in self.selectedItems():
            dimension_id = getattr(item, "dimension_id", None)
            if isinstance(dimension_id, str):
                selected_ids.add(dimension_id)

        return [
            dimension
            for dimension in self._active_floor.dimensions
            if dimension.id in selected_ids
        ]

    def selected_manual_dimensions(self) -> list[Dimension]:
        """Return selected dimensions that are manually created only."""
        return [dimension for dimension in self.selected_dimensions() if dimension.is_manual]

    def wall_endpoints(self) -> list[tuple[Point, str]]:
        """Return wall endpoints with associated wall id for snapping."""
        if self._active_floor is None:
            return []

        endpoints: list[tuple[Point, str]] = []
        for wall in self._active_floor.walls:
            endpoints.append((wall.start, wall.id))
            endpoints.append((wall.end, wall.id))

        return endpoints

    def object_side_snap_points(self) -> tuple[list[Point], list[Point]]:
        """Return endpoints and side-midpoints from selectable object outlines."""
        endpoints: list[Point] = []
        midpoints: list[Point] = []

        for item in self.items():
            polygon = item.mapToScene(item.boundingRect())
            if polygon.isEmpty() or polygon.count() < 2:
                continue

            points: list[Point] = []
            for index in range(polygon.count()):
                p = polygon.at(index)
                points.append(Point(float(p.x()), float(p.y())))

            for index in range(len(points)):
                start = points[index]
                end = points[(index + 1) % len(points)]
                if abs(start.x - end.x) < 0.001 and abs(start.y - end.y) < 0.001:
                    continue

                endpoints.append(start)
                midpoints.append(Point((start.x + end.x) / 2.0, (start.y + end.y) / 2.0))

        return endpoints, midpoints

    def wall_midpoints(self) -> list[Point]:
        """Return wall center points for midpoint snapping."""
        if self._active_floor is None:
            return []

        return [wall.center for wall in self._active_floor.walls]

    def wall_intersections(self) -> list[Point]:
        """Return pairwise wall intersections for high-priority snapping."""
        if self._active_floor is None:
            return []

        return self._intersections_for_walls(self._active_floor.walls)

    def overlay_endpoints(self) -> list[Point]:
        """Return visible overlay wall outer-corner points for snapping."""
        endpoints: list[Point] = []
        for wall in self._overlay_source_walls():
            endpoints.extend(self._wall_outline_points(wall))
        return endpoints

    def overlay_midpoints(self) -> list[Point]:
        """Return visible overlay wall outer-edge midpoints for snapping."""
        midpoints: list[Point] = []
        for wall in self._overlay_source_walls():
            corners = self._wall_outline_points(wall)
            for index in range(len(corners)):
                a = corners[index]
                b = corners[(index + 1) % len(corners)]
                midpoints.append(Point((a.x + b.x) / 2.0, (a.y + b.y) / 2.0))
        return midpoints

    def overlay_intersections(self) -> list[Point]:
        """Return visible overlay wall intersections for snapping."""
        return self._intersections_for_walls(self._overlay_source_walls())

    def _overlay_source_walls(self) -> list[Wall]:
        """Collect walls from visible, snap-enabled overlay source floors."""
        if self._active_floor is None or not self._available_floors:
            return []

        floors_by_id = {floor.id: floor for floor in self._available_floors}
        source_walls: list[Wall] = []
        for overlay in self._active_floor.overlays:
            if not overlay.visible or not overlay.snap_enabled:
                continue

            source_floor = floors_by_id.get(overlay.source_floor_id)
            if source_floor is not None:
                source_walls.extend(source_floor.walls)

        return source_walls

    def _intersections_for_walls(self, walls: list[Wall]) -> list[Point]:
        """Return pairwise intersections for the provided wall set."""
        if not walls:
            return []

        lines = [
            LineString([(wall.start.x, wall.start.y), (wall.end.x, wall.end.y)])
            for wall in walls
            if wall.length > 0
        ]

        intersections: list[Point] = []
        seen: set[tuple[float, float]] = set()
        for first_index, first_line in enumerate(lines):
            for second_line in lines[first_index + 1 :]:
                geometry = first_line.intersection(second_line)
                if geometry.is_empty or geometry.geom_type != "Point":
                    continue

                x = float(geometry.x)
                y = float(geometry.y)
                key = (round(x, 3), round(y, 3))
                if key in seen:
                    continue

                seen.add(key)
                intersections.append(Point(x, y))

        return intersections

    def _wall_outline_points(self, wall: Wall) -> list[Point]:
        """Return four wall rectangle corner points (outer contour)."""
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return []

        nx = -dy / length
        ny = dx / length
        half = wall.thickness / 2.0
        return [
            Point(wall.start.x + nx * half, wall.start.y + ny * half),
            Point(wall.end.x + nx * half, wall.end.y + ny * half),
            Point(wall.end.x - nx * half, wall.end.y - ny * half),
            Point(wall.start.x - nx * half, wall.start.y - ny * half),
        ]

    def _rebuild_wall_items(self) -> None:
        """Recreate scene wall items from active floor state."""
        for wall_item in self._wall_items_by_id.values():
            self.removeItem(wall_item)
        self._wall_items_by_id.clear()

        if self._merged_wall_item is not None:
            self.removeItem(self._merged_wall_item)
            self._merged_wall_item = None

        for dimension_item in self._dimension_items_by_id.values():
            self.removeItem(dimension_item)
        self._dimension_items_by_id.clear()

        if self._active_floor is None:
            return

        for wall in self._active_floor.walls:
            self._upsert_wall_hit_item(wall)

        self._refresh_merged_wall_item()

        self.refresh_rooms()
        self.refresh_dimensions()

    def _refresh_merged_wall_item(self) -> None:
        """Create or update the merged wall contour item for the active floor."""
        if self._active_floor is None:
            if self._merged_wall_item is not None:
                self.removeItem(self._merged_wall_item)
                self._merged_wall_item = None
            return

        merged_path = self._wall_rendering_service.build_merged_wall_path(self._active_floor.walls)
        if merged_path.isEmpty():
            if self._merged_wall_item is not None:
                self.removeItem(self._merged_wall_item)
                self._merged_wall_item = None
            return

        if self._merged_wall_item is None:
            self._merged_wall_item = WallMergedGraphicsItem(merged_path)
            self.addItem(self._merged_wall_item)
            return

        self._merged_wall_item.set_merged_path(merged_path)

    def drawBackground(self, painter: QPainter | None, rect: QRectF) -> None:  # noqa: N802
        """Render a minor/major background grid in world millimeters."""
        super().drawBackground(painter, rect)
        if painter is None or self.grid_enabled is False:
            return

        view = self.views()[0] if self.views() else None
        zoom_scale = view.transform().m11() if view is not None else 1.0
        zoom_scale = max(0.01, zoom_scale)

        grid_step, major_step = self.grid_steps_for_zoom(zoom_scale)

        opacity = max(0.0, min(1.0, self.grid_opacity))
        minor_color = QColor("#A8A8A8")
        minor_color.setAlphaF(opacity)
        major_color = QColor("#7A7A7A")
        major_color.setAlphaF(min(1.0, opacity + 0.2))

        minor_pen = QPen(minor_color)
        major_pen = QPen(major_color)
        minor_pen.setWidthF(self.grid_line_width)
        major_pen.setWidthF(self.grid_line_width + 1.0)
        minor_pen.setCosmetic(True)
        major_pen.setCosmetic(True)

        grid_step_int = max(1, int(grid_step))
        major_step_int = max(grid_step_int, int(major_step))

        left = int(rect.left() // grid_step_int) * grid_step_int
        right = int(rect.right() // grid_step_int + 1) * grid_step_int
        top = int(rect.top() // grid_step_int) * grid_step_int
        bottom = int(rect.bottom() // grid_step_int + 1) * grid_step_int

        for x in range(left, right + 1, grid_step_int):
            painter.setPen(major_pen if x % major_step_int == 0 else minor_pen)
            painter.drawLine(x, top, x, bottom)

        for y in range(top, bottom + 1, grid_step_int):
            painter.setPen(major_pen if y % major_step_int == 0 else minor_pen)
            painter.drawLine(left, y, right, y)

    def drawForeground(self, painter: QPainter | None, rect: QRectF) -> None:  # noqa: N802
        """Render viewport-stable scale HUD and navigation labels above all items."""
        super().drawForeground(painter, rect)
        if painter is None:
            return

        view = self.views()[0] if self.views() else None
        if view is None:
            return

        zoom_scale = view.transform().m11() if view is not None else 1.0
        zoom_scale = max(0.01, zoom_scale)

        grid_step, _ = self.grid_steps_for_zoom(zoom_scale)

        painter.save()
        self._draw_snap_markers(painter, zoom_scale)
        self._draw_debug_snap_marker(painter, zoom_scale)
        # Draw UI overlays in viewport coordinates so they stay readable on all zoom levels.
        painter.resetTransform()
        self._draw_navigation_hud(painter, view, grid_step, zoom_scale)
        self._draw_scale_bar_hud(painter, view, zoom_scale)

        painter.restore()

    def set_grid_visibility(self, visible: bool) -> None:
        """Enable or disable background grid rendering."""
        self.grid_enabled = visible
        self.update()

    def set_snap_marker_mode(self, mode: str, attachment_width_mm: float) -> None:
        """Configure which wall snap markers should be visible."""
        self._snap_marker_mode = mode
        self._snap_attachment_width_mm = max(1.0, attachment_width_mm)
        self.update()

    def set_debug_snap_point(self, point: Point | None) -> None:
        """Set the current debug snap point highlight."""
        self._debug_snap_point = point
        self.update()

    def grid_steps_for_zoom(self, zoom_scale: float) -> tuple[float, float]:
        """Return minor/major grid spacing in mm for a given zoom level."""
        safe_zoom = max(0.01, zoom_scale)
        target_minor_px = 24.0
        desired_minor_mm = target_minor_px / safe_zoom
        minor_step = self._nice_grid_step(desired_minor_mm)
        major_step = minor_step * float(max(1, self.major_grid_factor))
        return minor_step, major_step

    def _nice_grid_step(self, target_mm: float) -> float:
        """Round target grid spacing to stable engineering intervals (1/2/5*10^n)."""
        if target_mm <= 1e-6:
            return max(1.0, self.base_grid_size_mm / 10.0)

        exponent = int(math.floor(math.log10(target_mm)))
        base = 10.0 ** exponent
        normalized = target_mm / base
        candidates = [1.0, 2.0, 5.0, 10.0]
        step_factor = min(candidates, key=lambda candidate: abs(candidate - normalized))
        return max(1.0, step_factor * base)

    def refresh_overlays(self) -> None:
        """Rebuild overlay graphics from active floor overlay models."""
        for item in self._overlay_items_by_id.values():
            self.removeItem(item)
        self._overlay_items_by_id.clear()

        if self._active_floor is None or not self._available_floors:
            return

        # Create a mapping of floor id to floor model
        floors_by_id = {floor.id: floor for floor in self._available_floors}

        floors_by_id = {floor.id: floor for floor in self._available_floors}
        for overlay in self._active_floor.overlays:
            source_floor = floors_by_id.get(overlay.source_floor_id)
            if source_floor is not None and overlay.visible:
                self.add_overlay_item(overlay, source_floor.walls, source_floor.rooms)

    def add_overlay_item(
        self,
        overlay: Overlay,
        source_walls: list[Wall],
        source_rooms: list[Room],
    ) -> None:
        """Add or refresh an overlay graphics item by model identifier."""
        existing = self._overlay_items_by_id.get(overlay.id)
        if existing is not None:
            self.removeItem(existing)

        item = OverlayGraphicsItem(source_walls, source_rooms, overlay.opacity)
        self.addItem(item)
        self._overlay_items_by_id[overlay.id] = item

    def remove_overlay_item(self, overlay: Overlay) -> None:
        """Remove overlay graphics item if it exists."""
        existing = self._overlay_items_by_id.pop(overlay.id, None)
        if existing is not None:
            self.removeItem(existing)

    def update_overlay_opacity(self, overlay: Overlay) -> None:
        """Update opacity of an overlay graphics item."""
        item = self._overlay_items_by_id.get(overlay.id)
        if item is not None:
            item.set_opacity(overlay.opacity)

    def _draw_navigation_hud(
        self,
        painter: QPainter,
        view: QGraphicsView,
        grid_step_mm: float,
        zoom_scale: float,
    ) -> None:
        """Draw stable grid/position info in the viewport corner."""
        viewport = getattr(view, "viewport", lambda: None)()
        if viewport is None:
            return

        center = view.mapToScene(viewport.rect().center())
        cursor_scene = self._cursor_scene_position(view)
        font_scale = max(0.25, min(4.0, zoom_scale))
        font = painter.font()
        font.setPointSizeF(max(8.0, min(14.0, 10.0 + math.log2(font_scale) * 1.2)))
        painter.setFont(font)

        if cursor_scene is not None:
            cursor_text = (
                f"Maus X {self._format_scene_distance(cursor_scene.x())}"
                f" / Y {self._format_scene_distance(cursor_scene.y())}"
            )
        else:
            cursor_text = "Maus außerhalb der Zeichenfläche"

        text = (
            f"Raster {self._format_scene_distance(grid_step_mm)}"
            f" | Zoom {zoom_scale * 100.0:.0f}%"
            f" | {cursor_text}"
            f" | Zentrum X {self._format_scene_distance(center.x())}"
            f" / Y {self._format_scene_distance(center.y())}"
        )

        box = QRectF(12.0, 12.0, 760.0, 30.0)
        painter.setPen(QPen(QColor("#334155"), 1.0))
        painter.setBrush(QColor(255, 255, 255, 210))
        painter.drawRoundedRect(box, 6.0, 6.0)
        painter.setPen(QPen(QColor("#0F172A"), 1.0))
        painter.drawText(QRectF(20.0, 16.0, 744.0, 24.0), text)

    def _draw_snap_markers(self, painter: QPainter, zoom_scale: float) -> None:
        """Draw wall marker points for the current overlay mode."""
        walls = self._marker_walls()
        if not walls:
            return

        radius = self._marker_radius_scene(zoom_scale)
        self._draw_marker_points(
            painter,
            [point for wall in walls for point in self._wall_outline_points(wall)],
            QColor("#16A34A"),
            radius,
        )
        self._draw_marker_points(
            painter,
            [point for wall in walls for point in self._wall_edge_midpoints(wall)],
            QColor("#2563EB"),
            radius,
        )
        self._draw_marker_points(
            painter,
            [
                point
                for wall in walls
                for point in self._wall_attachment_points(wall, self._snap_attachment_width_mm)
            ],
            QColor("#DC2626"),
            radius,
        )
        self._draw_marker_points(
            painter,
            [wall.center for wall in walls],
            QColor("#9333EA"),
            radius,
        )

    def _draw_debug_snap_marker(self, painter: QPainter, zoom_scale: float) -> None:
        """Draw the debug snap highlight for the current snap candidate."""
        if self._debug_snap_point is None:
            return

        radius = self._marker_radius_scene(zoom_scale) * 1.4
        pen = QPen(QColor("#F59E0B"))
        pen.setWidthF(max(1.5, radius * 0.2))
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(245, 158, 11, 120)))
        painter.drawEllipse(QPointF(self._debug_snap_point.x, self._debug_snap_point.y), radius, radius)

    def _draw_marker_points(
        self,
        painter: QPainter,
        points: list[Point],
        color: QColor,
        radius: float,
    ) -> None:
        """Draw a colored set of scene-space marker points."""
        if not points:
            return

        pen = QPen(color)
        pen.setWidthF(max(1.0, radius * 0.18))
        painter.setPen(pen)
        painter.setBrush(QBrush(color))
        for point in points:
            painter.drawEllipse(QPointF(point.x, point.y), radius, radius)

    def _marker_walls(self) -> list[Wall]:
        """Return walls whose snap markers should be shown."""
        if self._active_floor is None:
            return []
        if self._snap_marker_mode == "all":
            return self._active_floor.walls
        if self._snap_marker_mode != "selected":
            return []
        return self.selected_walls()

    def _marker_radius_scene(self, zoom_scale: float) -> float:
        """Return a scene radius whose screen size grows moderately with zoom."""
        desired_screen_radius = max(4.0, min(12.0, 6.0 * (zoom_scale ** 0.35)))
        return desired_screen_radius / max(0.01, zoom_scale)

    def _wall_edge_midpoints(self, wall: Wall) -> list[Point]:
        """Return midpoints of the outer wall edges."""
        corners = self._wall_outline_points(wall)
        if len(corners) < 4:
            return []
        return [
            Point(
                (corners[index].x + corners[(index + 1) % 4].x) / 2.0,
                (corners[index].y + corners[(index + 1) % 4].y) / 2.0,
            )
            for index in range(4)
        ]

    def _wall_attachment_points(self, wall: Wall, attachment_width_mm: float) -> list[Point]:
        """Return attachment points located near wall corners on the outer contour."""
        if attachment_width_mm <= 0.0:
            return []

        corners = self._wall_outline_points(wall)
        if len(corners) < 4:
            return []

        half_attachment = attachment_width_mm / 2.0
        result: list[Point] = []
        for index in range(4):
            start = corners[index]
            end = corners[(index + 1) % 4]
            dx = end.x - start.x
            dy = end.y - start.y
            length = math.hypot(dx, dy)
            if length <= attachment_width_mm + 1e-6:
                continue
            ux = dx / length
            uy = dy / length
            result.append(Point(start.x + ux * half_attachment, start.y + uy * half_attachment))
            result.append(Point(end.x - ux * half_attachment, end.y - uy * half_attachment))
        return result

    def _draw_scale_bar_hud(
        self,
        painter: QPainter,
        view: QGraphicsView,
        zoom_scale: float,
    ) -> None:
        """Draw a zoom-aware scale bar with meaningful tick spacing."""
        viewport = getattr(view, "viewport", lambda: None)()
        if viewport is None:
            return

        viewport_rect = viewport.rect()
        target_px = 150.0
        target_mm = target_px / zoom_scale
        bar_length_mm = self._nice_scale_length(target_mm)
        bar_length_px = bar_length_mm * zoom_scale
        tick_step_mm = self._nice_tick_step(bar_length_mm)
        tick_count = max(1, int(round(bar_length_mm / tick_step_mm)))

        margin = 20.0
        x2 = float(viewport_rect.right()) - margin
        x1 = x2 - bar_length_px
        y = float(viewport_rect.bottom()) - margin

        font_scale = max(0.25, min(4.0, zoom_scale))
        font = painter.font()
        font.setPointSizeF(max(8.0, min(14.0, 10.0 + math.log2(font_scale) * 1.2)))
        painter.setFont(font)

        panel = QRectF(x1 - 12.0, y - 36.0, bar_length_px + 24.0, 44.0)
        painter.setPen(QPen(QColor("#334155"), 1.0))
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawRoundedRect(panel, 6.0, 6.0)

        painter.setPen(QPen(QColor("#111827"), 2.0))
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))
        for index in range(tick_count + 1):
            tick_x = x1 + (bar_length_px / tick_count) * index
            tick_half = 6.0 if index in (0, tick_count) else 4.0
            painter.drawLine(
                QPointF(tick_x, y - tick_half),
                QPointF(tick_x, y + tick_half),
            )

        label = (
            f"{self._format_scene_distance(bar_length_mm)}"
            f" ({self._format_scene_distance(tick_step_mm)} je Strich)"
        )
        painter.setPen(QPen(QColor("#0F172A"), 1.0))
        painter.drawText(QRectF(x1, y - 30.0, bar_length_px, 18.0), label)

    def _nice_scale_length(self, target_mm: float) -> float:
        """Return a meaningful scale-bar length near target (10 mm ... 5 m ...)."""
        if target_mm <= 1e-6:
            return 10.0

        base_steps = [10.0, 20.0, 50.0, 100.0, 200.0, 500.0]
        exponent = int(math.floor(math.log10(target_mm)))
        candidates: list[float] = []
        for power in range(exponent - 2, exponent + 3):
            factor = 10.0 ** power
            for step in base_steps:
                value = step * factor
                if value >= 5.0:
                    candidates.append(value)

        if not candidates:
            return 10.0

        return min(candidates, key=lambda value: abs(value - target_mm))

    def _nice_tick_step(self, bar_length_mm: float) -> float:
        """Return sensible tick spacing for a chosen scale-bar length."""
        steps = [
            10.0,
            20.0,
            50.0,
            100.0,
            200.0,
            500.0,
            1000.0,
            2000.0,
            5000.0,
            10000.0,
        ]
        candidates: list[tuple[float, int]] = []
        for step in steps:
            if step >= bar_length_mm:
                continue
            ratio = bar_length_mm / step
            rounded = int(round(ratio))
            if 2 <= rounded <= 10 and abs(ratio - rounded) <= 0.2:
                candidates.append((step, rounded))

        if candidates:
            # Prefer more detail (higher tick count), then larger step for cleaner labels.
            best_step, _ = max(candidates, key=lambda entry: (entry[1], entry[0]))
            return best_step

        return max(10.0, bar_length_mm / 2.0)

    def _cursor_scene_position(self, view: QGraphicsView) -> QPointF | None:
        """Return scene position of the mouse cursor when inside the view viewport."""
        viewport = view.viewport()
        if viewport is None:
            return None
        local_pos = viewport.mapFromGlobal(QCursor.pos())
        if not viewport.rect().contains(local_pos):
            return None
        return view.mapToScene(local_pos)

    def _format_scene_distance(self, value_mm: float) -> str:
        """Format world distances as mm/cm/m for labels."""
        magnitude = abs(value_mm)
        if magnitude >= 1000.0:
            return f"{value_mm / 1000.0:.1f} m"
        if magnitude >= 100.0:
            return f"{value_mm / 10.0:.0f} cm"
        if magnitude >= 10.0:
            return f"{value_mm / 10.0:.1f} cm"
        return f"{value_mm:.0f} mm"

