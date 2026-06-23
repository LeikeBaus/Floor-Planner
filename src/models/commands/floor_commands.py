"""Undoable floor command models."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from math import cos, radians, sin
from typing import TypeVar

from PyQt6.QtGui import QUndoCommand

from geometry.point import Point
from models.dimension import Dimension
from models.door import Door
from models.floor import Floor
from models.opening import Opening
from models.roof_slope import RoofSlope
from models.stair import Stair
from models.wall import Wall
from models.window import Window

TModel = TypeVar(
    "TModel",
    Wall,
    Dimension,
    Window,
    Door,
    Opening,
    Stair,
    RoofSlope,
)

class BaseCommand(QUndoCommand):
    """Base command abstraction used with QUndoStack."""

    @abstractmethod
    def redo(self) -> None:
        """Apply command effect."""

    @abstractmethod
    def undo(self) -> None:
        """Revert command effect."""


class CreateWallCommand(BaseCommand):
    """Undoable command that appends/removes a wall from a floor."""

    def __init__(
        self,
        floor: Floor,
        wall: Wall,
        on_create: Callable[[Wall], None] | None = None,
        on_delete: Callable[[Wall], None] | None = None,
    ) -> None:
        super().__init__("Create Wall")
        self._floor = floor
        self._wall = wall
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Append wall to floor and notify view callback."""
        if not any(existing.id == self._wall.id for existing in self._floor.walls):
            self._floor.walls.append(self._wall)
            if self._on_create is not None:
                self._on_create(self._wall)

    def undo(self) -> None:
        """Remove wall from floor and notify view callback."""
        for index, existing in enumerate(self._floor.walls):
            if existing.id == self._wall.id:
                del self._floor.walls[index]
                if self._on_delete is not None:
                    self._on_delete(self._wall)
                break


