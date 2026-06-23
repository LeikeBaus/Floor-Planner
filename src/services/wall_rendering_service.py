"""Rendering helper for merged wall path generation with geometry caching."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath, QPolygonF

from models.wall import Wall


class WallRenderingService:
    """Build and cache a unified wall contour path for rendering."""

    def __init__(self) -> None:
        self._cached_signature: tuple[tuple[str, float, float, float, float, float], ...] | None = None
        self._cached_path = QPainterPath()

    def build_merged_wall_path(self, walls: list[Wall]) -> QPainterPath:
        """Return a merged wall path containing only the outer contour."""
        signature = self._build_signature(walls)
        if signature == self._cached_signature:
            return QPainterPath(self._cached_path)

        wall_polygons = [self.wall_polygon(wall) for wall in walls]
        merged_path = self.build_merged_path_from_polygons(wall_polygons)

        self._cached_signature = signature
        self._cached_path = QPainterPath(merged_path)
        return QPainterPath(merged_path)

    def invalidate_cache(self) -> None:
        """Force a recomputation on next merged path build."""
        self._cached_signature = None
        self._cached_path = QPainterPath()

    @staticmethod
    def wall_polygon(wall: Wall) -> QPolygonF:
        """Build the wall rectangle polygon from centerline and thickness."""
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return QPolygonF()

        half = wall.thickness / 2.0
        nx = -dy / length
        ny = dx / length
        p1 = QPointF(wall.start.x + nx * half, wall.start.y + ny * half)
        p2 = QPointF(wall.end.x + nx * half, wall.end.y + ny * half)
        p3 = QPointF(wall.end.x - nx * half, wall.end.y - ny * half)
        p4 = QPointF(wall.start.x - nx * half, wall.start.y - ny * half)
        return QPolygonF([p1, p2, p3, p4])

    @staticmethod
    def build_merged_path_from_polygons(polygons: list[QPolygonF]) -> QPainterPath:
        """Merge a list of polygons into a single contour path."""
        merged_path = QPainterPath()
        for polygon in polygons:
            if polygon.isEmpty():
                continue
            polygon_path = QPainterPath()
            polygon_path.addPolygon(polygon)
            polygon_path.closeSubpath()
            merged_path = polygon_path if merged_path.isEmpty() else merged_path.united(polygon_path)
        return merged_path

    def _build_signature(self, walls: list[Wall]) -> tuple[tuple[str, float, float, float, float, float], ...]:
        """Build a stable signature for wall geometry cache invalidation."""
        signature: list[tuple[str, float, float, float, float, float]] = []
        for wall in walls:
            signature.append(
                (
                    wall.id,
                    wall.start.x,
                    wall.start.y,
                    wall.end.x,
                    wall.end.y,
                    wall.thickness,
                )
            )

        signature.sort(key=lambda value: value[0])
        return tuple(signature)
