"""Central snapping engine."""

from __future__ import annotations

import math
from dataclasses import dataclass

from geometry.point import Point


# ============================================================
# Result
# ============================================================

@dataclass(slots=True, frozen=True)
class SnapResult:
    point: Point
    kind: str


# ============================================================
# Engine
# ============================================================

class SnapEngine:

    SNAP_NONE = "none"
    SNAP_POINT = "point"
    SNAP_EDGE = "edge"
    SNAP_GRID = "grid"
    SNAP_ANGLE = "angle"

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------

    def snap_create(
        self,
        cursor: Point,
        special_points: list[Point],
        edges: list[tuple[Point, Point]],
        grid_step: float,
        snap_distance: float,
        wall_start: Point | None = None,
        angle_increment: float = 45.0,
    ) -> SnapResult:
        """
        Priority:

        1. Special points
        2. Angle snap (wall creation only)
        3. Edge snap
        4. Grid
        """

        point_hit = self._nearest_point(
            cursor,
            special_points,
            snap_distance,
        )

        if point_hit is not None:
            return SnapResult(point_hit, self.SNAP_POINT)

        if wall_start is not None:
            angle_hit = self._angle_snap(
                wall_start,
                cursor,
                angle_increment,
                grid_step,
            )

            if self._distance(cursor, angle_hit) <= snap_distance:
                return SnapResult(angle_hit, self.SNAP_ANGLE)

        edge_hit = self._nearest_edge_projection(
            cursor,
            edges,
            snap_distance,
        )

        if edge_hit is not None:
            return SnapResult(edge_hit, self.SNAP_EDGE)

        return SnapResult(
            self._grid_snap(cursor, grid_step),
            self.SNAP_GRID,
        )

    def snap_move(
        self,
        moving_points: list[Point],
        move_delta: Point,
        target_points: list[Point],
        target_edges: list[tuple[Point, Point]],
        grid_step: float,
        snap_distance: float,
    ) -> SnapResult:
        """
        Priority:

        1. Point -> Point
        2. Edge -> Edge
        3. Grid
        """

        point_hit = self._best_point_alignment(
            moving_points,
            move_delta,
            target_points,
            snap_distance,
        )

        if point_hit is not None:
            return SnapResult(point_hit, self.SNAP_POINT)

        edge_hit = self._best_edge_alignment(
            moving_points,
            move_delta,
            target_edges,
            snap_distance,
        )

        if edge_hit is not None:
            return SnapResult(edge_hit, self.SNAP_EDGE)

        snapped_delta = Point(
            round(move_delta.x / grid_step) * grid_step,
            round(move_delta.y / grid_step) * grid_step,
        )

        return SnapResult(snapped_delta, self.SNAP_GRID)

    # --------------------------------------------------------
    # POINT SNAP
    # --------------------------------------------------------

    def _nearest_point(
        self,
        source: Point,
        targets: list[Point],
        radius: float,
    ) -> Point | None:

        best = None
        best_distance = radius

        for target in targets:

            distance = self._distance(source, target)

            if distance <= best_distance:
                best_distance = distance
                best = target

        return best

    # --------------------------------------------------------
    # EDGE SNAP
    # --------------------------------------------------------

    def _nearest_edge_projection(
        self,
        point: Point,
        edges: list[tuple[Point, Point]],
        radius: float,
    ) -> Point | None:

        best = None
        best_distance = radius

        for start, end in edges:

            projection = self._project_to_segment(
                point,
                start,
                end,
            )

            distance = self._distance(point, projection)

            if distance <= best_distance:
                best_distance = distance
                best = projection

        return best

    # --------------------------------------------------------
    # MOVE POINT -> POINT
    # --------------------------------------------------------

    def _best_point_alignment(
        self,
        moving_points: list[Point],
        move_delta: Point,
        targets: list[Point],
        radius: float,
    ) -> Point | None:

        best_distance = radius
        best_delta = None

        for moving in moving_points:

            moved = Point(
                moving.x + move_delta.x,
                moving.y + move_delta.y,
            )

            for target in targets:

                distance = self._distance(moved, target)

                if distance <= best_distance:

                    best_distance = distance

                    best_delta = Point(
                        target.x - moving.x,
                        target.y - moving.y,
                    )

        return best_delta

    # --------------------------------------------------------
    # MOVE EDGE -> EDGE
    # --------------------------------------------------------

    def _best_edge_alignment(
        self,
        moving_points: list[Point],
        move_delta: Point,
        target_edges: list[tuple[Point, Point]],
        radius: float,
    ) -> Point | None:

        best_distance = radius
        best_delta = None

        for moving in moving_points:

            moved = Point(
                moving.x + move_delta.x,
                moving.y + move_delta.y,
            )

            for edge_start, edge_end in target_edges:

                projection = self._project_to_segment(
                    moved,
                    edge_start,
                    edge_end,
                )

                distance = self._distance(
                    moved,
                    projection,
                )

                if distance <= best_distance:

                    best_distance = distance

                    best_delta = Point(
                        projection.x - moving.x,
                        projection.y - moving.y,
                    )

        return best_delta

    # --------------------------------------------------------
    # ANGLE SNAP
    # --------------------------------------------------------

    def _angle_snap(
        self,
        start: Point,
        end: Point,
        increment_deg: float,
        length_step: float,
    ) -> Point:

        dx = end.x - start.x
        dy = end.y - start.y

        length = math.hypot(dx, dy)

        if length < 1e-6:
            return end

        angle = math.degrees(math.atan2(dy, dx))

        snapped_angle = (
            round(angle / increment_deg)
            * increment_deg
        )

        snapped_length = (
            round(length / length_step)
            * length_step
        )

        radians = math.radians(snapped_angle)

        return Point(
            start.x + math.cos(radians) * snapped_length,
            start.y + math.sin(radians) * snapped_length,
        )

    # --------------------------------------------------------
    # GRID
    # --------------------------------------------------------

    def _grid_snap(
        self,
        point: Point,
        grid_step: float,
    ) -> Point:

        return Point(
            round(point.x / grid_step) * grid_step,
            round(point.y / grid_step) * grid_step,
        )

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    def _project_to_segment(
        self,
        point: Point,
        start: Point,
        end: Point,
    ) -> Point:

        dx = end.x - start.x
        dy = end.y - start.y

        length_sq = dx * dx + dy * dy

        if length_sq <= 1e-6:
            return start

        t = (
            ((point.x - start.x) * dx)
            + ((point.y - start.y) * dy)
        ) / length_sq

        t = max(0.0, min(1.0, t))

        return Point(
            start.x + dx * t,
            start.y + dy * t,
        )

    def _distance(
        self,
        a: Point,
        b: Point,
    ) -> float:

        return math.hypot(
            b.x - a.x,
            b.y - a.y,
        )

    # --------------------------------------------------------
    # ZOOM
    # --------------------------------------------------------

    def dynamic_snap_distance(
        self,
        base_distance: float,
        zoom_scale: float,
        minimum: float = 5.0,
        maximum: float = 1200.0,
    ) -> float:

        zoom_scale = max(zoom_scale, 0.01)

        distance = base_distance / zoom_scale

        return max(
            minimum,
            min(maximum, distance),
        )