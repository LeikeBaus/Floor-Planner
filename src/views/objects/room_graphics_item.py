"""Graphics item for room polygon visualization."""

from __future__ import annotations

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QFont, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsPolygonItem,
    QGraphicsSimpleTextItem,
)

from models.room import Room


class RoomGraphicsItem(QGraphicsItemGroup):
    """Visual representation of a detected room polygon."""

    def __init__(self, room: Room, font_size: float = 96.0) -> None:
        super().__init__()
        self.room_id = room.id
        polygon = QPolygonF([QPointF(point.x, point.y) for point in room.polygon])
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        polygon_item = QGraphicsPolygonItem(polygon)
        polygon_item.setBrush(QColor("#DDEEFF"))
        pen = QPen(QColor("#7AA7D9"))
        pen.setWidthF(1.0)
        pen.setCosmetic(True)
        polygon_item.setPen(pen)
        self.addToGroup(polygon_item)

        center = polygon.boundingRect().center()
        label_x = center.x() + room.label_offset_x
        label_y = center.y() + room.label_offset_y

        name_item = QGraphicsSimpleTextItem(room.name)
        name_font = QFont()
        name_font.setPointSizeF(font_size)
        name_font.setBold(True)
        name_item.setFont(name_font)
        name_item.setBrush(QColor("#1E3A8A"))

        area_item = QGraphicsSimpleTextItem(f"{room.floor_area / 1_000_000.0:.2f} m2")
        area_font = QFont()
        area_font.setPointSizeF(font_size)
        area_item.setFont(area_font)
        area_item.setBrush(QColor("#1D4ED8"))

        name_bounds = name_item.boundingRect()
        area_bounds = area_item.boundingRect()
        name_item.setPos(label_x - name_bounds.width() / 2.0, label_y - font_size)
        area_item.setPos(label_x - area_bounds.width() / 2.0, label_y + font_size)

        self.addToGroup(name_item)
        self.addToGroup(area_item)

        self.setZValue(-1)