class DeleteWallsCommand(BaseCommand):
    """Undoable command that removes a list of walls from a floor."""

    def __init__(
        self,
        floor: Floor,
        walls: list[Wall],
        on_create: Callable[[Wall], None] | None = None,
        on_delete: Callable[[Wall], None] | None = None,
    ) -> None:
        super().__init__("Delete Walls")
        self._floor = floor
        self._walls = walls
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Delete target walls from floor and notify view callback."""
        ids_to_remove = {wall.id for wall in self._walls}
        kept_walls: list[Wall] = []

        for existing in self._floor.walls:
            if existing.id in ids_to_remove:
                if self._on_delete is not None:
                    self._on_delete(existing)
            else:
                kept_walls.append(existing)

        self._floor.walls = kept_walls

    def undo(self) -> None:
        """Restore deleted walls to floor and notify view callback."""
        existing_ids = {wall.id for wall in self._floor.walls}
        for wall in self._walls:
            if wall.id not in existing_ids:
                self._floor.walls.append(wall)
                if self._on_create is not None:
                    self._on_create(wall)


class MoveWallsCommand(BaseCommand):
    """Undoable command that translates selected walls by a delta."""

    def __init__(
        self,
        walls: list[Wall],
        delta_x: float,
        delta_y: float,
        on_update: Callable[[Wall], None] | None = None,
        floor: Floor | None = None,
        stairs: list[Stair] | None = None,
        roof_slopes: list[RoofSlope] | None = None,
        on_stair_update: Callable[[Stair], None] | None = None,
        on_roof_slope_update: Callable[[RoofSlope], None] | None = None,
    ) -> None:
        super().__init__("Move Selection")
        self._walls = walls
        self._delta_x = delta_x
        self._delta_y = delta_y
        self._on_update = on_update
        self._floor = floor
        self._stairs = stairs or []
        self._roof_slopes = roof_slopes or []
        self._on_stair_update = on_stair_update
        self._on_roof_slope_update = on_roof_slope_update

    def redo(self) -> None:
        """Apply translation to all target walls."""
        self._translate(self._delta_x, self._delta_y)

    def undo(self) -> None:
        """Revert translation for all target walls."""
        self._translate(-self._delta_x, -self._delta_y)

    def _translate(self, delta_x: float, delta_y: float) -> None:
        """Translate wall endpoints and refresh view callback."""
        from geometry.point import Point

        for wall in self._walls:
            wall.start = Point(wall.start.x + delta_x, wall.start.y + delta_y)
            wall.end = Point(wall.end.x + delta_x, wall.end.y + delta_y)
            if self._on_update is not None:
                self._on_update(wall)

        for stair in self._stairs:
            stair.position_x += delta_x
            stair.position_y += delta_y
            if self._on_stair_update is not None:
                self._on_stair_update(stair)

        for slope in self._roof_slopes:
            slope.start_line_start = Point(
                slope.start_line_start.x + delta_x,
                slope.start_line_start.y + delta_y,
            )
            slope.start_line_end = Point(
                slope.start_line_end.x + delta_x,
                slope.start_line_end.y + delta_y,
            )
            slope.end_line_start = Point(
                slope.end_line_start.x + delta_x,
                slope.end_line_start.y + delta_y,
            )
            slope.end_line_end = Point(
                slope.end_line_end.x + delta_x,
                slope.end_line_end.y + delta_y,
            )
            if self._on_roof_slope_update is not None:
                self._on_roof_slope_update(slope)

        if self._floor is not None:
            moved_walls = [wall for wall in self._walls]
            for dimension in self._floor.dimensions:
                if not dimension.is_manual:
                    continue
                if _point_near_any_wall(dimension.start, moved_walls):
                    dimension.start = Point(
                        dimension.start.x + delta_x,
                        dimension.start.y + delta_y,
                    )
                if _point_near_any_wall(dimension.end, moved_walls):
                    dimension.end = Point(
                        dimension.end.x + delta_x,
                        dimension.end.y + delta_y,
                    )
                if dimension.display_start is not None:
                    dimension.display_start = Point(
                        dimension.display_start.x + delta_x,
                        dimension.display_start.y + delta_y,
                    )
                if dimension.display_end is not None:
                    dimension.display_end = Point(
                        dimension.display_end.x + delta_x,
                        dimension.display_end.y + delta_y,
                    )


class MoveHostedObjectsCommand(BaseCommand):
    """Undoable command that moves wall-hosted objects along wall length."""

    def __init__(
        self,
        windows: list[Window],
        window_positions: dict[str, tuple[float, float]],
        doors: list[Door],
        door_positions: dict[str, tuple[float, float]],
        openings: list[Opening],
        opening_positions: dict[str, tuple[float, float]],
        on_window_update: Callable[[Window], None] | None = None,
        on_door_update: Callable[[Door], None] | None = None,
        on_opening_update: Callable[[Opening], None] | None = None,
    ) -> None:
        super().__init__("Move Hosted Objects")
        self._windows = windows
        self._window_positions = window_positions
        self._doors = doors
        self._door_positions = door_positions
        self._openings = openings
        self._opening_positions = opening_positions
        self._on_window_update = on_window_update
        self._on_door_update = on_door_update
        self._on_opening_update = on_opening_update

    def redo(self) -> None:
        """Apply target positions for hosted objects."""
        self._apply(use_new=True)

    def undo(self) -> None:
        """Restore original positions for hosted objects."""
        self._apply(use_new=False)

    def _apply(self, use_new: bool) -> None:
        index = 1 if use_new else 0
        for window in self._windows:
            pos = self._window_positions.get(window.id)
            if pos is not None:
                window.position = pos[index]
                if self._on_window_update is not None:
                    self._on_window_update(window)

        for door in self._doors:
            pos = self._door_positions.get(door.id)
            if pos is not None:
                door.position = pos[index]
                if self._on_door_update is not None:
                    self._on_door_update(door)

        for opening in self._openings:
            pos = self._opening_positions.get(opening.id)
            if pos is not None:
                opening.position = pos[index]
                if self._on_opening_update is not None:
                    self._on_opening_update(opening)


class MoveDimensionsCommand(BaseCommand):
    """Undoable command that moves dimension display offsets."""

    def __init__(
        self,
        dimensions: list[Dimension],
        positions: dict[str, tuple[Point, Point]],
        on_update: Callable[[Dimension], None] | None = None,
    ) -> None:
        super().__init__("Move Dimensions")
        self._dimensions = dimensions
        self._positions = positions
        self._on_update = on_update

    def redo(self) -> None:
        """Apply new display positions."""
        self._apply(use_new=True)

    def undo(self) -> None:
        """Restore original display positions."""
        self._apply(use_new=False)

    def _apply(self, use_new: bool) -> None:
        index = 1 if use_new else 0
        for dimension in self._dimensions:
            pair = self._positions.get(dimension.id)
            if pair is None:
                continue
            selected = pair[index]
            dx = selected.x - dimension.start.x
            dy = selected.y - dimension.start.y
            dimension.display_start = Point(dimension.start.x + dx, dimension.start.y + dy)
            dimension.display_end = Point(dimension.end.x + dx, dimension.end.y + dy)
            if self._on_update is not None:
                self._on_update(dimension)


class RotateSelectionCommand(BaseCommand):
    """Undoable command that rotates walls, stairs, and roof slopes in place."""

    def __init__(
        self,
        walls: list[Wall],
        stairs: list[Stair],
        roof_slopes: list[RoofSlope],
        delta_degrees: float,
        on_wall_update: Callable[[Wall], None] | None = None,
        on_stair_update: Callable[[Stair], None] | None = None,
        on_roof_slope_update: Callable[[RoofSlope], None] | None = None,
    ) -> None:
        super().__init__("Rotate Selection")
        self._walls = walls
        self._stairs = stairs
        self._roof_slopes = roof_slopes
        self._delta_degrees = delta_degrees
        self._on_wall_update = on_wall_update
        self._on_stair_update = on_stair_update
        self._on_roof_slope_update = on_roof_slope_update

    def redo(self) -> None:
        """Apply the configured rotation."""
        self._rotate(self._delta_degrees)

    def undo(self) -> None:
        """Revert the configured rotation."""
        self._rotate(-self._delta_degrees)

    def _rotate(self, delta_degrees: float) -> None:
        """Rotate all supported object types by the same delta."""
        for wall in self._walls:
            center = wall.center
            wall.start = _rotate_point(wall.start, center, delta_degrees)
            wall.end = _rotate_point(wall.end, center, delta_degrees)
            if self._on_wall_update is not None:
                self._on_wall_update(wall)

        for stair in self._stairs:
            center = Point(stair.position_x + stair.width / 2.0, stair.position_y + stair.depth / 2.0)
            stair.orientation_degrees = (stair.orientation_degrees + delta_degrees) % 360.0
            stair.position_x = center.x - stair.width / 2.0
            stair.position_y = center.y - stair.depth / 2.0
            if self._on_stair_update is not None:
                self._on_stair_update(stair)

        for roof_slope in self._roof_slopes:
            center = _roof_slope_center(roof_slope)
            roof_slope.start_line_start = _rotate_point(roof_slope.start_line_start, center, delta_degrees)
            roof_slope.start_line_end = _rotate_point(roof_slope.start_line_end, center, delta_degrees)
            roof_slope.end_line_start = _rotate_point(roof_slope.end_line_start, center, delta_degrees)
            roof_slope.end_line_end = _rotate_point(roof_slope.end_line_end, center, delta_degrees)
            if self._on_roof_slope_update is not None:
                self._on_roof_slope_update(roof_slope)


class ToggleDoorSwingCommand(BaseCommand):
    """Undoable command that toggles a door's opening direction."""

    def __init__(
        self,
        door: Door,
        new_swing_direction: str,
        on_update: Callable[[Door], None] | None = None,
    ) -> None:
        super().__init__("Toggle Door Swing")
        self._door = door
        self._old_swing_direction = door.swing_direction
        self._new_swing_direction = new_swing_direction
        self._on_update = on_update

    def redo(self) -> None:
        """Apply the new swing direction."""
        self._door.swing_direction = self._new_swing_direction
        if self._on_update is not None:
            self._on_update(self._door)

    def undo(self) -> None:
        """Restore the old swing direction."""
        self._door.swing_direction = self._old_swing_direction
        if self._on_update is not None:
            self._on_update(self._door)


