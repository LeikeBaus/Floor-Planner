"""Pure snap geometry logic independent from UI classes."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from geometry.point import Point
from geometry.snap_engine import SnapEngine
from models.roof_slope import RoofSlope
from models.stair import Stair
from models.wall import Wall


@dataclass(slots=True)
class SnapLogicService:
    """Pure geometry and snapping priority calculations."""

    _snap_engine: SnapEngine = field(default_factory=SnapEngine)
    _snap_enabled: bool = True
    _snap_distance_mm: float = 300.0
    _angle_snap_increment: float = 15.0

    def set_snap_enabled(self, enabled: bool) -> None:
        self._snap_enabled = enabled

    def is_snap_enabled(self) -> bool:
        return self._snap_enabled

    def set_snap_distance(self, distance_mm: float) -> None:
        self._snap_distance_mm = max(0.0, distance_mm)

    def snap_distance_mm(self) -> float:
        return self._snap_distance_mm

    def set_angle_snap_increment(self, increment_degrees: float) -> None:
        self._angle_snap_increment = max(1.0, min(90.0, increment_degrees))

    def angle_snap_increment(self) -> float:
        return self._angle_snap_increment

    def dynamic_snap_distance(self, zoom_scale: float) -> float:
        return self._snap_engine.dynamic_snap_distance(
            base_distance=self._snap_distance_mm,
            zoom_scale=zoom_scale,
        )

    def wall_outline_points(self, wall: Wall) -> list[Point]:
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
        points = self.wall_outline_points(wall)
        if len(points) < 4:
            return []
        return [(points[index], points[(index + 1) % 4]) for index in range(4)]

    def wall_attachment_points(self, wall: Wall, attachment_width: float) -> list[Point]:
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

    def nearest_point(self, source: Point, targets: list[Point], radius: float) -> Point | None:
        best_point: Point | None = None
        best_distance = radius

        for target in targets:
            candidate_distance = math.hypot(source.x - target.x, source.y - target.y)
            if candidate_distance <= best_distance:
                best_distance = candidate_distance
                best_point = target

        return best_point

    def nearest_segment_projection(
        self,
        source: Point,
        segments: list[tuple[Point, Point]],
        radius: float,
    ) -> Point | None:
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
        endpoint = self.nearest_point(point, endpoint_targets, snap_distance)
        if endpoint is not None:
            return endpoint

        attachment = self.nearest_point(point, attachment_targets, snap_distance)
        if attachment is not None:
            return attachment

        midpoint = self.nearest_point(point, midpoint_targets, snap_distance)
        if midpoint is not None:
            return midpoint

        edge = self.nearest_segment_projection(point, edge_segments, snap_distance)
        if edge is not None:
            return edge

        centerline = self.nearest_segment_projection(point, centerline_segments, snap_distance)
        if centerline is not None:
            return centerline

        return None

    def snap_grid(self, point: Point, grid_step: float) -> Point:
        if grid_step <= 1e-6:
            return point
        snapped_x = round(point.x / grid_step) * grid_step
        snapped_y = round(point.y / grid_step) * grid_step
        return Point(snapped_x, snapped_y)

    def snap_to_angle(self, start: Point, end: Point) -> Point:
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

    def wall_corner_points(self, walls: list[Wall]) -> list[Point]:
        result: list[Point] = []
        for wall in walls:
            result.extend(self.wall_outline_points(wall))
        return result

    def stair_corner_points(self, stairs: list[Stair]) -> list[Point]:
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

    def roof_slope_corner_points(self, slopes: list[RoofSlope]) -> list[Point]:
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

    def hosted_object_outline_points(self, wall: Wall, position: float, width: float) -> list[Point]:
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
