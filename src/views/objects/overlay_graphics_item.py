"""Graphics item for displaying an overlay projection of another floor."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsPolygonItem

from models.room import Room
from models.wall import Wall


class OverlayGraphicsItem(QGraphicsItemGroup):
    """Visual representation of projected overlay walls from another floor."""

    def __init__(self, walls: list[Wall], rooms: list[Room], opacity: float = 0.3) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self._opacity = max(0.0, min(1.0, opacity))
        self._wall_polygons: list[QGraphicsPolygonItem] = []
        self._room_polygons: list[QGraphicsPolygonItem] = []

        for wall in walls:
            wall_polygon = self._wall_to_polygon(wall)
            if wall_polygon is None:
                continue
            item = QGraphicsPolygonItem(wall_polygon)
            self.addToGroup(item)
            self._wall_polygons.append(item)

        for room in rooms:
            if len(room.polygon) < 3:
                continue
            polygon = QPolygonF([QPointF(p.x, p.y) for p in room.polygon])
            item = QGraphicsPolygonItem(polygon)
            self.addToGroup(item)
            self._room_polygons.append(item)

        self._apply_style()

        # Position overlay at low z-value (behind main floor elements)
        self.setZValue(-2)

    def set_opacity(self, opacity: float) -> None:
        """Update opacity of all overlay lines."""
        self._opacity = max(0.0, min(1.0, opacity))
        self._apply_style()

    def _apply_style(self) -> None:
        """Apply current opacity and colors to wall and room overlay polygons."""
        wall_fill = QColor("#9CA3AF")
        wall_fill.setAlphaF(min(1.0, self._opacity * 0.55))
        wall_edge = QColor("#4B5563")
        wall_edge.setAlphaF(min(1.0, self._opacity * 0.95))

        room_fill = QColor("#DBEAFE")
        room_fill.setAlphaF(min(1.0, self._opacity * 0.45))
        room_edge = QColor("#60A5FA")
        room_edge.setAlphaF(min(1.0, self._opacity * 0.8))

        for polygon_item in self._wall_polygons:
            pen = QPen(wall_edge)
            pen.setWidthF(1.2)
            pen.setCosmetic(True)
            polygon_item.setPen(pen)
            polygon_item.setBrush(wall_fill)

        for polygon_item in self._room_polygons:
            pen = QPen(room_edge)
            pen.setWidthF(1.0)
            pen.setCosmetic(True)
            polygon_item.setPen(pen)
            polygon_item.setBrush(room_fill)

    def _wall_to_polygon(self, wall: Wall) -> QPolygonF | None:
        """Build wall rectangle polygon from centerline and thickness."""
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            return None

        nx = -dy / length
        ny = dx / length
        half = wall.thickness / 2.0
        p1 = QPointF(wall.start.x + nx * half, wall.start.y + ny * half)
        p2 = QPointF(wall.end.x + nx * half, wall.end.y + ny * half)
        p3 = QPointF(wall.end.x - nx * half, wall.end.y - ny * half)
        p4 = QPointF(wall.start.x - nx * half, wall.start.y - ny * half)
        return QPolygonF([p1, p2, p3, p4])

    def set_visible(self, visible: bool) -> None:
        """Toggle visibility of overlay."""
        self.setVisible(visible)