def _rotate_point(point: Point, center: Point, delta_degrees: float) -> Point:
    """Rotate a point around a center by a given angle in degrees."""
    angle = radians(delta_degrees)
    offset_x = point.x - center.x
    offset_y = point.y - center.y
    cos_angle = cos(angle)
    sin_angle = sin(angle)
    return Point(
        center.x + offset_x * cos_angle - offset_y * sin_angle,
        center.y + offset_x * sin_angle + offset_y * cos_angle,
    )


def _roof_slope_center(roof_slope: RoofSlope) -> Point:
    """Return the geometric center of a roof slope boundary quad."""
    points = [
        roof_slope.start_line_start,
        roof_slope.start_line_end,
        roof_slope.end_line_start,
        roof_slope.end_line_end,
    ]
    return Point(
        sum(point.x for point in points) / 4.0,
        sum(point.y for point in points) / 4.0,
    )


def _point_near_any_wall(point: object, walls: list[Wall], tolerance: float = 5.0) -> bool:
    """Return True when point lies on or close to any wall center line segment."""
    from geometry.point import Point

    if not isinstance(point, Point):
        return False

    for wall in walls:
        ax, ay = wall.start.x, wall.start.y
        bx, by = wall.end.x, wall.end.y
        px, py = point.x, point.y

        abx = bx - ax
        aby = by - ay
        ab_len_sq = abx * abx + aby * aby
        if ab_len_sq <= 1e-9:
            continue

        apx = px - ax
        apy = py - ay
        t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_len_sq))
        cx = ax + t * abx
        cy = ay + t * aby
        dx = px - cx
        dy = py - cy
        if dx * dx + dy * dy <= tolerance * tolerance:
            return True

    return False


