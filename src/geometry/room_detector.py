"""Room detection based on wall centerline polygonization."""

from __future__ import annotations

import math

from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

from geometry.point import Point
from models.room import Room
from models.wall import Wall


class RoomDetector:
    """Detect enclosed rooms from a set of wall segments."""

    def detect_rooms(self, walls: list[Wall]) -> list[Room]:
        """Detect enclosed spaces using exact union of wall outer contours."""
        wall_polygons = [self._wall_polygon(wall) for wall in walls if wall.length > 0]
        wall_polygons = [polygon for polygon in wall_polygons if polygon is not None]

        if not wall_polygons:
            return []

        merged_walls = unary_union(wall_polygons)

        boundary_lines: list[LineString] = []
        geometries = list(getattr(merged_walls, "geoms", [merged_walls]))
        for geometry in geometries:
            exterior = getattr(geometry, "exterior", None)
            if exterior is not None:
                boundary_lines.append(LineString(exterior.coords))
            for interior in getattr(geometry, "interiors", []):
                boundary_lines.append(LineString(interior.coords))

        if not boundary_lines:
            return []

        merged_boundaries = unary_union(boundary_lines)

        rooms: list[Room] = []
        room_index = 1
        for polygon in polygonize(merged_boundaries):
            if polygon.area <= 1.0:
                continue

            # Ignore polygons that lie inside the wall solids themselves.
            centroid = polygon.representative_point()
            if merged_walls.buffer(0.01).contains(centroid):
                continue

            points = [Point(float(x), float(y)) for x, y in polygon.exterior.coords[:-1]]
            rooms.append(
                Room(
                    polygon=points,
                    floor_area=float(polygon.area),
                    living_area=float(polygon.area),
                    name=f"Room {room_index}",
                )
            )
            room_index += 1

        return rooms

    def _wall_polygon(self, wall: Wall) -> Polygon | None:
        """Build exact rectangular wall polygon from center line and thickness."""
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        length = math.hypot(dx, dy)
        if length <= 1e-9:
            return None

        nx = -dy / length
        ny = dx / length
        half = wall.thickness / 2.0
        corners = [
            (wall.start.x + nx * half, wall.start.y + ny * half),
            (wall.end.x + nx * half, wall.end.y + ny * half),
            (wall.end.x - nx * half, wall.end.y - ny * half),
            (wall.start.x - nx * half, wall.start.y - ny * half),
        ]
        return Polygon(corners)
