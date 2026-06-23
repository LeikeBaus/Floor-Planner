"""QGraphicsView implementation with zoom, pan, and coordinate conversion helpers."""

from __future__ import annotations

import math
from typing import Protocol

from PyQt6.QtCore import QPoint, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QUndoCommand, QWheelEvent
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsView,
)
from PyQt6.QtGui import QPolygonF

from models.commands import (
    CreateDimensionCommand,
    CreateDoorCommand,
    CreateOpeningCommand,
    CreateRoofSlopeCommand,
    CreateStairCommand,
    CreateWallCommand,
    CreateWindowCommand,
    DeleteFloorSelectionCommand,
    MoveDimensionsCommand,
    MoveHostedObjectsCommand,
    MoveWallsCommand,
    RotateSelectionCommand,
    ToggleDoorSwingCommand,
)
from geometry.point import Point
from models.dimension import Dimension
from models.door import Door
from models.opening import Opening
from models.roof_slope import RoofSlope
from models.stair import Stair
from models.wall import Wall, WallType
from models.window import Window
from services.snap_service import SnapService
from services.wall_service import WallService
from views.scene.drawing_scene import DrawingScene


class WallCallbacks(Protocol):
    """Callback contract for wall and dimension notifications."""

    def on_wall_created(self, wall: Wall) -> None:
        """Handle wall creation event."""

    def on_wall_deleted(self, wall: Wall) -> None:
        """Handle wall deletion event."""

    def on_wall_updated(self, wall: Wall) -> None:
        """Handle wall update event."""

    def on_dimension_created(self, dimension: Dimension) -> None:
        """Handle dimension creation event."""

    def on_dimension_deleted(self, dimension: Dimension) -> None:
        """Handle dimension deletion event."""

    def on_dimension_updated(self, dimension: Dimension) -> None:
        """Handle dimension update event."""

    def on_window_created(self, window: Window) -> None:
        """Handle window creation event."""

    def on_window_deleted(self, window: Window) -> None:
        """Handle window deletion event."""

    def on_window_updated(self, window: Window) -> None:
        """Handle window update event."""

    def on_door_created(self, door: Door) -> None:
        """Handle door creation event."""

    def on_door_deleted(self, door: Door) -> None:
        """Handle door deletion event."""

    def on_door_updated(self, door: Door) -> None:
        """Handle door update event."""

    def on_opening_created(self, opening: Opening) -> None:
        """Handle opening creation event."""

    def on_opening_deleted(self, opening: Opening) -> None:
        """Handle opening deletion event."""

    def on_opening_updated(self, opening: Opening) -> None:
        """Handle opening update event."""

    def on_stair_created(self, stair: Stair) -> None:
        """Handle stair creation event."""

    def on_stair_deleted(self, stair: Stair) -> None:
        """Handle stair deletion event."""

    def on_stair_updated(self, stair: Stair) -> None:
        """Handle stair update event."""

    def on_roof_slope_created(self, roof_slope: RoofSlope) -> None:
        """Handle roof slope creation event."""

    def on_roof_slope_deleted(self, roof_slope: RoofSlope) -> None:
        """Handle roof slope deletion event."""

    def on_roof_slope_updated(self, roof_slope: RoofSlope) -> None:
        """Handle roof slope update event."""


class ToolMode:
    """Current interactive tool modes for the drawing view."""

    SELECT = "SELECT"
    WALL = "WALL"
    DIMENSION = "DIMENSION"
    WINDOW = "WINDOW"
    DOOR = "DOOR"
    OPENING = "OPENING"
    STAIR = "STAIR"
    ROOF_SLOPE = "ROOF_SLOPE"


class CommandSink(Protocol):
    """Minimal interface implemented by command stacks."""

    def push(self, command: QUndoCommand | None) -> None:
        """Push command onto stack."""