class CreateDimensionCommand(BaseCommand):
    """Undoable command that appends/removes a dimension from a floor."""

    def __init__(
        self,
        floor: Floor,
        dimension: Dimension,
        on_create: Callable[[Dimension], None] | None = None,
        on_delete: Callable[[Dimension], None] | None = None,
    ) -> None:
        super().__init__("Create Dimension")
        self._floor = floor
        self._dimension = dimension
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Append dimension to floor and notify view callback."""
        if not any(existing.id == self._dimension.id for existing in self._floor.dimensions):
            self._floor.dimensions.append(self._dimension)
            if self._on_create is not None:
                self._on_create(self._dimension)

    def undo(self) -> None:
        """Remove dimension from floor and notify view callback."""
        for index, existing in enumerate(self._floor.dimensions):
            if existing.id == self._dimension.id:
                del self._floor.dimensions[index]
                if self._on_delete is not None:
                    self._on_delete(self._dimension)
                break


class DeleteDimensionsCommand(BaseCommand):
    """Undoable command that removes a list of dimensions from a floor."""

    def __init__(
        self,
        floor: Floor,
        dimensions: list[Dimension],
        on_create: Callable[[Dimension], None] | None = None,
        on_delete: Callable[[Dimension], None] | None = None,
    ) -> None:
        super().__init__("Delete Dimensions")
        self._floor = floor
        self._dimensions = dimensions
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Delete target dimensions from floor and notify view callback."""
        ids_to_remove = {dimension.id for dimension in self._dimensions}
        kept_dimensions: list[Dimension] = []

        for existing in self._floor.dimensions:
            if existing.id in ids_to_remove:
                if self._on_delete is not None:
                    self._on_delete(existing)
            else:
                kept_dimensions.append(existing)

        self._floor.dimensions = kept_dimensions

    def undo(self) -> None:
        """Restore deleted dimensions to floor and notify view callback."""
        existing_ids = {dimension.id for dimension in self._floor.dimensions}
        for dimension in self._dimensions:
            if dimension.id not in existing_ids:
                self._floor.dimensions.append(dimension)
                if self._on_create is not None:
                    self._on_create(dimension)


