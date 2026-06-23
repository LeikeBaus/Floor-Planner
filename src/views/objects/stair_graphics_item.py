"""Graphics item for displaying a staircase."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsPathItem, QGraphicsRectItem

from models.stair import Stair


class StairGraphicsItem(QGraphicsItemGroup):
    """Visual representation of a staircase."""

    def __init__(self, stair: Stair) -> None:
        super().__init__()
        self.stair_id = stair.id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Draw stair as rectangle with diagonal steps indicator
        rect_item = QGraphicsRectItem(0.0, 0.0, stair.width, stair.depth)
        pen = QPen(QColor("#059669"))  # Green for stairs
        pen.setWidthF(2.5)
        pen.setCosmetic(True)
        rect_item.setPen(pen)
        rect_item.setBrush(QColor("#D1FAE5"))  # Light green fill
        self.addToGroup(rect_item)
        self._rect_item = rect_item

        # Add diagonal lines to indicate steps
        path = QPainterPath()
        tread_length_mm = 280.0
        step_count = max(1, int(round(stair.width / tread_length_mm)))
        self._step_count = step_count
        step_spacing = stair.width / step_count
        for i in range(step_count + 1):
            x = step_spacing * i
            path.moveTo(x, 0.0)
            path.lineTo(x, stair.depth)

        path_item = QGraphicsPathItem(path)
        step_pen = QPen(QColor("#10B981"))  # Slightly darker green
        step_pen.setWidthF(1.0)
        step_pen.setCosmetic(True)
        path_item.setPen(step_pen)
        self.addToGroup(path_item)

        arrow_path = QPainterPath()
        center_x = stair.width / 2.0
        center_y = stair.depth / 2.0
        arrow_size = min(stair.width, stair.depth) * 0.3
        ux = 1.0
        uy = 0.0
        vx = -uy
        vy = ux

        tip_x = center_x + ux * arrow_size
        tip_y = center_y + uy * arrow_size
        base_center_x = center_x - ux * arrow_size * 0.25
        base_center_y = center_y - uy * arrow_size * 0.25
        left_x = base_center_x + vx * arrow_size * 0.35
        left_y = base_center_y + vy * arrow_size * 0.35
        right_x = base_center_x - vx * arrow_size * 0.35
        right_y = base_center_y - vy * arrow_size * 0.35

        arrow_path.moveTo(tip_x, tip_y)
        arrow_path.lineTo(left_x, left_y)
        arrow_path.lineTo(right_x, right_y)
        arrow_path.closeSubpath()

        arrow_item = QGraphicsPathItem(arrow_path)
        arrow_pen = QPen(QColor("#065F46"))
        arrow_pen.setWidthF(1.2)
        arrow_pen.setCosmetic(True)
        arrow_item.setPen(arrow_pen)
        arrow_item.setBrush(QColor("#047857"))
        self.addToGroup(arrow_item)
        self._arrow_item = arrow_item

        # Position based on floor floor connection (visual placement)
        self.setPos(stair.position_x, stair.position_y)
        self.setTransformOriginPoint(stair.width / 2.0, stair.depth / 2.0)
        self.setRotation(stair.orientation_degrees)
        self.setZValue(8)

    def itemChange(
        self,
        change: QGraphicsItem.GraphicsItemChange,
        value: object,
    ) -> object:
        """Update visual style when selection state changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if hasattr(self, "_rect_item") and self._rect_item is not None:
                if value:
                    pen = QPen(QColor("#EF4444"))
                    pen.setWidthF(3.0)
                    arrow_color = QColor("#B91C1C")
                else:
                    pen = QPen(QColor("#059669"))
                    pen.setWidthF(2.5)
                    arrow_color = QColor("#047857")
                pen.setCosmetic(True)
                self._rect_item.setPen(pen)
                if hasattr(self, "_arrow_item") and self._arrow_item is not None:
                    self._arrow_item.setBrush(arrow_color)
        return super().itemChange(change, value)
