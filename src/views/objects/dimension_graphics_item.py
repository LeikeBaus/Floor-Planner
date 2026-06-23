"""Graphics item for displaying a dimension line with text label."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
)

from geometry.point import Point
from models.dimension import Dimension


class DimensionGraphicsItem(QGraphicsItemGroup):
    """Visual representation of one linear dimension annotation."""

    def __init__(self, dimension: Dimension, font_size: float = 48.0) -> None:
        super().__init__()
        self.dimension_id = dimension.id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        draw_start = dimension.display_start or dimension.start
        draw_end = dimension.display_end or dimension.end

        self._line_item = QGraphicsLineItem(
            draw_start.x,
            draw_start.y,
            draw_end.x,
            draw_end.y,
        )
        self.addToGroup(self._line_item)

        self._helper_lines: list[QGraphicsLineItem] = []
        if dimension.display_start is not None and dimension.display_end is not None:
            for a, b in (
                (dimension.start, dimension.display_start),
                (dimension.end, dimension.display_end),
            ):
                helper = QGraphicsLineItem(a.x, a.y, b.x, b.y)
                self.addToGroup(helper)
                self._helper_lines.append(helper)

        value_m = dimension.value / 1000.0
        self._text_item = QGraphicsSimpleTextItem(f"{value_m:.2f} m")
        text_font = self._text_item.font()
        text_font.setPointSizeF(max(8.0, font_size))
        self._text_item.setFont(text_font)
        self._text_item.setBrush(QColor("#1E3A8A"))
        self._place_text_near_line(draw_start, draw_end)
        self.addToGroup(self._text_item)

        self._apply_visual_state(selected=False)
        self.setVisible(dimension.visible)
        self.setOpacity(dimension.opacity)
        self.setZValue(5)

    def itemChange(
        self,
        change: QGraphicsItem.GraphicsItemChange,
        value: object,
    ) -> object:
        """Update visual style when the dimension selection state changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._apply_visual_state(selected=bool(value))
        return super().itemChange(change, value)

    def _place_text_near_line(self, start: Point, end: Point) -> None:
        """Offset text label perpendicular to line for consistent legibility."""
        mid_x = (start.x + end.x) / 2.0
        mid_y = (start.y + end.y) / 2.0

        dx = end.x - start.x
        dy = end.y - start.y
        length = math.hypot(dx, dy)

        if length <= 1e-6:
            offset_x = 10.0
            offset_y = -14.0
        else:
            normal_x = -dy / length
            normal_y = dx / length
            offset_distance = 16.0
            offset_x = normal_x * offset_distance
            offset_y = normal_y * offset_distance

        text_rect = self._text_item.boundingRect()
        self._text_item.setPos(
            QPointF(
                mid_x + offset_x - text_rect.width() / 2.0,
                mid_y + offset_y - text_rect.height() / 2.0,
            )
        )

    def _apply_visual_state(self, selected: bool) -> None:
        """Apply selected/default styling to line and label."""
        line_color = QColor("#E01515") if selected else QColor("#0F49C5")
        text_color = QColor("#5E0A0A") if selected else QColor("#0A1C50")

        pen = QPen(line_color)
        pen.setWidthF(2.0 if selected else 1.5)
        pen.setCosmetic(True)
        self._line_item.setPen(pen)
        helper_pen = QPen(line_color)
        helper_pen.setWidthF(1.2)
        helper_pen.setStyle(Qt.PenStyle.DashLine)
        helper_pen.setCosmetic(True)
        for helper in self._helper_lines:
            helper.setPen(helper_pen)
        self._text_item.setBrush(text_color)