class CreateWindowCommand(BaseCommand):
    """Undoable command that appends/removes a window from a floor."""

    def __init__(
        self,
        floor: Floor,
        window: Window,
        on_create: Callable[[Window], None] | None = None,
        on_delete: Callable[[Window], None] | None = None,
    ) -> None:
        super().__init__("Create Window")
        self._floor = floor
        self._window = window
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Append window to floor and notify view callback."""
        if not any(existing.id == self._window.id for existing in self._floor.windows):
            self._floor.windows.append(self._window)
            if self._on_create is not None:
                self._on_create(self._window)

    def undo(self) -> None:
        """Remove window from floor and notify view callback."""
        for index, existing in enumerate(self._floor.windows):
            if existing.id == self._window.id:
                del self._floor.windows[index]
                if self._on_delete is not None:
                    self._on_delete(self._window)
                break


class CreateDoorCommand(BaseCommand):
    """Undoable command that appends/removes a door from a floor."""

    def __init__(
        self,
        floor: Floor,
        door: Door,
        on_create: Callable[[Door], None] | None = None,
        on_delete: Callable[[Door], None] | None = None,
    ) -> None:
        super().__init__("Create Door")
        self._floor = floor
        self._door = door
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Append door to floor and notify view callback."""
        if not any(existing.id == self._door.id for existing in self._floor.doors):
            self._floor.doors.append(self._door)
            if self._on_create is not None:
                self._on_create(self._door)

    def undo(self) -> None:
        """Remove door from floor and notify view callback."""
        for index, existing in enumerate(self._floor.doors):
            if existing.id == self._door.id:
                del self._floor.doors[index]
                if self._on_delete is not None:
                    self._on_delete(self._door)
                break


class CreateOpeningCommand(BaseCommand):
    """Undoable command that appends/removes an opening from a floor."""

    def __init__(
        self,
        floor: Floor,
        opening: Opening,
        on_create: Callable[[Opening], None] | None = None,
        on_delete: Callable[[Opening], None] | None = None,
    ) -> None:
        super().__init__("Create Opening")
        self._floor = floor
        self._opening = opening
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Append opening to floor and notify view callback."""
        if not any(existing.id == self._opening.id for existing in self._floor.openings):
            self._floor.openings.append(self._opening)
            if self._on_create is not None:
                self._on_create(self._opening)

    def undo(self) -> None:
        """Remove opening from floor and notify view callback."""
        for index, existing in enumerate(self._floor.openings):
            if existing.id == self._opening.id:
                del self._floor.openings[index]
                if self._on_delete is not None:
                    self._on_delete(self._opening)
                break


class CreateStairCommand(BaseCommand):
    """Undoable command that appends/removes a stair from a floor."""

    def __init__(
        self,
        floor: Floor,
        stair: Stair,
        on_create: Callable[[Stair], None] | None = None,
        on_delete: Callable[[Stair], None] | None = None,
    ) -> None:
        super().__init__("Create Stair")
        self._floor = floor
        self._stair = stair
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Append stair to floor and notify view callback."""
        if not any(existing.id == self._stair.id for existing in self._floor.stairs):
            self._floor.stairs.append(self._stair)
            if self._on_create is not None:
                self._on_create(self._stair)

    def undo(self) -> None:
        """Remove stair from floor and notify view callback."""
        for index, existing in enumerate(self._floor.stairs):
            if existing.id == self._stair.id:
                del self._floor.stairs[index]
                if self._on_delete is not None:
                    self._on_delete(self._stair)
                break


class CreateRoofSlopeCommand(BaseCommand):
    """Undoable command that appends/removes a roof slope from a floor."""

    def __init__(
        self,
        floor: Floor,
        roof_slope: RoofSlope,
        on_create: Callable[[RoofSlope], None] | None = None,
        on_delete: Callable[[RoofSlope], None] | None = None,
    ) -> None:
        super().__init__("Create Roof Slope")
        self._floor = floor
        self._roof_slope = roof_slope
        self._on_create = on_create
        self._on_delete = on_delete

    def redo(self) -> None:
        """Append roof slope to floor and notify view callback."""
        if not any(existing.id == self._roof_slope.id for existing in self._floor.roof_slopes):
            self._floor.roof_slopes.append(self._roof_slope)
            if self._on_create is not None:
                self._on_create(self._roof_slope)

    def undo(self) -> None:
        """Remove roof slope from floor and notify view callback."""
        for index, existing in enumerate(self._floor.roof_slopes):
            if existing.id == self._roof_slope.id:
                del self._floor.roof_slopes[index]
                if self._on_delete is not None:
                    self._on_delete(self._roof_slope)
                break


