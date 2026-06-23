"""Graphics item for displaying an opening (hole) in a wall."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsRectItem

from models.opening import Opening


class OpeningGraphicsItem(QGraphicsItemGroup):
    """Visual representation of an opening in a wall."""

    def __init__(
        self,
        opening: Opening,
        start_point: QPointF,
        end_point: QPointF,
        wall_thickness: float,
    ) -> None:
        super().__init__()
        self.opening_id = opening.id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self._rect_item: QGraphicsRectItem | None = None

        # Calculate opening position along wall
        wall_dx = end_point.x() - start_point.x()
        wall_dy = end_point.y() - start_point.y()
        wall_length = (wall_dx**2 + wall_dy**2) ** 0.5

        if wall_length > 1e-6:
            # Normalize wall direction
            wall_ux = wall_dx / wall_length
            wall_uy = wall_dy / wall_length

            # Perpendicular direction (rotated 90 degrees)
            perp_ux = -wall_uy
            perp_uy = wall_ux

            # Opening center position along wall
            opening_center_x = start_point.x() + wall_ux * opening.position
            opening_center_y = start_point.y() + wall_uy * opening.position

            # Rectangle follows wall width and wall thickness.
            offset_dist = max(40.0, wall_thickness / 2.0)
            half_width = opening.width / 2.0

            left_top = QPointF(
                opening_center_x - wall_ux * half_width - perp_ux * offset_dist,
                opening_center_y - wall_uy * half_width - perp_uy * offset_dist,
            )

            rect_item = QGraphicsRectItem(0.0, 0.0, opening.width, offset_dist * 2.0)
            rect_item.setPos(left_top)
            rect_item.setRotation(math.degrees(math.atan2(wall_uy, wall_ux)))

            # Color based on opening type
            type_colors = {
                "passage": ("#7C3AED", "#EDE9FE"),  # Violet
                "alcove": ("#0891B2", "#CFFAFE"),  # Cyan
                "vent": ("#84CC16", "#ECFDF5"),  # Lime
                "custom": ("#71717A", "#F4F4F5"),  # Gray
            }
            line_color, fill_color = type_colors.get(opening.opening_type, type_colors["custom"])

            pen = QPen(QColor(line_color))
            pen.setWidthF(2.0)
            pen.setCosmetic(True)
            pen.setStyle(Qt.PenStyle.DotLine)
            rect_item.setPen(pen)
            rect_item.setBrush(QColor(fill_color))
            self.addToGroup(rect_item)
            self._rect_item = rect_item

        self.setZValue(9)

    def itemChange(
        self,
        change: QGraphicsItem.GraphicsItemChange,
        value: object,
    ) -> object:
        """Update visual style when the opening selection state changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self._rect_item is not None:
                if value:
                    pen = QPen(QColor("#EF4444"))
                    pen.setWidthF(2.5)
                else:
                    # Restore original color
                    pen = QPen(QColor("#7C3AED"))
                    pen.setWidthF(2.0)
                pen.setCosmetic(True)
                pen.setStyle(Qt.PenStyle.DotLine)
                self._rect_item.setPen(pen)
        return super().itemChange(change, value)
