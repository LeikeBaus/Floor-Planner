"""Graphics item for displaying a roof slope definition."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsLineItem

from models.roof_slope import RoofSlope


class RoofSlopeGraphicsItem(QGraphicsItemGroup):
    """Visual representation of a roof slope boundary pair."""

    def __init__(self, roof_slope: RoofSlope) -> None:
        super().__init__()
        self.roof_slope_id = roof_slope.id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        start_line = QGraphicsLineItem(
            roof_slope.start_line_start.x,
            roof_slope.start_line_start.y,
            roof_slope.start_line_end.x,
            roof_slope.start_line_end.y,
        )
        start_pen = QPen(QColor("#B45309"))
        start_pen.setWidthF(2.5)
        start_pen.setCosmetic(True)
        start_line.setPen(start_pen)
        self.addToGroup(start_line)

        end_line = QGraphicsLineItem(
            roof_slope.end_line_start.x,
            roof_slope.end_line_start.y,
            roof_slope.end_line_end.x,
            roof_slope.end_line_end.y,
        )
        end_pen = QPen(QColor("#92400E"))
        end_pen.setWidthF(2.0)
        end_pen.setCosmetic(True)
        end_pen.setStyle(start_pen.style())
        end_line.setPen(end_pen)
        self.addToGroup(end_line)

        self._start_line = start_line
        self._end_line = end_line
        self.setZValue(7)

    def itemChange(
        self,
        change: QGraphicsItem.GraphicsItemChange,
        value: object,
    ) -> object:
        """Update visual style when selection state changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:
                selected_start_pen = QPen(QColor("#EF4444"))
                selected_start_pen.setWidthF(3.0)
                selected_start_pen.setCosmetic(True)
                self._start_line.setPen(selected_start_pen)

                selected_end_pen = QPen(QColor("#DC2626"))
                selected_end_pen.setWidthF(2.5)
                selected_end_pen.setCosmetic(True)
                self._end_line.setPen(selected_end_pen)
            else:
                normal_start_pen = QPen(QColor("#B45309"))
                normal_start_pen.setWidthF(2.5)
                normal_start_pen.setCosmetic(True)
                self._start_line.setPen(normal_start_pen)

                normal_end_pen = QPen(QColor("#92400E"))
                normal_end_pen.setWidthF(2.0)
                normal_end_pen.setCosmetic(True)
                self._end_line.setPen(normal_end_pen)

        return super().itemChange(change, value)
