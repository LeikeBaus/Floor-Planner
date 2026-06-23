"""Roof slope interpolation and height-zone classification helpers."""

from __future__ import annotations

from math import hypot

from shapely.geometry import LineString, Polygon
from shapely.ops import split

from geometry.point import Point
from models.height_zone import HeightZone, HeightZoneType
from models.roof_slope import RoofSlope
from models.room import Room


class RoofSlopeEngine:
    """Computes heights and derived zone semantics from roof slopes."""

    def interpolate_height(self, roof_slope: RoofSlope, point: Point) -> float:
        """Return interpolated height at a point using linear interpolation between boundaries."""
        start_mid = self._midpoint(roof_slope.start_line_start, roof_slope.start_line_end)
        end_mid = self._midpoint(roof_slope.end_line_start, roof_slope.end_line_end)

        axis_x = end_mid.x - start_mid.x
        axis_y = end_mid.y - start_mid.y
        axis_len_sq = axis_x * axis_x + axis_y * axis_y
        if axis_len_sq <= 1e-9:
            return roof_slope.height_start

        point_x = point.x - start_mid.x
        point_y = point.y - start_mid.y
        t = (point_x * axis_x + point_y * axis_y) / axis_len_sq
        t_clamped = max(0.0, min(1.0, t))

        return roof_slope.height_start + (
            roof_slope.height_end - roof_slope.height_start
        ) * t_clamped

    def zone_type_for_height(self, height: float) -> HeightZoneType:
        """Map a single height to a living-area zone category."""
        if height < 1000.0:
            return HeightZoneType.UNDER_1M
        if height <= 2000.0:
            return HeightZoneType.BETWEEN_1M_AND_2M
        return HeightZoneType.ABOVE_2M

    def zone_type_for_range(self, min_height: float, max_height: float) -> HeightZoneType:
        """Map a height interval to a dominant zone category."""
        if max_height < 1000.0:
            return HeightZoneType.UNDER_1M
        if min_height >= 2000.0:
            return HeightZoneType.ABOVE_2M
        return HeightZoneType.BETWEEN_1M_AND_2M

    def build_height_zone(
        self,
        polygon: list[Point],
        min_height: float,
        max_height: float,
    ) -> HeightZone:
        """Build one persisted HeightZone from polygon and min/max height interval."""
        return HeightZone(
            polygon=polygon,
            min_height=min_height,
            max_height=max_height,
            zone_type=self.zone_type_for_range(min_height=min_height, max_height=max_height),
        )

    def generate_height_zones(
        self,
        roof_slopes: list[RoofSlope],
        rooms: list[Room],
    ) -> list[HeightZone]:
        """Generate split height zones per room from the active roof slope definition."""
        if not roof_slopes:
            return []

        slope = roof_slopes[0]
        zones: list[HeightZone] = []
        split_lines = self._height_threshold_lines(slope)
        slope_polygon = self._slope_polygon(slope)
        if slope_polygon is None or slope_polygon.is_empty or slope_polygon.area <= 1.0:
            return []

        for room in rooms:
            if not room.polygon:
                continue

            room_polygon = Polygon([(point.x, point.y) for point in room.polygon])
            if room_polygon.is_empty or room_polygon.area <= 1.0:
                continue

            overlap = room_polygon.intersection(slope_polygon)
            if overlap.is_empty or overlap.area <= 1.0:
                continue

            geometries = list(getattr(overlap, "geoms", [overlap]))
            parts = [geometry for geometry in geometries if isinstance(geometry, Polygon)]
            for split_line in split_lines:
                next_parts: list[Polygon] = []
                for part in parts:
                    if part.is_empty or part.area <= 1.0:
                        continue

                    split_result = split(part, split_line)
                    if len(split_result.geoms) <= 1:
                        next_parts.append(part)
                    else:
                        for geometry in split_result.geoms:
                            if isinstance(geometry, Polygon) and geometry.area > 1.0:
                                next_parts.append(geometry)

                parts = next_parts

            for part in parts:
                coords = list(part.exterior.coords)
                polygon_points = [Point(float(x), float(y)) for x, y in coords[:-1]]
                if len(polygon_points) < 3:
                    continue

                heights = [self.interpolate_height(slope, point) for point in polygon_points]
                centroid = Point(float(part.centroid.x), float(part.centroid.y))
                zone_type = self.zone_type_for_height(self.interpolate_height(slope, centroid))
                zones.append(
                    HeightZone(
                        polygon=polygon_points,
                        min_height=min(heights),
                        max_height=max(heights),
                        zone_type=zone_type,
                        room_id=room.id,
                    )
                )

        return zones

    def _height_threshold_lines(self, roof_slope: RoofSlope) -> list[LineString]:
        """Build iso-height split lines (1m and 2m) clipped by slope extent."""
        start_mid = self._midpoint(roof_slope.start_line_start, roof_slope.start_line_end)
        end_mid = self._midpoint(roof_slope.end_line_start, roof_slope.end_line_end)
        axis_x = end_mid.x - start_mid.x
        axis_y = end_mid.y - start_mid.y
        axis_len = hypot(axis_x, axis_y)
        if axis_len <= 1e-9:
            return []

        # Perpendicular direction for iso-height contours.
        perp_x = -axis_y / axis_len
        perp_y = axis_x / axis_len
        span = 1_000_000.0

        delta_h = roof_slope.height_end - roof_slope.height_start
        if abs(delta_h) <= 1e-9:
            return []

        lines: list[LineString] = []
        for threshold in (1000.0, 2000.0):
            t = (threshold - roof_slope.height_start) / delta_h
            if t <= 0.0 or t >= 1.0:
                continue

            anchor_x = start_mid.x + axis_x * t
            anchor_y = start_mid.y + axis_y * t
            lines.append(
                LineString(
                    [
                        (anchor_x - perp_x * span, anchor_y - perp_y * span),
                        (anchor_x + perp_x * span, anchor_y + perp_y * span),
                    ]
                )
            )

        return lines

    def _slope_polygon(self, roof_slope: RoofSlope) -> Polygon | None:
        """Return polygon enclosed by the roof slope boundary lines."""
        polygon = Polygon(
            [
                (roof_slope.start_line_start.x, roof_slope.start_line_start.y),
                (roof_slope.start_line_end.x, roof_slope.start_line_end.y),
                (roof_slope.end_line_end.x, roof_slope.end_line_end.y),
                (roof_slope.end_line_start.x, roof_slope.end_line_start.y),
            ]
        )
        if not polygon.is_valid:
            polygon = polygon.buffer(0)

        if polygon.is_empty or polygon.area <= 1.0:
            return None

        return polygon if isinstance(polygon, Polygon) else None

    def _midpoint(self, first: Point, second: Point) -> Point:
        """Return midpoint between two points."""
        return Point((first.x + second.x) / 2.0, (first.y + second.y) / 2.0)