class DeleteFloorSelectionCommand(BaseCommand):
    """Undoable command deleting mixed floor selection with wall-linked cascades."""

    def __init__(
        self,
        floor: Floor,
        walls: list[Wall],
        dimensions: list[Dimension],
        windows: list[Window],
        doors: list[Door],
        openings: list[Opening],
        stairs: list[Stair],
        roof_slopes: list[RoofSlope],
    ) -> None:
        super().__init__("Delete Selection")
        self._floor = floor
        self._walls = list(walls)
        self._dimensions = list(dimensions)
        self._windows = list(windows)
        self._doors = list(doors)
        self._openings = list(openings)
        self._stairs = list(stairs)
        self._roof_slopes = list(roof_slopes)

        wall_ids = {wall.id for wall in self._walls}
        self._cascade_windows = [w for w in floor.windows if w.wall_id in wall_ids]
        self._cascade_doors = [d for d in floor.doors if d.wall_id in wall_ids]
        self._cascade_openings = [o for o in floor.openings if o.wall_id in wall_ids]
        self._cascade_dimensions = [
            d
            for d in floor.dimensions
            if d.is_manual
            and (
                _point_near_any_wall(d.start, self._walls)
                or _point_near_any_wall(d.end, self._walls)
            )
        ]

    def redo(self) -> None:
        """Delete selected and cascaded objects from floor."""
        self._floor.walls = [
            wall for wall in self._floor.walls if wall.id not in {w.id for w in self._walls}
        ]
        removed_dimension_ids = {d.id for d in self._dimensions + self._cascade_dimensions}
        self._floor.dimensions = [
            d for d in self._floor.dimensions if d.id not in removed_dimension_ids
        ]
        self._floor.windows = [
            w
            for w in self._floor.windows
            if w.id
            not in {window.id for window in self._windows + self._cascade_windows}
        ]
        self._floor.doors = [
            d
            for d in self._floor.doors
            if d.id not in {door.id for door in self._doors + self._cascade_doors}
        ]
        self._floor.openings = [
            o
            for o in self._floor.openings
            if o.id not in {op.id for op in self._openings + self._cascade_openings}
        ]
        self._floor.stairs = [
            stair for stair in self._floor.stairs if stair.id not in {i.id for i in self._stairs}
        ]
        self._floor.roof_slopes = [
            r for r in self._floor.roof_slopes if r.id not in {i.id for i in self._roof_slopes}
        ]

    def undo(self) -> None:
        """Restore selected and cascaded objects to floor."""
        self._restore_unique(self._floor.walls, self._walls)
        self._restore_unique(self._floor.dimensions, self._dimensions + self._cascade_dimensions)
        self._restore_unique(self._floor.windows, self._windows + self._cascade_windows)
        self._restore_unique(self._floor.doors, self._doors + self._cascade_doors)
        self._restore_unique(self._floor.openings, self._openings + self._cascade_openings)
        self._restore_unique(self._floor.stairs, self._stairs)
        self._restore_unique(self._floor.roof_slopes, self._roof_slopes)

    @staticmethod
    def _restore_unique(target: list[TModel], items: list[TModel]) -> None:
        existing_ids = {item.id for item in target}
        for item in items:
            item_id = item.id
            if item_id not in existing_ids:
                target.append(item)
                existing_ids.add(item_id)

class ChangeObjectsPropertyCommand(BaseCommand):
    """Undoable command that changes a property value for a single object."""
    
    def __init__(
        self,
        obj: object,
        property_name: str,
        new_value: object,
        on_update: Callable[[object], None] | None = None,
    ) -> None:
        super().__init__(f"Change {property_name}")
        self._obj = obj
        self._property_name = property_name
        self._new_value = new_value
        self._old_value = getattr(obj, property_name, None)
        self._on_update = on_update

    def redo(self) -> None:
        """Apply the new property value."""
        setattr(self._obj, self._property_name, self._new_value)
        if self._on_update is not None:
            self._on_update(self._obj)

    def undo(self) -> None:
        """Restore the old property value."""
        setattr(self._obj, self._property_name, self._old_value)
        if self._on_update is not None:
            self._on_update(self._obj)
