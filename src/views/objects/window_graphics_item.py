"""Graphics item for displaying a window on a wall."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QGraphicsRectItem,
)

from models.window import Window


class WindowGraphicsItem(QGraphicsItemGroup):
    """Visual representation of a window on a wall."""

    def __init__(
        self,
        window: Window,
        start_point: QPointF,
        end_point: QPointF,
        wall_thickness: float,
    ) -> None:
        super().__init__()
        self.window_id = window.id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self._rect_item: QGraphicsRectItem | None = None
        self._line_items: list[QGraphicsLineItem] = []

        # Calculate window rectangle position along wall
        wall_dx = end_point.x() - start_point.x()
        wall_dy = end_point.y() - start_point.y()
        wall_length = math.hypot(wall_dx, wall_dy)

        if wall_length > 1e-6:
            # Normalize wall direction
            wall_ux = wall_dx / wall_length
            wall_uy = wall_dy / wall_length

            # Perpendicular direction (rotated 90 degrees)
            perp_ux = -wall_uy
            perp_uy = wall_ux

            # Window center position along wall
            window_center_x = start_point.x() + wall_ux * window.position
            window_center_y = start_point.y() + wall_uy * window.position

            # Rectangle follows wall width and wall thickness.
            offset_dist = max(40.0, wall_thickness / 2.0)
            half_width = window.width / 2.0

            left_top = QPointF(
                window_center_x - wall_ux * half_width - perp_ux * offset_dist,
                window_center_y - wall_uy * half_width - perp_uy * offset_dist,
            )

            rect_item = QGraphicsRectItem(0.0, 0.0, window.width, offset_dist * 2.0)
            rect_item.setPos(left_top)
            rect_item.setRotation(math.degrees(math.atan2(wall_uy, wall_ux)))

            pen = QPen(QColor("#059669"))
            pen.setWidthF(2.0)
            pen.setCosmetic(True)
            rect_item.setPen(pen)
            rect_item.setBrush(QColor("#D1FAE5"))
            self.addToGroup(rect_item)
            self._rect_item = rect_item

            inset = max(6.0, offset_dist * 0.25)
            for y in (inset, offset_dist * 2.0 - inset):
                line = QGraphicsLineItem(6.0, y, window.width - 6.0, y)
                line.setPos(left_top)
                line.setRotation(math.degrees(math.atan2(wall_uy, wall_ux)))
                line_pen = QPen(QColor("#047857"))
                line_pen.setWidthF(1.5)
                line_pen.setCosmetic(True)
                line.setPen(line_pen)
                self.addToGroup(line)
                self._line_items.append(line)

        self.setZValue(10)

    def itemChange(
        self,
        change: QGraphicsItem.GraphicsItemChange,
        value: object,
    ) -> object:
        """Update visual style when the window selection state changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self._rect_item is not None:
                if value:
                    pen = QPen(QColor("#DC2626"))
                    pen.setWidthF(2.5)
                    line_color = QColor("#B91C1C")
                else:
                    pen = QPen(QColor("#059669"))
                    pen.setWidthF(2.0)
                    line_color = QColor("#047857")
                pen.setCosmetic(True)
                self._rect_item.setPen(pen)
                for line in self._line_items:
                    line_pen = QPen(line_color)
                    line_pen.setWidthF(1.5)
                    line_pen.setCosmetic(True)
                    line.setPen(line_pen)
        return super().itemChange(change, value)
