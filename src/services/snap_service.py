"""Snap business service for drawing interactions."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from geometry.point import Point
from geometry.snap_engine import SnapEngine
from models.roof_slope import RoofSlope
from models.stair import Stair
from models.wall import Wall, WallType
from views.scene.drawing_scene import DrawingScene


@dataclass(slots=True)
class SnapService:
    """Owns snap calculations and anchor selection for the drawing view."""

    _snap_engine: SnapEngine = field(default_factory=SnapEngine)
    _snap_enabled: bool = True
    _snap_distance_mm: float = 300.0
    _angle_snap_increment: float = 15.0

    def set_snap_enabled(self, enabled: bool) -> None:
        """Enable or disable snapping."""
        self._snap_enabled = enabled

    def set_snap_distance(self, distance_mm: float) -> None:
        """Set the base snap distance used for zoom-aware snapping."""
        self._snap_distance_mm = max(0.0, distance_mm)

    def set_angle_snap_increment(self, increment_degrees: float) -> None:
        """Set directional angle snap increment in degrees."""
        self._angle_snap_increment = max(1.0, min(90.0, increment_degrees))

    def snap_point(self, view: object, point: Point) -> Point:
        """Snap world point to wall-aware targets when enabled."""
        scene = self._scene_from_view(view)
        if not isinstance(scene, DrawingScene) or not self._snap_enabled:
            self._publish_debug_snap_point(view, None)
            return point

        snap_distance = self._snap_engine.dynamic_snap_distance(
            base_distance=self._snap_distance_mm,
            zoom_scale=self._view_zoom_scale(view),
        )

        walls = self.walls_for_snap(scene)
        wall_id_to_skip = self._find_preview_start_wall_id(view)
        if wall_id_to_skip is not None:
            walls = [wall for wall in walls if wall.id != wall_id_to_skip]

        tool_mode = getattr(view, "_tool_mode", None)
        is_drag_moving = bool(getattr(view, "_is_drag_moving", False))
        if tool_mode == "WALL":
            snapped = self.snap_for_wall_creation(view, point, walls, snap_distance)
        elif tool_mode == "SELECT" and is_drag_moving:
            snapped = self.snap_for_wall_movement(view, point, walls, snap_distance)
        else:
            snapped = self.snap_for_wall_hosted(view, point, walls, snap_distance)

        self._publish_debug_snap_point(view, snapped)
        return snapped

    def snap_dimension_endpoint_point(self, view: object, point: Point) -> Point:
        """Snap dimension start/end points to wall and hosted-object corners and edges."""
        scene = self._scene_from_view(view)
        if not isinstance(scene, DrawingScene) or not self._snap_enabled:
            self._publish_debug_snap_point(view, None)
            return point
        print(f"Base snap distance: {self._snap_distance_mm:.2f} mm")
        snap_distance = self._snap_engine.dynamic_snap_distance(
            base_distance=self._snap_distance_mm,
            zoom_scale=self._view_zoom_scale(view),
        )
        print(f"Snapping dimension endpoint with snap distance {snap_distance:.2f}")

        corners, attachments, edge_segments = self._dimension_snap_targets(view, scene)
        snapped_corner = self._nearest_point(point, corners, snap_distance)
        if snapped_corner is not None:
            print(f"Snapped to corner at ({snapped_corner.x:.2f}, {snapped_corner.y:.2f})")
            self._publish_debug_snap_point(view, snapped_corner)
            return snapped_corner
        
        snapped_attachment = self._nearest_point(point, attachments, snap_distance)
        if snapped_attachment is not None:
            print(f"Snapped to attachment at ({snapped_attachment.x:.2f}, {snapped_attachment.y:.2f})")
            self._publish_debug_snap_point(view, snapped_attachment)
            return snapped_attachment

        snapped_edge = self._nearest_segment_projection(point, edge_segments, snap_distance)
        if snapped_edge is not None:
            print(f"Snapped to edge at ({snapped_edge.x:.2f}, {snapped_edge.y:.2f})")
            self._publish_debug_snap_point(view, snapped_edge)
            return snapped_edge

        grid_point = self.snap_grid(view, point)
        print(f"Snapped to grid at ({grid_point.x:.2f}, {grid_point.y:.2f})")
        self._publish_debug_snap_point(view, grid_point)
        return grid_point

    def snap_for_wall_creation(
        self,
        view: object,
        point: Point,
        walls: list[Wall],
        snap_distance: float,
    ) -> Point:
        """Snap new wall drawing to wall endpoints, attachments, side geometry, and angle."""
        endpoint_targets = [endpoint for wall in walls for endpoint in (wall.start, wall.end)]
        attachment_targets = [
            attachment
            for wall in walls
            for attachment in self.wall_attachment_points(wall, self.current_wall_thickness(view))
        ]
        midpoint_targets = [midpoint for wall in walls for midpoint in self.wall_side_midpoints(wall)]
        edge_segments = [segment for wall in walls for segment in self.wall_side_segments(wall)]
        centerline_segments = [(wall.start, wall.end) for wall in walls]

        snapped = self._snap_with_priority(
            point=point,
            snap_distance=snap_distance,
            endpoint_targets=endpoint_targets,
            attachment_targets=attachment_targets,
            midpoint_targets=midpoint_targets,
            edge_segments=edge_segments,
            centerline_segments=centerline_segments,
        )
        if snapped is not None:
            return snapped

        wall_start_point = getattr(view, "_wall_start_point", None)
        if wall_start_point is None:
            return point

        return self.snap_to_angle(view, wall_start_point, point)

    def snap_for_wall_movement(
        self,
        view: object,
        point: Point,
        walls: list[Wall],
        snap_distance: float,
    ) -> Point:
        """Snap moved walls by aligning selection geometry against scene targets.

        For each candidate point of the selected objects (corners / midpoints /
        attachment points for walls; corners for stairs and roof slopes) the raw
        displacement vector is applied and the result is tested against snap
        targets on the non-selected scene walls.  The correction that produces
        the tightest snap is chosen and the whole selection is moved by that
        uniform delta.

        Priority: outline corners > centerline endpoints > attachment points
                  > side midpoints > edge projections > grid.
        """
        # Compute cursor-corrected desired anchor position so the anchor
        # (a selection corner) moves with the mouse, not the raw cursor.
        cursor_offset = getattr(view, "_drag_cursor_offset", None)
        if cursor_offset is not None:
            desired_anchor = Point(point.x - cursor_offset.x, point.y - cursor_offset.y)
        else:
            desired_anchor = point

        drag_last: Point = getattr(view, "_drag_last_world", None) or desired_anchor

        # Incremental raw movement since the last snapped frame.
        raw_dx = desired_anchor.x - drag_last.x
        raw_dy = desired_anchor.y - drag_last.y

        # Collect candidate points from the *current* (mid-drag) positions of
        # the selected objects.
        selected_walls: list[Wall] = getattr(view, "_drag_selected_walls", [])
        selected_stairs = getattr(view, "_drag_selected_stairs", [])
        selected_slopes = getattr(view, "_drag_selected_roof_slopes", [])
        selected_ids = {w.id for w in selected_walls}

        candidates: list[Point] = []
        for w in selected_walls:
            candidates.extend(self.wall_outline_points(w))           # Eckpunkte
            candidates.extend(self.wall_side_midpoints(w))           # Kantenmittelpunkte
            candidates.extend(self.wall_attachment_points(w, w.thickness))  # Anknüpfpunkte
        candidates.extend(self._stair_corner_points(None, selected_stairs))
        candidates.extend(self._roof_slope_corner_points(None, selected_slopes))

        # Snap target pools built only from *non-selected* walls.
        target_walls = [w for w in walls if w.id not in selected_ids]

        if not candidates or not target_walls:
            # Nothing to snap against – fall back to anchor-only grid snap.
            return self.snap_grid(view, desired_anchor)

        corner_targets   = [p for w in target_walls for p in self.wall_outline_points(w)]
        endpoint_targets = [p for w in target_walls for p in (w.start, w.end)]
        attach_targets   = [p for w in target_walls for p in self.wall_attachment_points(w, w.thickness)]
        midpoint_targets = [p for w in target_walls for p in self.wall_side_midpoints(w)]
        edge_segments    = [s for w in target_walls for s in self.wall_side_segments(w)]

        def _best_point_snap(
            target_pool: list[Point],
        ) -> tuple[float, Point] | None:
            """Return (distance, correction_vector) for the tightest candidate→target snap."""
            best_dist = snap_distance
            best_corr: Point | None = None
            for c in candidates:
                cx = c.x + raw_dx
                cy = c.y + raw_dy
                for t in target_pool:
                    d = math.hypot(t.x - cx, t.y - cy)
                    if d < best_dist:
                        best_dist = d
                        best_corr = Point(t.x - c.x, t.y - c.y)
            return (best_dist, best_corr) if best_corr is not None else None

        def _best_segment_snap(
            segments: list[tuple[Point, Point]],
        ) -> tuple[float, Point] | None:
            """Return (distance, correction_vector) for the tightest candidate→edge snap."""
            best_dist = snap_distance
            best_corr: Point | None = None
            for c in candidates:
                cx = c.x + raw_dx
                cy = c.y + raw_dy
                for seg_start, seg_end in segments:
                    sdx = seg_end.x - seg_start.x
                    sdy = seg_end.y - seg_start.y
                    length_sq = sdx * sdx + sdy * sdy
                    if length_sq <= 1e-6:
                        continue
                    t_val = max(0.0, min(1.0, ((cx - seg_start.x) * sdx + (cy - seg_start.y) * sdy) / length_sq))
                    proj_x = seg_start.x + t_val * sdx
                    proj_y = seg_start.y + t_val * sdy
                    d = math.hypot(proj_x - cx, proj_y - cy)
                    if d < best_dist:
                        best_dist = d
                        best_corr = Point(proj_x - c.x, proj_y - c.y)
            return (best_dist, best_corr) if best_corr is not None else None

        # Walk priorities highest → lowest; stop at the first level that yields a snap.
        for pool in (corner_targets, endpoint_targets, attach_targets, midpoint_targets):
            hit = _best_point_snap(pool)
            if hit is not None:
                _, corr = hit
                return Point(drag_last.x + corr.x, drag_last.y + corr.y)

        edge_hit = _best_segment_snap(edge_segments)
        if edge_hit is not None:
            _, corr = edge_hit
            return Point(drag_last.x + corr.x, drag_last.y + corr.y)

        # Grid fallback: align the desired anchor to the grid.
        return self.snap_grid(view, desired_anchor)

    def snap_for_wall_hosted(
        self,
        view: object,
        point: Point,
        walls: list[Wall],
        snap_distance: float,
    ) -> Point:
        """Snap hosted-object placement only to walls and grid."""
        endpoint_targets = [endpoint for wall in walls for endpoint in (wall.start, wall.end)]
        midpoint_targets = [midpoint for wall in walls for midpoint in self.wall_side_midpoints(wall)]
        edge_segments = [segment for wall in walls for segment in self.wall_side_segments(wall)]

        snapped = self._snap_with_priority(
            point=point,
            snap_distance=snap_distance,
            endpoint_targets=endpoint_targets,
            attachment_targets=[],
            midpoint_targets=midpoint_targets,
            edge_segments=edge_segments,
            centerline_segments=[],
        )
        if snapped is not None:
            return snapped

        return self.snap_grid(view, point)

    def snap_with_priority(
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
        return self._snap_with_priority(
            point=point,
            snap_distance=snap_distance,
            endpoint_targets=endpoint_targets,
            attachment_targets=attachment_targets,
            midpoint_targets=midpoint_targets,
            edge_segments=edge_segments,
            centerline_segments=centerline_segments,
        )

    def walls_for_snap(self, scene: DrawingScene) -> list[Wall]:
        """Return walls from the active floor for snapping."""
        floor = scene.active_floor
        if floor is None:
            return []

        return floor.walls

    def wall_outline_points(self, wall: Wall) -> list[Point]:
        """Return the rectangle corners of a wall thickness footprint."""
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

    def wall_side_midpoints(self, wall: Wall) -> list[Point]:
        """Return midpoints of the wall's outer contour edges."""
        points = self.wall_outline_points(wall)
        if len(points) < 4:
            return []

        return [
            Point(
                (points[index].x + points[(index + 1) % 4].x) / 2.0,
                (points[index].y + points[(index + 1) % 4].y) / 2.0,
            )
            for index in range(4)
        ]

    def wall_side_segments(self, wall: Wall) -> list[tuple[Point, Point]]:
        """Return the outer contour segments of a wall."""
        points = self.wall_outline_points(wall)
        if len(points) < 4:
            return []

        return [(points[index], points[(index + 1) % 4]) for index in range(4)]

    def wall_attachment_points(self, wall: Wall, attachment_width: float) -> list[Point]:
        """Return dynamic anchor points near wall corners."""
        if attachment_width <= 0.0:
            return []

        half_attachment = attachment_width / 2.0
        attachments: list[Point] = []
        for start, end in self.wall_side_segments(wall):
            edge_dx = end.x - start.x
            edge_dy = end.y - start.y
            edge_length = math.hypot(edge_dx, edge_dy)
            if edge_length <= attachment_width + 1e-6:
                continue

            ux = edge_dx / edge_length
            uy = edge_dy / edge_length
            attachments.append(Point(start.x + ux * half_attachment, start.y + uy * half_attachment))
            attachments.append(Point(end.x - ux * half_attachment, end.y - uy * half_attachment))

        return attachments

    def current_wall_thickness(self, view: object) -> float:
        """Return the default thickness for the currently active wall tool."""
        current_wall_type = getattr(view, "_current_wall_type", None)
        if current_wall_type == WallType.INTERIOR:
            return getattr(view, "_default_interior_wall_thickness", 110.0)
        return getattr(view, "_default_exterior_wall_thickness", 300.0)

    def nearest_point(self, source: Point, targets: list[Point], radius: float) -> Point | None:
        """Return nearest target point within a radius."""
        return self._nearest_point(source, targets, radius)

    def nearest_segment_projection(
        self,
        source: Point,
        segments: list[tuple[Point, Point]],
        radius: float,
    ) -> Point | None:
        """Return the nearest projection onto a segment within a radius."""
        return self._nearest_segment_projection(source, segments, radius)

    def snap_grid(self, view: object, point: Point) -> Point:
        """Snap a point to a zoom-aware grid."""
        scene = self._scene_from_view(view)
        if not isinstance(scene, DrawingScene):
            return point

        zoom_scale = max(0.01, self._view_zoom_scale(view))
        grid_step, _ = scene.grid_steps_for_zoom(zoom_scale)
        snapped_x = round(point.x / grid_step) * grid_step
        snapped_y = round(point.y / grid_step) * grid_step
        return Point(snapped_x, snapped_y)

    def quantize_point(self, view: object, point: Point) -> Point:
        """Quantize a world point to the current zoom-aware grid."""
        return self.snap_grid(view, point)

    def nearest_selection_corner(self, view: object, click_world: Point) -> Point:
        """Return nearest corner from current selection for stable move anchoring."""
        corners = self._selection_corner_points(view)
        if not corners:
            return click_world

        return min(
            corners,
            key=lambda point: (point.x - click_world.x) ** 2 + (point.y - click_world.y) ** 2,
        )

    def selection_corner_points(self, view: object) -> list[Point]:
        """Collect snap-relevant corners from selected movable objects."""
        corners: list[Point] = []
        corners.extend(self._wall_corner_points(view, getattr(view, "_drag_selected_walls", [])))
        corners.extend(self._stair_corner_points(view, getattr(view, "_drag_selected_stairs", [])))
        corners.extend(self._roof_slope_corner_points(view, getattr(view, "_drag_selected_roof_slopes", [])))
        return corners

    def wall_corner_points(self, walls: list[Wall]) -> list[Point]:
        """Return outer-corner points of selected walls."""
        return self._wall_corner_points(None, walls)

    def stair_corner_points(self, stairs: list[Stair]) -> list[Point]:
        """Return axis-aligned rectangle corners of selected stairs."""
        return self._stair_corner_points(None, stairs)

    def roof_slope_corner_points(self, slopes: list[RoofSlope]) -> list[Point]:
        """Return boundary corners from selected roof slopes."""
        return self._roof_slope_corner_points(None, slopes)

    def snap_to_angle(self, view: object, start: Point, end: Point) -> Point:
        """Snap the vector from start to end to the configured angle increment."""
        dx = end.x - start.x
        dy = end.y - start.y
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return end

        increment_rad = math.radians(self._angle_snap_increment)
        angle = math.atan2(dy, dx)
        snapped_angle = round(angle / increment_rad) * increment_rad
        return Point(
            x=start.x + math.cos(snapped_angle) * length,
            y=start.y + math.sin(snapped_angle) * length,
        )

    def _publish_debug_snap_point(self, view: object, point: Point | None) -> None:
        """Publish the current debug snap point to scene and status listeners."""
        publish = getattr(view, "_publish_debug_snap_point", None)
        if callable(publish):
            publish(point)

    def _scene_from_view(self, view: object) -> DrawingScene | None:
        scene_getter = getattr(view, "scene", None)
        if callable(scene_getter):
            return scene_getter()
        return None

    def _view_zoom_scale(self, view: object) -> float:
        transform_getter = getattr(view, "transform", None)
        if callable(transform_getter):
            return transform_getter().m11()
        return 1.0

    def _find_preview_start_wall_id(self, view: object) -> str | None:
        finder = getattr(view, "_find_preview_start_wall_id", None)
        if callable(finder):
            return finder()
        return None

    def _dimension_snap_targets(self, view: object, scene: DrawingScene) -> tuple[list[Point], list[tuple[Point, Point]]]:
        """Collect corners and edges used when snapping dimension endpoints."""
        floor = scene.active_floor
        if floor is None:
            return ([], [])

        corners: list[Point] = []
        attachments: list[Point] = []
        edges: list[tuple[Point, Point]] = []

        for wall in floor.walls:
            wall_corners = self.wall_outline_points(wall)
            corners.extend(wall_corners)
            wall_attachments = self.wall_attachment_points(wall, self.current_wall_thickness(view))
            attachments.extend(wall_attachments)
            edges.extend(self.wall_side_segments(wall))

        hosted_specs = [
            (window.wall_id, window.position, window.width) for window in floor.windows
        ]
        hosted_specs.extend((door.wall_id, door.position, door.width) for door in floor.doors)
        hosted_specs.extend(
            (opening.wall_id, opening.position, opening.width) for opening in floor.openings
        )
        for wall_id, position, width in hosted_specs:
            wall = next((entry for entry in floor.walls if entry.id == wall_id), None)
            if wall is None:
                continue
            points = self._hosted_object_outline_points(wall, position, width)
            corners.extend(points)
            if len(points) == 4:
                edges.extend([(points[index], points[(index + 1) % 4]) for index in range(4)])

        return corners, attachments, edges

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
        endpoint = self._nearest_point(point, endpoint_targets, snap_distance)
        if endpoint is not None:
            return endpoint

        attachment = self._nearest_point(point, attachment_targets, snap_distance)
        if attachment is not None:
            return attachment

        midpoint = self._nearest_point(point, midpoint_targets, snap_distance)
        if midpoint is not None:
            return midpoint

        edge = self._nearest_segment_projection(point, edge_segments, snap_distance)
        if edge is not None:
            return edge

        centerline = self._nearest_segment_projection(point, centerline_segments, snap_distance)
        if centerline is not None:
            return centerline

        return None

    def _nearest_point(self, source: Point, targets: list[Point], radius: float) -> Point | None:
        """Return nearest target point within a radius."""
        best_point: Point | None = None
        best_distance = radius

        for target in targets:
            candidate_distance = math.hypot(source.x - target.x, source.y - target.y)
            if candidate_distance <= best_distance:
                best_distance = candidate_distance
                best_point = target

        return best_point

    def _nearest_segment_projection(
        self,
        source: Point,
        segments: list[tuple[Point, Point]],
        radius: float,
    ) -> Point | None:
        """Return the nearest projection onto a segment within a radius."""
        best_point: Point | None = None
        best_distance = radius

        for start, end in segments:
            dx = end.x - start.x
            dy = end.y - start.y
            length_sq = dx * dx + dy * dy
            if length_sq <= 1e-6:
                continue

            offset_x = source.x - start.x
            offset_y = source.y - start.y
            t = max(0.0, min(1.0, (offset_x * dx + offset_y * dy) / length_sq))
            projected = Point(start.x + t * dx, start.y + t * dy)
            candidate_distance = math.hypot(source.x - projected.x, source.y - projected.y)
            if candidate_distance <= best_distance:
                best_distance = candidate_distance
                best_point = projected

        return best_point

    def _wall_corner_points(self, view: object | None, walls: list[Wall]) -> list[Point]:
        """Return outer-corner points of selected walls."""
        result: list[Point] = []
        for wall in walls:
            result.extend(self.wall_outline_points(wall))
        return result

    def _stair_corner_points(self, view: object | None, stairs: list[Stair]) -> list[Point]:
        """Return axis-aligned rectangle corners of selected stairs."""
        result: list[Point] = []
        for stair in stairs:
            x = stair.position_x
            y = stair.position_y
            result.extend(
                [
                    Point(x, y),
                    Point(x + stair.width, y),
                    Point(x + stair.width, y + stair.depth),
                    Point(x, y + stair.depth),
                ]
            )
        return result

    def _roof_slope_corner_points(self, view: object | None, slopes: list[RoofSlope]) -> list[Point]:
        """Return boundary corners from selected roof slopes."""
        result: list[Point] = []
        for slope in slopes:
            result.extend(
                [
                    slope.start_line_start,
                    slope.start_line_end,
                    slope.end_line_end,
                    slope.end_line_start,
                ]
            )
        return result

    def _selection_corner_points(self, view: object) -> list[Point]:
        """Collect snap-relevant corners from selected movable objects."""
        corners: list[Point] = []
        corners.extend(self._wall_corner_points(view, getattr(view, "_drag_selected_walls", [])))
        corners.extend(self._stair_corner_points(view, getattr(view, "_drag_selected_stairs", [])))
        corners.extend(self._roof_slope_corner_points(view, getattr(view, "_drag_selected_roof_slopes", [])))
        return corners