"""Snapping helpers for precise point placement in the drawing workflow."""

from __future__ import annotations

from dataclasses import dataclass
from math import dist

from geometry.point import Point


@dataclass(frozen=True, slots=True)
class SnapResult:
    """Result of a snapping query."""

    point: Point
    snap_type: str


class SnapEngine:
    """Computes snapped points against wall endpoints and grid."""

    SNAP_NONE = "NONE"
    SNAP_INTERSECTION = "INTERSECTION"
    SNAP_ENDPOINT = "ENDPOINT"
    SNAP_MIDPOINT = "MIDPOINT"
    SNAP_GRID = "GRID"

    def dynamic_snap_distance(
        self,
        base_distance: float,
        zoom_scale: float,
        min_distance: float = 5.0,
        max_distance: float = 1200.0,
    ) -> float:
        """Return zoom-adjusted snap distance constrained to safe bounds."""
        safe_zoom = max(zoom_scale, 0.01)
        scaled_distance = max(0.0, base_distance) / safe_zoom
        return max(min_distance, min(max_distance, scaled_distance))

    def snap_point(
        self,
        input_point: Point,
        intersection_targets: list[Point],
        endpoint_targets: list[Point],
        midpoint_targets: list[Point],
        grid_size: float,
        snap_distance: float,
    ) -> SnapResult:
        """Return best snapped point according to configured priority."""
        endpoint = self._nearest_within_radius(input_point, endpoint_targets, snap_distance)
        if endpoint is not None:
            return SnapResult(point=endpoint, snap_type=self.SNAP_ENDPOINT)

        midpoint = self._nearest_within_radius(input_point, midpoint_targets, snap_distance)
        if midpoint is not None:
            return SnapResult(point=midpoint, snap_type=self.SNAP_MIDPOINT)

        intersection = self._nearest_within_radius(input_point, intersection_targets, snap_distance)
        if intersection is not None:
            return SnapResult(point=intersection, snap_type=self.SNAP_INTERSECTION)

        grid_point = self._grid_snap(input_point, grid_size)
        if self._distance(input_point, grid_point) <= snap_distance:
            return SnapResult(point=grid_point, snap_type=self.SNAP_GRID)

        return SnapResult(point=input_point, snap_type=self.SNAP_NONE)

    def _nearest_within_radius(
        self,
        source: Point,
        targets: list[Point],
        radius: float,
    ) -> Point | None:
        """Return nearest point in radius, otherwise None."""
        best_point: Point | None = None
        best_distance = radius

        for target in targets:
            candidate_distance = self._distance(source, target)
            if candidate_distance <= best_distance:
                best_distance = candidate_distance
                best_point = target

        return best_point

    def _grid_snap(self, point: Point, grid_size: float) -> Point:
        """Return nearest grid intersection for given point."""
        if grid_size <= 0:
            return point

        snapped_x = round(point.x / grid_size) * grid_size
        snapped_y = round(point.y / grid_size) * grid_size
        return Point(snapped_x, snapped_y)

    def _distance(self, first: Point, second: Point) -> float:
        """Compute euclidean distance between two points."""
        return dist((first.x, first.y), (second.x, second.y))