class DrawingView(QGraphicsView):
    """Main drawing viewport with CAD-like interaction behavior."""

    cursor_world_changed = pyqtSignal(float, float)
    wall_preview_length_changed = pyqtSignal(float)
    snap_debug_changed = pyqtSignal(bool, float, float)

    def __init__(self, scene: DrawingScene) -> None:
        super().__init__(scene)
        self._is_panning = False
        self._last_pan_pos = QPoint()
        self._zoom_factor = 1.15
        self._min_zoom = 0.02
        self._max_zoom = 8.0
        self._tool_mode: str = ToolMode.SELECT
        self._wall_start_point: Point | None = None
        self._wall_preview_item: QGraphicsPolygonItem | None = None
        self._dimension_start_point: Point | None = None
        self._dimension_end_point: Point | None = None
        self._dimension_preview_item: QGraphicsLineItem | None = None
        self._dimension_visible: bool = True
        self._dimension_opacity: float = 0.5
        self._default_exterior_wall_thickness: float = 300.0
        self._default_interior_wall_thickness: float = 110.0
        self._current_wall_type: WallType = WallType.EXTERIOR
        self._window_wall: Wall | None = None
        self._window_position: float | None = None
        self._door_wall: Wall | None = None
        self._door_position: float | None = None
        self._wall_service = WallService()
        self._snap_service = SnapService()
        self._snap_enabled = True
        self._snap_distance_mm = 200.0
        self._angle_snap_increment: float = 15.0
        self._is_drag_moving = False
        self._drag_start_world: Point | None = None
        self._drag_last_world: Point | None = None
        self._drag_cursor_offset: Point | None = None
        self._drag_selected_walls: list[Wall] = []
        self._drag_selected_stairs: list[Stair] = []
        self._drag_selected_roof_slopes: list[RoofSlope] = []
        self._drag_selected_windows: list[Window] = []
        self._drag_selected_doors: list[Door] = []
        self._drag_selected_openings: list[Opening] = []
        self._drag_selected_dimensions: list[Dimension] = []
        self._drag_window_start_positions: dict[str, float] = {}
        self._drag_door_start_positions: dict[str, float] = {}
        self._drag_opening_start_positions: dict[str, float] = {}
        self._drag_dimension_start_offsets: dict[str, float] = {}
        self._drag_dimension_start_points: dict[str, Point] = {}
        self._drag_mode_kind: str | None = None
        self._drag_rotation_origin: Point | None = None
        self._drag_rotation_start_angle: float = 0.0
        self._drag_rotation_applied_degrees: float = 0.0
        self._debug_snap_enabled = False
        self._command_sink: CommandSink | None = None
        self._wall_callbacks: WallCallbacks | None = None

        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setMouseTracking(True)
        viewport = self.viewport()
        if viewport is not None:
            viewport.setMouseTracking(True)

    def set_tool_mode(self, mode: str) -> None:
        """Set active drawing interaction mode."""
        self._tool_mode = mode
        self._reset_wall_drawing_state()
        self._reset_dimension_drawing_state()
        if mode == ToolMode.SELECT:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        self._sync_scene_overlay_state()

    def set_command_sink(self, command_sink: CommandSink) -> None:
        """Assign object that owns push(command) API, typically QUndoStack."""
        self._command_sink = command_sink

    def set_wall_callbacks(self, callbacks: WallCallbacks) -> None:
        """Assign wall callbacks for side effects after commands execute."""
        self._wall_callbacks = callbacks

    def set_snap_options(self, enabled: bool, distance_mm: float) -> None:
        """Set snap enablement; snap radius is managed internally by zoom-aware logic."""
        self._snap_enabled = enabled
        self._snap_service.set_snap_enabled(enabled)
        self._snap_service.set_snap_distance(distance_mm)

    def set_dimension_options(self, visible: bool, opacity: float) -> None:
        """Set default properties for newly created manual dimensions."""
        self._dimension_visible = visible
        self._dimension_opacity = max(0.0, min(1.0, opacity))

    def set_default_wall_thickness(self, thickness_mm: float) -> None:
        """Backwards-compatible setter for the exterior wall default."""
        self._default_exterior_wall_thickness = max(1.0, thickness_mm)

    def set_wall_defaults(self, exterior_thickness_mm: float, interior_thickness_mm: float) -> None:
        """Set wall creation defaults for both supported wall types."""
        self._default_exterior_wall_thickness = max(1.0, exterior_thickness_mm)
        self._default_interior_wall_thickness = max(1.0, interior_thickness_mm)
        self._sync_scene_overlay_state()

    def set_wall_creation_type(self, wall_type: WallType) -> None:
        """Set the wall type used by the wall creation tool."""
        self._current_wall_type = wall_type
        self._sync_scene_overlay_state()

    def set_debug_snap_enabled(self, enabled: bool) -> None:
        """Enable or disable debug visualization of the active snap point."""
        self._debug_snap_enabled = enabled
        if not enabled:
            self._publish_debug_snap_point(None)

    def set_angle_snap_increment(self, increment_degrees: float) -> None:
        """Set directional angle snap increment in degrees."""
        self._angle_snap_increment = max(1.0, min(90.0, increment_degrees))
        self._snap_service.set_angle_snap_increment(self._angle_snap_increment)

    def wheelEvent(self, event: QWheelEvent | None) -> None:  # noqa: N802
        """Zoom in/out around cursor while clamping scale to safe bounds."""
        if event is None:
            return

        delta = event.angleDelta().y()
        factor = self._zoom_factor if delta > 0 else 1 / self._zoom_factor

        current_scale = self.transform().m11()
        new_scale = current_scale * factor
        if self._min_zoom <= new_scale <= self._max_zoom:
            self.scale(factor, factor)

        event.accept()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Start middle-mouse panning while preserving default selection behavior."""
        if event is None:
            return

        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.WALL
            and not self._is_panning
        ):
            self._handle_wall_click(event.pos())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.DIMENSION
            and not self._is_panning
        ):
            self._handle_dimension_click(event.pos())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.WINDOW
            and not self._is_panning
        ):
            self._handle_window_click(event.pos())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.DOOR
            and not self._is_panning
        ):
            self._handle_door_click(event.pos())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.OPENING
            and not self._is_panning
        ):
            self._handle_opening_click(event.pos())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.STAIR
            and not self._is_panning
        ):
            self._handle_stair_click(event.pos())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.ROOF_SLOPE
            and not self._is_panning
        ):
            self._handle_roof_slope_click(event.pos())
            event.accept()
            return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool_mode == ToolMode.SELECT
            and not self._is_panning
        ):
            if self._try_begin_drag_move(
                event.pos(),
                rotate=bool(event.modifiers() & Qt.KeyboardModifier.AltModifier),
            ):
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Toggle door swing direction on double click."""
        if event is None:
            return

        if event.button() == Qt.MouseButton.LeftButton and self._tool_mode == ToolMode.SELECT:
            if self._toggle_door_on_double_click(event.pos()):
                event.accept()
                return

        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Pan viewport by scrollbar offset while middle mouse is held."""
        if event is None:
            return

        scene = self.scene()

        if self._is_panning:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            horizontal = self.horizontalScrollBar()
            vertical = self.verticalScrollBar()
            moved_by_scrollbar = False

            if horizontal is not None:
                previous = horizontal.value()
                horizontal.setValue(horizontal.value() - delta.x())
                moved_by_scrollbar = moved_by_scrollbar or (horizontal.value() != previous)
            if vertical is not None:
                previous = vertical.value()
                vertical.setValue(vertical.value() - delta.y())
                moved_by_scrollbar = moved_by_scrollbar or (vertical.value() != previous)

            if not moved_by_scrollbar:
                center = self.mapToScene(self.viewport().rect().center())
                target = self.mapToScene(self.viewport().rect().center() - delta)
                self.centerOn(center + (center - target))

            if isinstance(scene, DrawingScene):
                scene.update()

            event.accept()
            return

        if self._is_drag_moving:
            self._update_drag_move(event.pos())
            if isinstance(scene, DrawingScene):
                scene.update()
            event.accept()
            return

        world = self.mapToScene(event.pos())
        raw_point = Point(world.x(), world.y())
        snapped = self._cursor_snap_point(raw_point)
        self.cursor_world_changed.emit(snapped.x, snapped.y)

        if self._tool_mode == ToolMode.WALL and self._wall_start_point is not None:
            self._update_wall_preview(self._snap_to_angle(self._wall_start_point, snapped))

        if self._tool_mode == ToolMode.DIMENSION and self._dimension_start_point is not None:
            preview_point = raw_point if self._dimension_end_point is not None else snapped
            if self._dimension_end_point is not None:
                self._publish_debug_snap_point(None)
            self._update_dimension_preview(preview_point)

        if isinstance(scene, DrawingScene):
            scene.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Stop middle-mouse panning and restore cursor."""
        if event is None:
            return

        if event.button() == Qt.MouseButton.MiddleButton and self._is_panning:
            self._is_panning = False
            if self._tool_mode == ToolMode.SELECT:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton and self._is_drag_moving:
            self._finish_drag_move(event.pos())
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def view_to_world(self, view_point: QPoint) -> QPointF:
        """Convert viewport coordinates to world coordinates in millimeters."""
        return self.mapToScene(view_point)

    def world_to_view(self, world_point: QPointF) -> QPoint:
        """Convert world coordinates in millimeters to viewport coordinates."""
        return self.mapFromScene(world_point)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        """Cancel pending wall draw with Escape."""
        if event is not None and event.key() == Qt.Key.Key_Escape:
            if self._tool_mode == ToolMode.WALL:
                self._reset_wall_drawing_state()
                event.accept()
                return
            if self._tool_mode == ToolMode.DIMENSION:
                self._reset_dimension_drawing_state()
                event.accept()
                return

        super().keyPressEvent(event)

    def delete_selected_items(self) -> None:
        """Delete current selection as one undoable command."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene) or self._command_sink is None:
            return
        floor = scene.active_floor
        if floor is None:
            return

        command = DeleteFloorSelectionCommand(
            floor=floor,
            walls=scene.selected_walls(),
            dimensions=scene.selected_manual_dimensions(),
            windows=scene.selected_windows(),
            doors=scene.selected_doors(),
            openings=scene.selected_openings(),
            stairs=scene.selected_stairs(),
            roof_slopes=scene.selected_roof_slopes(),
        )
        self._command_sink.push(command)
        scene.refresh_walls()
        scene.refresh_windows()
        scene.refresh_doors()
        scene.refresh_openings()
        scene.refresh_stairs()
        scene.refresh_roof_slopes()
        scene.refresh_rooms()
        scene.refresh_dimensions()
        scene.refresh_height_zones()

    def _handle_wall_click(self, view_pos: QPoint) -> None:
        """Handle two-click wall creation workflow."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        floor = scene.active_floor
        if floor is None or self._command_sink is None:
            return

        world = self.mapToScene(view_pos)
        raw_point = Point(x=world.x(), y=world.y())
        print(f"Raw click at world coordinates: ({raw_point.x:.2f}, {raw_point.y:.2f})")
        point = self._snap_dimension_endpoint_point(raw_point)
        print(f"Clicked at world coordinates: ({point.x:.2f}, {point.y:.2f})")

        if self._wall_start_point is None:
            self._wall_start_point = point
            self._update_wall_preview(point)
            self.wall_preview_length_changed.emit(0.0)
            return

        point = self._snap_to_angle(self._wall_start_point, point)

        thickness = self._current_wall_thickness()
        dx = point.x - self._wall_start_point.x
        dy = point.y - self._wall_start_point.y
        length_mm = math.hypot(dx, dy)
        if thickness <= 0.0 or length_mm <= 1e-6:
            self._reset_wall_drawing_state()
            return

        try:
            wall = self._wall_service.create_wall(
                start=self._wall_start_point,
                end=point,
                thickness=thickness,
                wall_type=self._current_wall_type,
            )
        except ValueError:
            self._reset_wall_drawing_state()
            return

        command = CreateWallCommand(
            floor=floor,
            wall=wall,
            on_create=self._wall_callbacks.on_wall_created if self._wall_callbacks else None,
            on_delete=self._wall_callbacks.on_wall_deleted if self._wall_callbacks else None,
        )
        self._command_sink.push(command)
        self._reset_wall_drawing_state()

    def _handle_dimension_click(self, view_pos: QPoint) -> None:
        """Handle three-click manual dimension creation workflow."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        floor = scene.active_floor
        if floor is None or self._command_sink is None:
            return

        world = self.mapToScene(view_pos)
        raw_point = Point(x=world.x(), y=world.y())
        point = self._snap_dimension_endpoint_point(raw_point)

        if self._dimension_start_point is None:
            self._dimension_start_point = point
            self._update_dimension_preview(point)
            self.wall_preview_length_changed.emit(0.0)
            return

        if self._dimension_end_point is None:
            dx = point.x - self._dimension_start_point.x
            dy = point.y - self._dimension_start_point.y
            length_mm = (dx * dx + dy * dy) ** 0.5
            if length_mm <= 0.001:
                self._reset_dimension_drawing_state()
                return

            self._dimension_end_point = point
            self._update_dimension_preview(point)
            self.wall_preview_length_changed.emit(length_mm)
            return

        point = raw_point
        self._publish_debug_snap_point(None)

        dx = self._dimension_end_point.x - self._dimension_start_point.x
        dy = self._dimension_end_point.y - self._dimension_start_point.y
        length_mm = (dx * dx + dy * dy) ** 0.5
        if length_mm <= 0.001:
            self._reset_dimension_drawing_state()
            return

        nx = -dy / length_mm
        ny = dx / length_mm
        signed_offset = (
            (point.x - self._dimension_start_point.x) * nx
            + (point.y - self._dimension_start_point.y) * ny
        )

        if abs(signed_offset) < 1.0:
            signed_offset = 150.0

        display_start = Point(
            x=self._dimension_start_point.x + nx * signed_offset,
            y=self._dimension_start_point.y + ny * signed_offset,
        )
        display_end = Point(
            x=self._dimension_end_point.x + nx * signed_offset,
            y=self._dimension_end_point.y + ny * signed_offset,
        )

        dimension = Dimension(
            start=self._dimension_start_point,
            end=self._dimension_end_point,
            value=length_mm,
            display_start=display_start,
            display_end=display_end,
            is_manual=True,
            visible=self._dimension_visible,
            opacity=self._dimension_opacity,
        )
        command = CreateDimensionCommand(
            floor=floor,
            dimension=dimension,
            on_create=self._wall_callbacks.on_dimension_created if self._wall_callbacks else None,
            on_delete=self._wall_callbacks.on_dimension_deleted if self._wall_callbacks else None,
        )
        self._command_sink.push(command)
        self._reset_dimension_drawing_state()

    def _handle_window_click(self, view_pos: QPoint) -> None:
        """Handle window placement on a wall via single click."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        floor = scene.active_floor
        if floor is None or self._command_sink is None:
            return

        world = self.mapToScene(view_pos)
        point = self._snap_point(Point(x=world.x(), y=world.y()))

        closest_wall = self._find_nearest_wall_projection(point, floor.walls)
        if closest_wall is None:
            return

        wall, t = closest_wall
        position_mm = t * wall.length

        window = Window(
            wall_id=wall.id,
            position=position_mm,
            width=1000.0,
            height=1200.0,
        )
        command = CreateWindowCommand(
            floor=floor,
            window=window,
            on_create=self._wall_callbacks.on_window_created if self._wall_callbacks else None,
            on_delete=self._wall_callbacks.on_window_deleted if self._wall_callbacks else None,
        )
        self._command_sink.push(command)

    def _handle_door_click(self, view_pos: QPoint) -> None:
        """Handle door placement on a wall via single click."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        floor = scene.active_floor
        if floor is None or self._command_sink is None:
            return

        world = self.mapToScene(view_pos)
        point = self._snap_point(Point(x=world.x(), y=world.y()))

        closest_wall = self._find_nearest_wall_projection(point, floor.walls)
        if closest_wall is None:
            return

        wall, t = closest_wall
        position_mm = t * wall.length

        door = Door(
            wall_id=wall.id,
            position=position_mm,
            width=1000.0,
            height=2100.0,
            swing_direction="right_in",
        )
        command = CreateDoorCommand(
            floor=floor,
            door=door,
            on_create=self._wall_callbacks.on_door_created if self._wall_callbacks else None,
            on_delete=self._wall_callbacks.on_door_deleted if self._wall_callbacks else None,
        )
        self._command_sink.push(command)

    def _handle_opening_click(self, view_pos: QPoint) -> None:
        """Handle opening placement on a wall via single click."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        floor = scene.active_floor
        if floor is None or self._command_sink is None:
            return

        world = self.mapToScene(view_pos)
        point = self._snap_point(Point(x=world.x(), y=world.y()))

        closest_wall = self._find_nearest_wall_projection(point, floor.walls)
        if closest_wall is None:
            return

        wall, t = closest_wall
        position_mm = t * wall.length

        opening = Opening(
            wall_id=wall.id,
            position=position_mm,
            width=1500.0,
            height=2400.0,
            opening_type="passage",
        )
        command = CreateOpeningCommand(
            floor=floor,
            opening=opening,
            on_create=self._wall_callbacks.on_opening_created if self._wall_callbacks else None,
            on_delete=self._wall_callbacks.on_opening_deleted if self._wall_callbacks else None,
        )
        self._command_sink.push(command)

    def _handle_stair_click(self, view_pos: QPoint) -> None:
        """Handle stair placement via single click (free placement on floor)."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        floor = scene.active_floor
        if floor is None or self._command_sink is None:
            return

        world = self.mapToScene(view_pos)
        point = self._snap_point(Point(x=world.x(), y=world.y()))

        # Create stair at clicked position (free-form placement)
        stair = Stair(
            floor_id_from=floor.id,
            floor_id_to="",  # To be set by user in properties
            position_x=point.x,
            position_y=point.y,
            width=1200.0,
            depth=1200.0,
            stair_type="straight",
            orientation_degrees=0.0,
        )
        command = CreateStairCommand(
            floor=floor,
            stair=stair,
            on_create=self._wall_callbacks.on_stair_created if self._wall_callbacks else None,
            on_delete=self._wall_callbacks.on_stair_deleted if self._wall_callbacks else None,
        )
        self._command_sink.push(command)

    def _handle_roof_slope_click(self, view_pos: QPoint) -> None:
        """Handle roof slope placement via single click."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        floor = scene.active_floor
        if floor is None or self._command_sink is None:
            return

        world = self.mapToScene(view_pos)
        point = self._snap_point(Point(x=world.x(), y=world.y()))

        half_width = 2000.0
        line_spacing = 3000.0
        roof_slope = RoofSlope(
            start_line_start=Point(point.x - half_width, point.y),
            start_line_end=Point(point.x + half_width, point.y),
            end_line_start=Point(point.x - half_width, point.y + line_spacing),
            end_line_end=Point(point.x + half_width, point.y + line_spacing),
            height_start=2500.0,
            height_end=500.0,
        )
        command = CreateRoofSlopeCommand(
            floor=floor,
            roof_slope=roof_slope,
            on_create=self._wall_callbacks.on_roof_slope_created if self._wall_callbacks else None,
            on_delete=self._wall_callbacks.on_roof_slope_deleted if self._wall_callbacks else None,
        )
        self._command_sink.push(command)

    def _update_wall_preview(self, end: Point) -> None:
        """Render or refresh temporary preview polygon for current wall draw."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene) or self._wall_start_point is None:
            return

        if self._wall_preview_item is None:
            created_preview = QGraphicsPolygonItem()
            scene.addItem(created_preview)
            if created_preview is None:
                return

            self._wall_preview_item = created_preview
            pen = QPen(QColor("#F59E0B"))
            pen.setWidthF(1.8)
            pen.setCosmetic(True)
            self._wall_preview_item.setPen(pen)
            self._wall_preview_item.setBrush(QColor(245, 158, 11, 70))
            self._wall_preview_item.setZValue(30)

        preview = self._wall_preview_item
        if preview is None:
            return

        preview.setPolygon(
            self._wall_preview_polygon(
                self._wall_start_point,
                end,
                self._current_wall_thickness(),
            )
        )
        dx = end.x - self._wall_start_point.x
        dy = end.y - self._wall_start_point.y
        length_mm = (dx * dx + dy * dy) ** 0.5
        self.wall_preview_length_changed.emit(length_mm)

    def _update_dimension_preview(self, end: Point) -> None:
        """Render or refresh temporary preview line for current dimension draw."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene) or self._dimension_start_point is None:
            return

        if self._dimension_preview_item is None:
            created_preview = scene.addLine(0.0, 0.0, 0.0, 0.0)
            if created_preview is None:
                return

            self._dimension_preview_item = created_preview
            pen = QPen(QColor("#2563EB"))
            pen.setWidthF(1.5)
            pen.setCosmetic(True)
            pen.setStyle(Qt.PenStyle.DotLine)
            self._dimension_preview_item.setPen(pen)

        preview = self._dimension_preview_item
        if preview is None:
            return

        if self._dimension_end_point is None:
            preview.setLine(
                self._dimension_start_point.x,
                self._dimension_start_point.y,
                end.x,
                end.y,
            )
            dx = end.x - self._dimension_start_point.x
            dy = end.y - self._dimension_start_point.y
        else:
            dx = self._dimension_end_point.x - self._dimension_start_point.x
            dy = self._dimension_end_point.y - self._dimension_start_point.y
            length = (dx * dx + dy * dy) ** 0.5
            if length <= 1e-6:
                return
            nx = -dy / length
            ny = dx / length
            signed_offset = (
                (end.x - self._dimension_start_point.x) * nx
                + (end.y - self._dimension_start_point.y) * ny
            )
            preview.setLine(
                self._dimension_start_point.x + nx * signed_offset,
                self._dimension_start_point.y + ny * signed_offset,
                self._dimension_end_point.x + nx * signed_offset,
                self._dimension_end_point.y + ny * signed_offset,
            )

        length_mm = (dx * dx + dy * dy) ** 0.5
        self.wall_preview_length_changed.emit(length_mm)

    def _reset_wall_drawing_state(self) -> None:
        """Clear pending points and remove temporary preview item."""
        self._wall_start_point = None
        self.wall_preview_length_changed.emit(-1.0)
        if self._wall_preview_item is not None:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self._wall_preview_item)
            self._wall_preview_item = None

    def _reset_dimension_drawing_state(self) -> None:
        """Clear pending points and remove temporary dimension preview item."""
        self._dimension_start_point = None
        self._dimension_end_point = None
        self.wall_preview_length_changed.emit(-1.0)
        if self._dimension_preview_item is not None:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self._dimension_preview_item)
            self._dimension_preview_item = None

    def _find_nearest_wall_projection(
        self,
        point: Point,
        walls: list[Wall],
        max_distance: float = 500.0,
    ) -> tuple[Wall, float] | None:
        """Return nearest wall plus normalized projection factor in [0, 1]."""
        closest: tuple[Wall, float] | None = None
        closest_distance = float("inf")

        for wall in walls:
            wall_vec_x = wall.end.x - wall.start.x
            wall_vec_y = wall.end.y - wall.start.y
            wall_len_sq = wall_vec_x * wall_vec_x + wall_vec_y * wall_vec_y
            if wall_len_sq < 1e-6:
                continue

            point_vec_x = point.x - wall.start.x
            point_vec_y = point.y - wall.start.y
            t = max(
                0.0,
                min(1.0, (point_vec_x * wall_vec_x + point_vec_y * wall_vec_y) / wall_len_sq),
            )

            proj_x = wall.start.x + t * wall_vec_x
            proj_y = wall.start.y + t * wall_vec_y
            distance = ((proj_x - point.x) ** 2 + (proj_y - point.y) ** 2) ** 0.5
            if distance < closest_distance:
                closest_distance = distance
                closest = (wall, t)

        if closest is None or closest_distance > max_distance:
            return None
        return closest

    def _wall_preview_polygon(self, start: Point, end: Point, thickness: float) -> QPolygonF:
        """Build a rectangle polygon for a wall centerline and thickness."""
        dx = end.x - start.x
        dy = end.y - start.y
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return QPolygonF()

        half_thickness = thickness / 2.0
        nx = -dy / length
        ny = dx / length
        p1 = QPointF(start.x + nx * half_thickness, start.y + ny * half_thickness)
        p2 = QPointF(end.x + nx * half_thickness, end.y + ny * half_thickness)
        p3 = QPointF(end.x - nx * half_thickness, end.y - ny * half_thickness)
        p4 = QPointF(start.x - nx * half_thickness, start.y - ny * half_thickness)
        return QPolygonF([p1, p2, p3, p4])

    def _snap_point(self, point: Point) -> Point:
        """Snap world point to wall-aware targets when enabled."""
        return self._snap_service.snap_point(self, point)

    def _snap_dimension_endpoint_point(self, point: Point) -> Point:
        """Snap dimension start/end points to wall and hosted-object corners and edges."""
        return self._snap_service.snap_dimension_endpoint_point(self, point)

    def _snap_for_wall_creation(
        self,
        point: Point,
        walls: list[Wall],
        snap_distance: float,
    ) -> Point:
        """Snap new wall drawing to wall endpoints, attachments, side geometry, and angle."""
        return self._snap_service.snap_for_wall_creation(self, point, walls, snap_distance)

    def _snap_for_wall_movement(
        self,
        point: Point,
        walls: list[Wall],
        snap_distance: float,
    ) -> Point:
        """Snap moved walls to wall endpoints, attachments, side geometry, and grid."""
        return self._snap_service.snap_for_wall_movement(self, point, walls, snap_distance)

    def _snap_for_wall_hosted(
        self,
        point: Point,
        walls: list[Wall],
        snap_distance: float,
    ) -> Point:
        """Snap hosted-object placement only to walls and grid."""
        return self._snap_service.snap_for_wall_hosted(self, point, walls, snap_distance)

    def _snap_with_priority(
        self,
        point: Point,
        snap_distance: float,
        endpoint_targets: list[Point],
        attachment_targets: list[Point],
        midpoint_targets: list[Point],
        edge_segments: list[tuple[Point, Point]],
        centerline_segments: list[tuple[Point, Point]],
    ) -> Point | None:
        """Return nearest wall snap target according to intent-specific priority."""
        return self._snap_service.snap_with_priority(
            point,
            snap_distance,
            endpoint_targets,
            attachment_targets,
            midpoint_targets,
            edge_segments,
            centerline_segments,
        )

    def _walls_for_snap(self, scene: DrawingScene) -> list[Wall]:
        """Return walls from the active floor for snapping."""
        _unused_scene = scene
        return self._snap_service.walls_for_snap(self)

    def _wall_outline_points(self, wall: Wall) -> list[Point]:
        """Return the rectangle corners of a wall thickness footprint."""
        return self._snap_service.wall_outline_points(wall)

    def _wall_side_midpoints(self, wall: Wall) -> list[Point]:
        """Return midpoints of the wall's outer contour edges."""
        return self._snap_service.wall_side_midpoints(wall)

    def _wall_side_segments(self, wall: Wall) -> list[tuple[Point, Point]]:
        """Return the outer contour segments of a wall."""
        return self._snap_service.wall_side_segments(wall)

    def _wall_attachment_points(self, wall: Wall, attachment_width: float) -> list[Point]:
        """Return dynamic anchor points near wall corners."""
        return self._snap_service.wall_attachment_points(wall, attachment_width)

    def _current_wall_thickness(self) -> float:
        """Return the default thickness for the currently active wall tool."""
        return self._snap_service.current_wall_thickness(self)

    def _nearest_point(self, source: Point, targets: list[Point], radius: float) -> Point | None:
        """Return nearest target point within a radius."""
        return self._snap_service.nearest_point(source, targets, radius)

    def _nearest_segment_projection(
        self,
        source: Point,
        segments: list[tuple[Point, Point]],
        radius: float,
    ) -> Point | None:
        """Return the nearest projection onto a segment within a radius."""
        return self._snap_service.nearest_segment_projection(source, segments, radius)

    def _snap_grid(self, point: Point) -> Point:
        """Snap a point to a zoom-aware grid."""
        return self._snap_service.snap_grid(self, point)

    def _cursor_snap_point(self, point: Point) -> Point:
        """Return the snap point used for cursor feedback in the current interaction state."""
        if self._tool_mode == ToolMode.DIMENSION and self._dimension_end_point is None:
            return self._snap_dimension_endpoint_point(point)
        if self._tool_mode == ToolMode.DIMENSION and self._dimension_end_point is not None:
            self._publish_debug_snap_point(None)
            return point
        return self._snap_point(point)

    def _dimension_snap_targets(
        self,
        scene: DrawingScene,
    ) -> tuple[list[Point], list[tuple[Point, Point]]]:
        """Collect corners and edges used when snapping dimension endpoints."""
        floor = scene.active_floor
        if floor is None:
            return ([], [])

        corners: list[Point] = []
        edges: list[tuple[Point, Point]] = []

        for wall in floor.walls:
            wall_corners = self._wall_outline_points(wall)
            corners.extend(wall_corners)
            edges.extend(self._wall_side_segments(wall))

        hosted_specs = [
            (window.wall_id, window.position, window.width) for window in floor.windows
        ]
        hosted_specs.extend((door.wall_id, door.position, door.width) for door in floor.doors)
        hosted_specs.extend(
            (opening.wall_id, opening.position, opening.width) for opening in floor.openings
        )
        for wall_id, position, width in hosted_specs:
            wall = self._wall_for_id(floor.walls, wall_id)
            if wall is None:
                continue
            points = self._hosted_object_outline_points(wall, position, width)
            corners.extend(points)
            if len(points) == 4:
                edges.extend([(points[index], points[(index + 1) % 4]) for index in range(4)])

        return corners, edges

    def _hosted_object_outline_points(self, wall: Wall, position: float, width: float) -> list[Point]:
        """Return the outline rectangle corners of a wall-hosted object."""
        wall_dx = wall.end.x - wall.start.x
        wall_dy = wall.end.y - wall.start.y
        wall_length = math.hypot(wall_dx, wall_dy)
        if wall_length <= 1e-6:
            return []

        wall_ux = wall_dx / wall_length
        wall_uy = wall_dy / wall_length
        perp_ux = -wall_uy
        perp_uy = wall_ux

        center_x = wall.start.x + wall_ux * position
        center_y = wall.start.y + wall_uy * position
        half_width = width / 2.0
        half_depth = max(40.0, wall.thickness / 2.0)

        return [
            Point(
                center_x - wall_ux * half_width - perp_ux * half_depth,
                center_y - wall_uy * half_width - perp_uy * half_depth,
            ),
            Point(
                center_x + wall_ux * half_width - perp_ux * half_depth,
                center_y + wall_uy * half_width - perp_uy * half_depth,
            ),
            Point(
                center_x + wall_ux * half_width + perp_ux * half_depth,
                center_y + wall_uy * half_width + perp_uy * half_depth,
            ),
            Point(
                center_x - wall_ux * half_width + perp_ux * half_depth,
                center_y - wall_uy * half_width + perp_uy * half_depth,
            ),
        ]

    def _publish_debug_snap_point(self, point: Point | None) -> None:
        """Publish the current debug snap point to scene and status listeners."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        if not self._debug_snap_enabled or point is None:
            scene.set_debug_snap_point(None)
            self.snap_debug_changed.emit(False, 0.0, 0.0)
            return

        scene.set_debug_snap_point(point)
        self.snap_debug_changed.emit(True, point.x, point.y)

    def _sync_scene_overlay_state(self) -> None:
        """Synchronize marker overlay visibility with the current interaction mode."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene):
            return

        mode = "all" if (self._tool_mode != ToolMode.SELECT or self._is_drag_moving) else "selected"
        scene.set_snap_marker_mode(mode, self._current_wall_thickness())

    def _find_preview_start_wall_id(self) -> str | None:
        """Return wall id whose endpoint equals current start point, if any."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene) or self._wall_start_point is None:
            return None

        for endpoint, wall_id in scene.wall_endpoints():
            if endpoint == self._wall_start_point:
                return wall_id
        return None

    def _try_begin_drag_move(self, view_pos: QPoint, rotate: bool = False) -> bool:
        """Start drag move when clicking a pre-selected item a second time."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene) or self._command_sink is None:
            return False

        selected_walls = scene.selected_walls()
        selected_stairs = scene.selected_stairs()
        selected_roof_slopes = scene.selected_roof_slopes()
        selected_windows = scene.selected_windows()
        selected_doors = scene.selected_doors()
        selected_openings = scene.selected_openings()
        selected_dimensions = scene.selected_dimensions()
        if not (
            selected_walls
            or selected_stairs
            or selected_roof_slopes
            or selected_windows
            or selected_doors
            or selected_openings
            or selected_dimensions
        ):
            return False

        clicked_item = self.itemAt(view_pos)
        if clicked_item is None:
            return False

        # Check parent chain because many items are grouped.
        current: QGraphicsItem | None = clicked_item
        clicked_selected = False
        while current is not None:
            if current.isSelected():
                clicked_selected = True
                break
            current = current.parentItem()

        if not clicked_selected:
            return False

        world = self.mapToScene(view_pos)
        click_world = Point(world.x(), world.y())
        is_translate_drag = bool(selected_walls or selected_stairs or selected_roof_slopes)
        if rotate and is_translate_drag:
            self._drag_selected_walls = selected_walls
            self._drag_selected_stairs = selected_stairs
            self._drag_selected_roof_slopes = selected_roof_slopes
            rotation_origin = self._nearest_rotation_center(click_world)
            if rotation_origin is None:
                return False
            self._drag_start_world = rotation_origin
            self._drag_last_world = rotation_origin
            self._drag_cursor_offset = None
            self._drag_selected_windows = []
            self._drag_selected_doors = []
            self._drag_selected_openings = []
            self._drag_selected_dimensions = []
            self._drag_rotation_origin = rotation_origin
            self._drag_rotation_start_angle = math.atan2(
                click_world.y - rotation_origin.y,
                click_world.x - rotation_origin.x,
            )
            self._drag_rotation_applied_degrees = 0.0
            self._drag_mode_kind = "rotate"
            self._is_drag_moving = True
            self.setCursor(Qt.CursorShape.CrossCursor)
            self._sync_scene_overlay_state()
            return True

        anchor = self._nearest_selection_corner(click_world) if is_translate_drag else click_world
        self._drag_start_world = anchor
        self._drag_last_world = self._drag_start_world
        self._drag_cursor_offset = Point(
            click_world.x - anchor.x,
            click_world.y - anchor.y,
        )
        self._drag_selected_walls = selected_walls
        self._drag_selected_stairs = selected_stairs
        self._drag_selected_roof_slopes = selected_roof_slopes
        self._drag_selected_windows = selected_windows
        self._drag_selected_doors = selected_doors
        self._drag_selected_openings = selected_openings
        self._drag_selected_dimensions = selected_dimensions
        self._drag_window_start_positions = {
            window.id: window.position for window in selected_windows
        }
        self._drag_door_start_positions = {door.id: door.position for door in selected_doors}
        self._drag_opening_start_positions = {
            opening.id: opening.position for opening in selected_openings
        }
        self._drag_dimension_start_offsets = {
            dimension.id: self._dimension_signed_offset(dimension)
            for dimension in selected_dimensions
        }
        self._drag_dimension_start_points = {
            dimension.id: (dimension.display_start or dimension.start)
            for dimension in selected_dimensions
        }
        self._drag_mode_kind = (
            "translate"
            if is_translate_drag
            else "hosted"
            if (selected_windows or selected_doors or selected_openings)
            else "dimension"
        )
        self._is_drag_moving = True
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self._sync_scene_overlay_state()
        return True

    def _update_drag_move(self, view_pos: QPoint) -> None:
        """Move selected walls live while dragging, snapped to movement constraints."""
        scene = self.scene()
        if not isinstance(scene, DrawingScene) or self._drag_start_world is None:
            return

        if self._drag_mode_kind == "rotate":
            self._update_rotate_drag(view_pos)
            return
        if self._drag_mode_kind == "hosted":
            self._update_hosted_drag(view_pos)
            return
        if self._drag_mode_kind == "dimension":
            self._update_dimension_drag(view_pos)
            return
        if (
            self._drag_last_world is None
            or not (
                self._drag_selected_walls
                or self._drag_selected_stairs
                or self._drag_selected_roof_slopes
            )
        ):
            return

        current_qt = self.mapToScene(view_pos)
        current_world = Point(current_qt.x(), current_qt.y())
        snapped_current = self._snap_point(current_world)

        delta_x = snapped_current.x - self._drag_last_world.x
        delta_y = snapped_current.y - self._drag_last_world.y
        if abs(delta_x) < 0.001 and abs(delta_y) < 0.001:
            return

        from geometry.point import Point as GeoPoint

        for wall in self._drag_selected_walls:
            wall.start = GeoPoint(wall.start.x + delta_x, wall.start.y + delta_y)
            wall.end = GeoPoint(wall.end.x + delta_x, wall.end.y + delta_y)
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_wall_updated(wall)

        for stair in self._drag_selected_stairs:
            stair.position_x += delta_x
            stair.position_y += delta_y
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_stair_updated(stair)

        for slope in self._drag_selected_roof_slopes:
            slope.start_line_start = GeoPoint(
                slope.start_line_start.x + delta_x,
                slope.start_line_start.y + delta_y,
            )
            slope.start_line_end = GeoPoint(
                slope.start_line_end.x + delta_x,
                slope.start_line_end.y + delta_y,
            )
            slope.end_line_start = GeoPoint(
                slope.end_line_start.x + delta_x,
                slope.end_line_start.y + delta_y,
            )
            slope.end_line_end = GeoPoint(
                slope.end_line_end.x + delta_x,
                slope.end_line_end.y + delta_y,
            )
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_roof_slope_updated(slope)

        self._drag_last_world = snapped_current

    def _update_hosted_drag(self, view_pos: QPoint) -> None:
        """Move selected hosted objects by projecting cursor onto their host walls."""
        scene = self.scene()
        if (
            not isinstance(scene, DrawingScene)
            or scene.active_floor is None
            or self._drag_start_world is None
        ):
            return

        current_qt = self.mapToScene(view_pos)
        current_world = self._snap_point(Point(current_qt.x(), current_qt.y()))

        changed = False
        for window in self._drag_selected_windows:
            wall = self._wall_for_id(scene.active_floor.walls, window.wall_id)
            start_position = self._drag_window_start_positions.get(window.id)
            if wall is None or start_position is None:
                continue
            start_cursor_position = self._project_mm_on_wall(self._drag_start_world, wall)
            current_cursor_position = self._project_mm_on_wall(current_world, wall)
            delta = current_cursor_position - start_cursor_position
            target_position = self._clamp_hosted_position(
                wall,
                window.width,
                start_position + delta,
            )
            if abs(target_position - window.position) >= 0.1:
                window.position = target_position
                changed = True
                if self._wall_callbacks is not None:
                    self._wall_callbacks.on_window_updated(window)

        for door in self._drag_selected_doors:
            wall = self._wall_for_id(scene.active_floor.walls, door.wall_id)
            start_position = self._drag_door_start_positions.get(door.id)
            if wall is None or start_position is None:
                continue
            start_cursor_position = self._project_mm_on_wall(self._drag_start_world, wall)
            current_cursor_position = self._project_mm_on_wall(current_world, wall)
            delta = current_cursor_position - start_cursor_position
            target_position = self._clamp_hosted_position(wall, door.width, start_position + delta)
            if abs(target_position - door.position) >= 0.1:
                door.position = target_position
                changed = True
                if self._wall_callbacks is not None:
                    self._wall_callbacks.on_door_updated(door)

        for opening in self._drag_selected_openings:
            wall = self._wall_for_id(scene.active_floor.walls, opening.wall_id)
            start_position = self._drag_opening_start_positions.get(opening.id)
            if wall is None or start_position is None:
                continue
            start_cursor_position = self._project_mm_on_wall(self._drag_start_world, wall)
            current_cursor_position = self._project_mm_on_wall(current_world, wall)
            delta = current_cursor_position - start_cursor_position
            target_position = self._clamp_hosted_position(
                wall,
                opening.width,
                start_position + delta,
            )
            if abs(target_position - opening.position) >= 0.1:
                opening.position = target_position
                changed = True
                if self._wall_callbacks is not None:
                    self._wall_callbacks.on_opening_updated(opening)

        if changed:
            self._drag_last_world = current_world

    def _update_dimension_drag(self, view_pos: QPoint) -> None:
        """Move selected dimensions along each line normal, preserving helper lines."""
        if not self._drag_selected_dimensions:
            return

        current_qt = self.mapToScene(view_pos)
        current_world = self._snap_point(Point(current_qt.x(), current_qt.y()))
        reference = self._drag_selected_dimensions[0]
        reference_start_offset = self._drag_dimension_start_offsets.get(reference.id, 0.0)
        current_reference_offset = self._signed_offset_for_point(reference, current_world)
        delta_offset = current_reference_offset - reference_start_offset

        from geometry.point import Point as GeoPoint

        for dimension in self._drag_selected_dimensions:
            base_offset = self._drag_dimension_start_offsets.get(dimension.id, 0.0)
            target_offset = base_offset + delta_offset
            nx, ny = self._dimension_normal(dimension)
            dimension.display_start = GeoPoint(
                dimension.start.x + nx * target_offset,
                dimension.start.y + ny * target_offset,
            )
            dimension.display_end = GeoPoint(
                dimension.end.x + nx * target_offset,
                dimension.end.y + ny * target_offset,
            )
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_dimension_updated(dimension)

        self._drag_last_world = current_world

    def _update_rotate_drag(self, view_pos: QPoint) -> None:
        """Rotate selected walls, stairs, and roof slopes around their own centers."""
        if self._drag_rotation_origin is None:
            return

        current_qt = self.mapToScene(view_pos)
        current_world = Point(current_qt.x(), current_qt.y())
        current_angle = math.atan2(
            current_world.y - self._drag_rotation_origin.y,
            current_world.x - self._drag_rotation_origin.x,
        )
        delta_degrees = round(
            math.degrees(current_angle - self._drag_rotation_start_angle) / 5.0
        ) * 5.0
        incremental = delta_degrees - self._drag_rotation_applied_degrees
        if abs(incremental) < 0.001:
            return

        self._apply_rotation_delta(incremental)
        self._drag_rotation_applied_degrees = delta_degrees

    def _finish_rotate_drag(self) -> None:
        """Finalize a rotation drag by reverting the preview and pushing an undoable command."""
        if self._command_sink is None:
            self._reset_drag_move_state()
            return

        applied = self._drag_rotation_applied_degrees
        if abs(applied) < 0.001:
            self._reset_drag_move_state()
            return

        self._apply_rotation_delta(-applied)
        command = RotateSelectionCommand(
            walls=self._drag_selected_walls,
            stairs=self._drag_selected_stairs,
            roof_slopes=self._drag_selected_roof_slopes,
            delta_degrees=applied,
            on_wall_update=self._wall_callbacks.on_wall_updated if self._wall_callbacks else None,
            on_stair_update=(self._wall_callbacks.on_stair_updated if self._wall_callbacks else None),
            on_roof_slope_update=(
                self._wall_callbacks.on_roof_slope_updated if self._wall_callbacks else None
            ),
        )
        self._command_sink.push(command)
        self._reset_drag_move_state()

    def _apply_rotation_delta(self, delta_degrees: float) -> None:
        """Apply a live rotation delta to the current rotate selection."""
        angle = math.radians(delta_degrees)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        def rotate(point: Point, center: Point) -> Point:
            offset_x = point.x - center.x
            offset_y = point.y - center.y
            return Point(
                center.x + offset_x * cos_angle - offset_y * sin_angle,
                center.y + offset_x * sin_angle + offset_y * cos_angle,
            )

        for wall in self._drag_selected_walls:
            center = wall.center
            wall.start = rotate(wall.start, center)
            wall.end = rotate(wall.end, center)
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_wall_updated(wall)

        for stair in self._drag_selected_stairs:
            center = Point(stair.position_x + stair.width / 2.0, stair.position_y + stair.depth / 2.0)
            stair.orientation_degrees = (stair.orientation_degrees + delta_degrees) % 360.0
            stair.position_x = center.x - stair.width / 2.0
            stair.position_y = center.y - stair.depth / 2.0
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_stair_updated(stair)

        for slope in self._drag_selected_roof_slopes:
            center = self._roof_slope_center(slope)
            slope.start_line_start = rotate(slope.start_line_start, center)
            slope.start_line_end = rotate(slope.start_line_end, center)
            slope.end_line_start = rotate(slope.end_line_start, center)
            slope.end_line_end = rotate(slope.end_line_end, center)
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_roof_slope_updated(slope)

    def _finish_drag_move(self, view_pos: QPoint) -> None:
        """Finish drag move and push undoable move command."""
        scene = self.scene()
        if (
            not isinstance(scene, DrawingScene)
            or self._command_sink is None
            or self._drag_start_world is None
        ):
            self._reset_drag_move_state()
            return

        if self._drag_mode_kind == "rotate":
            self._finish_rotate_drag()
            return
        if self._drag_mode_kind == "hosted":
            self._finish_hosted_drag(view_pos)
            return
        if self._drag_mode_kind == "dimension":
            self._finish_dimension_drag(view_pos)
            return
        if not (
            self._drag_selected_walls
            or self._drag_selected_stairs
            or self._drag_selected_roof_slopes
        ):
            self._reset_drag_move_state()
            return

        end_world_qt = self.mapToScene(view_pos)
        end_world = Point(end_world_qt.x(), end_world_qt.y())
        snapped_end = self._snap_point(end_world)

        if self._drag_last_world is not None:
            # Revert live preview movement before pushing undoable command.
            revert_x = self._drag_start_world.x - self._drag_last_world.x
            revert_y = self._drag_start_world.y - self._drag_last_world.y
            from geometry.point import Point as GeoPoint

            for wall in self._drag_selected_walls:
                wall.start = GeoPoint(wall.start.x + revert_x, wall.start.y + revert_y)
                wall.end = GeoPoint(wall.end.x + revert_x, wall.end.y + revert_y)
                if self._wall_callbacks is not None:
                    self._wall_callbacks.on_wall_updated(wall)

            for stair in self._drag_selected_stairs:
                stair.position_x += revert_x
                stair.position_y += revert_y
                if self._wall_callbacks is not None:
                    self._wall_callbacks.on_stair_updated(stair)

            for slope in self._drag_selected_roof_slopes:
                slope.start_line_start = GeoPoint(
                    slope.start_line_start.x + revert_x,
                    slope.start_line_start.y + revert_y,
                )
                slope.start_line_end = GeoPoint(
                    slope.start_line_end.x + revert_x,
                    slope.start_line_end.y + revert_y,
                )
                slope.end_line_start = GeoPoint(
                    slope.end_line_start.x + revert_x,
                    slope.end_line_start.y + revert_y,
                )
                slope.end_line_end = GeoPoint(
                    slope.end_line_end.x + revert_x,
                    slope.end_line_end.y + revert_y,
                )
                if self._wall_callbacks is not None:
                    self._wall_callbacks.on_roof_slope_updated(slope)

        delta_x = snapped_end.x - self._drag_start_world.x
        delta_y = snapped_end.y - self._drag_start_world.y
        if abs(delta_x) < 5.0 and abs(delta_y) < 5.0:
            self._reset_drag_move_state()
            return

        command = MoveWallsCommand(
            walls=self._drag_selected_walls,
            delta_x=delta_x,
            delta_y=delta_y,
            on_update=self._wall_callbacks.on_wall_updated if self._wall_callbacks else None,
            floor=scene.active_floor,
            stairs=self._drag_selected_stairs,
            roof_slopes=self._drag_selected_roof_slopes,
            on_stair_update=(
                self._wall_callbacks.on_stair_updated if self._wall_callbacks else None
            ),
            on_roof_slope_update=(
                self._wall_callbacks.on_roof_slope_updated if self._wall_callbacks else None
            ),
        )
        self._command_sink.push(command)
        self._reset_drag_move_state()

    def _finish_hosted_drag(self, view_pos: QPoint) -> None:
        """Finalize hosted-object drag with one undoable command."""
        scene = self.scene()
        if (
            not isinstance(scene, DrawingScene)
            or scene.active_floor is None
            or self._command_sink is None
            or self._drag_start_world is None
        ):
            self._reset_drag_move_state()
            return

        end_world_qt = self.mapToScene(view_pos)
        end_world = self._snap_point(Point(end_world_qt.x(), end_world_qt.y()))

        window_positions: dict[str, tuple[float, float]] = {}
        door_positions: dict[str, tuple[float, float]] = {}
        opening_positions: dict[str, tuple[float, float]] = {}

        for window in self._drag_selected_windows:
            wall = self._wall_for_id(scene.active_floor.walls, window.wall_id)
            start_position = self._drag_window_start_positions.get(window.id)
            if wall is None or start_position is None:
                continue
            window.position = start_position
            start_cursor_position = self._project_mm_on_wall(self._drag_start_world, wall)
            end_cursor_position = self._project_mm_on_wall(end_world, wall)
            delta = end_cursor_position - start_cursor_position
            target_position = self._clamp_hosted_position(
                wall,
                window.width,
                start_position + delta,
            )
            window_positions[window.id] = (start_position, target_position)
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_window_updated(window)

        for door in self._drag_selected_doors:
            wall = self._wall_for_id(scene.active_floor.walls, door.wall_id)
            start_position = self._drag_door_start_positions.get(door.id)
            if wall is None or start_position is None:
                continue
            door.position = start_position
            start_cursor_position = self._project_mm_on_wall(self._drag_start_world, wall)
            end_cursor_position = self._project_mm_on_wall(end_world, wall)
            delta = end_cursor_position - start_cursor_position
            target_position = self._clamp_hosted_position(wall, door.width, start_position + delta)
            door_positions[door.id] = (start_position, target_position)
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_door_updated(door)

        for opening in self._drag_selected_openings:
            wall = self._wall_for_id(scene.active_floor.walls, opening.wall_id)
            start_position = self._drag_opening_start_positions.get(opening.id)
            if wall is None or start_position is None:
                continue
            opening.position = start_position
            start_cursor_position = self._project_mm_on_wall(self._drag_start_world, wall)
            end_cursor_position = self._project_mm_on_wall(end_world, wall)
            delta = end_cursor_position - start_cursor_position
            target_position = self._clamp_hosted_position(
                wall,
                opening.width,
                start_position + delta,
            )
            opening_positions[opening.id] = (start_position, target_position)
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_opening_updated(opening)

        has_change = any(abs(after - before) >= 0.1 for before, after in window_positions.values())
        has_change = has_change or any(
            abs(after - before) >= 0.1 for before, after in door_positions.values()
        )
        has_change = has_change or any(
            abs(after - before) >= 0.1 for before, after in opening_positions.values()
        )
        if not has_change:
            self._reset_drag_move_state()
            return

        command = MoveHostedObjectsCommand(
            windows=self._drag_selected_windows,
            window_positions=window_positions,
            doors=self._drag_selected_doors,
            door_positions=door_positions,
            openings=self._drag_selected_openings,
            opening_positions=opening_positions,
            on_window_update=(
                self._wall_callbacks.on_window_updated if self._wall_callbacks else None
            ),
            on_door_update=(self._wall_callbacks.on_door_updated if self._wall_callbacks else None),
            on_opening_update=(
                self._wall_callbacks.on_opening_updated if self._wall_callbacks else None
            ),
        )
        self._command_sink.push(command)
        self._reset_drag_move_state()

    def _finish_dimension_drag(self, view_pos: QPoint) -> None:
        """Finalize dimension drag and persist as undoable display offset move."""
        if self._command_sink is None or not self._drag_selected_dimensions:
            self._reset_drag_move_state()
            return

        end_world_qt = self.mapToScene(view_pos)
        end_world = self._snap_point(Point(end_world_qt.x(), end_world_qt.y()))
        reference = self._drag_selected_dimensions[0]
        reference_start_offset = self._drag_dimension_start_offsets.get(reference.id, 0.0)
        current_reference_offset = self._signed_offset_for_point(reference, end_world)
        delta_offset = current_reference_offset - reference_start_offset

        from geometry.point import Point as GeoPoint

        positions: dict[str, tuple[Point, Point]] = {}
        for dimension in self._drag_selected_dimensions:
            base_offset = self._drag_dimension_start_offsets.get(dimension.id, 0.0)
            target_offset = base_offset + delta_offset
            nx, ny = self._dimension_normal(dimension)
            old_point = self._drag_dimension_start_points.get(dimension.id, dimension.start)
            new_point = GeoPoint(
                dimension.start.x + nx * target_offset,
                dimension.start.y + ny * target_offset,
            )
            positions[dimension.id] = (old_point, new_point)

            dimension.display_start = old_point
            dx = old_point.x - dimension.start.x
            dy = old_point.y - dimension.start.y
            dimension.display_end = GeoPoint(dimension.end.x + dx, dimension.end.y + dy)
            if self._wall_callbacks is not None:
                self._wall_callbacks.on_dimension_updated(dimension)

        has_change = any(
            abs(new_point.x - old_point.x) >= 0.1 or abs(new_point.y - old_point.y) >= 0.1
            for old_point, new_point in positions.values()
        )
        if not has_change:
            self._reset_drag_move_state()
            return

        command = MoveDimensionsCommand(
            dimensions=self._drag_selected_dimensions,
            positions=positions,
            on_update=(self._wall_callbacks.on_dimension_updated if self._wall_callbacks else None),
        )
        self._command_sink.push(command)
        self._reset_drag_move_state()

    def _reset_drag_move_state(self) -> None:
        """Clear drag move state and restore cursor for active tool."""
        self._is_drag_moving = False
        self._drag_start_world = None
        self._drag_last_world = None
        self._drag_cursor_offset = None
        self._drag_rotation_origin = None
        self._drag_rotation_start_angle = 0.0
        self._drag_rotation_applied_degrees = 0.0
        self._drag_selected_walls = []
        self._drag_selected_stairs = []
        self._drag_selected_roof_slopes = []
        self._drag_selected_windows = []
        self._drag_selected_doors = []
        self._drag_selected_openings = []
        self._drag_selected_dimensions = []
        self._drag_window_start_positions = {}
        self._drag_door_start_positions = {}
        self._drag_opening_start_positions = {}
        self._drag_dimension_start_offsets = {}
        self._drag_dimension_start_points = {}
        self._drag_mode_kind = None
        if self._tool_mode == ToolMode.SELECT:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)
        self._sync_scene_overlay_state()

    def _wall_for_id(self, walls: list[Wall], wall_id: str) -> Wall | None:
        """Return wall model by identifier."""
        return next((wall for wall in walls if wall.id == wall_id), None)

    def _nearest_rotation_center(self, click_world: Point) -> Point | None:
        """Return the nearest center of the currently selected rotatable objects."""
        centers: list[Point] = [wall.center for wall in self._drag_selected_walls]
        centers.extend(
            Point(stair.position_x + stair.width / 2.0, stair.position_y + stair.depth / 2.0)
            for stair in self._drag_selected_stairs
        )
        centers.extend(self._roof_slope_center(slope) for slope in self._drag_selected_roof_slopes)
        if not centers:
            return None
        return min(
            centers,
            key=lambda point: (point.x - click_world.x) ** 2 + (point.y - click_world.y) ** 2,
        )

    def _roof_slope_center(self, slope: RoofSlope) -> Point:
        """Return the geometric center of a roof slope boundary quad."""
        points = [
            slope.start_line_start,
            slope.start_line_end,
            slope.end_line_start,
            slope.end_line_end,
        ]
        return Point(
            sum(point.x for point in points) / 4.0,
            sum(point.y for point in points) / 4.0,
        )

    def _toggle_door_on_double_click(self, view_pos: QPoint) -> bool:
        """Toggle the swing direction of the door under the cursor."""
        scene = self.scene()
        if (
            not isinstance(scene, DrawingScene)
            or scene.active_floor is None
            or self._command_sink is None
        ):
            return False

        clicked_item = self.itemAt(view_pos)
        if clicked_item is None:
            return False

        door_id: str | None = None
        current: QGraphicsItem | None = clicked_item
        while current is not None:
            candidate = getattr(current, "door_id", None)
            if isinstance(candidate, str):
                door_id = candidate
                break
            current = current.parentItem()

        if door_id is None:
            return False

        door = next((entry for entry in scene.active_floor.doors if entry.id == door_id), None)
        if door is None:
            return False

        next_direction = {
            "left_out": "right_out",
            "right_out": "left_in",
            "left_in": "right_in",
            "right_in": "left_out",
        }.get(door.swing_direction, "left_in")

        self._command_sink.push(
            ToggleDoorSwingCommand(
                door=door,
                new_swing_direction=next_direction,
                on_update=self._wall_callbacks.on_door_updated if self._wall_callbacks else None,
            )
        )
        return True

    def _project_mm_on_wall(self, point: Point, wall: Wall) -> float:
        """Project point to wall axis and return distance in millimeters from wall start."""
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        length_sq = dx * dx + dy * dy
        if length_sq <= 1e-6:
            return 0.0
        t = ((point.x - wall.start.x) * dx + (point.y - wall.start.y) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        projected = t * wall.length
        step = max(1.0, self._snap_distance_mm)
        return round(projected / step) * step

    def _clamp_hosted_position(self, wall: Wall, width: float, position: float) -> float:
        """Clamp hosted element center position so width remains inside wall segment."""
        half = max(1.0, width / 2.0)
        if wall.length <= half * 2.0:
            return wall.length / 2.0
        return max(half, min(wall.length - half, position))

    def _dimension_normal(self, dimension: Dimension) -> tuple[float, float]:
        """Return unit normal vector for a dimension base line."""
        dx = dimension.end.x - dimension.start.x
        dy = dimension.end.y - dimension.start.y
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return (0.0, -1.0)
        return (-dy / length, dx / length)

    def _dimension_signed_offset(self, dimension: Dimension) -> float:
        """Return signed perpendicular offset between base and display line."""
        display_start = dimension.display_start or dimension.start
        nx, ny = self._dimension_normal(dimension)
        return (
            (display_start.x - dimension.start.x) * nx
            + (display_start.y - dimension.start.y) * ny
        )

    def _signed_offset_for_point(self, dimension: Dimension, point: Point) -> float:
        """Return signed perpendicular offset of an arbitrary point to dimension base line."""
        nx, ny = self._dimension_normal(dimension)
        return (point.x - dimension.start.x) * nx + (point.y - dimension.start.y) * ny

    def _snap_to_angle(self, start: Point, end: Point) -> Point:
        """Snap the vector from start to end to the configured angle increment."""
        print(f"Snapping from {start} to {end} with increment {self._angle_snap_increment}")
        dx = end.x - start.x
        dy = end.y - start.y
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return end

        increment_rad = math.radians(self._angle_snap_increment)
        angle = math.atan2(dy, dx)
        print(f"Original angle: {math.degrees(angle)} degrees")
        snapped_angle = round(angle / increment_rad) * increment_rad
        print(f"Snapped angle: {math.degrees(snapped_angle)} degrees")
        return Point(
            x=start.x + math.cos(snapped_angle) * length,
            y=start.y + math.sin(snapped_angle) * length,
        )

    def _quantize_point(self, point: Point) -> Point:
        """Quantize a world point to the current zoom-aware grid."""
        return self._snap_service.quantize_point(self, point)

    def _nearest_selection_corner(self, click_world: Point) -> Point:
        """Return nearest corner from current selection for stable move anchoring."""
        return self._snap_service.nearest_selection_corner(self, click_world)

    def _selection_corner_points(self) -> list[Point]:
        """Collect snap-relevant corners from selected movable objects."""
        return self._snap_service.selection_corner_points(self)

    def _wall_corner_points(self, walls: list[Wall]) -> list[Point]:
        """Return outer-corner points of selected walls."""
        return self._snap_service.wall_corner_points(walls)

    def _stair_corner_points(self, stairs: list[Stair]) -> list[Point]:
        """Return axis-aligned rectangle corners of selected stairs."""
        return self._snap_service.stair_corner_points(stairs)

    def _roof_slope_corner_points(self, slopes: list[RoofSlope]) -> list[Point]:
        """Return boundary corners from selected roof slopes."""
        return self._snap_service.roof_slope_corner_points(slopes)
