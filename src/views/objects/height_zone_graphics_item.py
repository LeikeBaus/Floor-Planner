"""Graphics item for displaying one generated height zone."""

from __future__ import annotations

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsPolygonItem

from models.height_zone import HeightZone, HeightZoneType


class HeightZoneGraphicsItem(QGraphicsPolygonItem):
    """Visual representation of one height zone polygon."""

    def __init__(self, height_zone: HeightZone) -> None:
        super().__init__()
        self.height_zone_id = height_zone.id
        polygon = QPolygonF([QPointF(point.x, point.y) for point in height_zone.polygon])
        self.setPolygon(polygon)
        self.setBrush(self._zone_brush(height_zone.zone_type))

        pen = QPen(QColor("#6B7280"))
        pen.setWidthF(1.0)
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setZValue(-0.5)

    def _zone_brush(self, zone_type: HeightZoneType) -> QColor:
        """Return semi-transparent fill color for zone class."""
        if zone_type == HeightZoneType.UNDER_1M:
            color = QColor("#EF4444")
        elif zone_type == HeightZoneType.BETWEEN_1M_AND_2M:
            color = QColor("#F59E0B")
        else:
            color = QColor("#10B981")

        color.setAlphaF(0.18)
        return color
