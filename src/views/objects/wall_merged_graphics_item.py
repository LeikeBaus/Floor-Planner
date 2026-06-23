"""Graphics item that renders the merged wall contour for the active floor."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainterPath
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from views.objects.wall_graphics_item import WallGraphicsItem


class WallMergedGraphicsItem(QGraphicsPathItem):
    """Non-selectable graphics item for the merged wall rendering path."""

    def __init__(self, path: QPainterPath) -> None:
        super().__init__(path)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setPen(WallGraphicsItem.default_pen())
        self.setBrush(WallGraphicsItem.default_brush())
        self.setZValue(WallGraphicsItem.default_z_value())

    def set_merged_path(self, path: QPainterPath) -> None:
        """Replace rendered geometry while preserving visual style."""
        self.setPath(path)
