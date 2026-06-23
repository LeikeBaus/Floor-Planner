"""Graphics item for rendering walls as filled rectangles."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPolygonItem

from models.wall import Wall
from services.wall_rendering_service import WallRenderingService


class WallGraphicsItem(QGraphicsPolygonItem):
    """Visual representation of a wall model object."""

    def __init__(self, wall: Wall, interaction_only: bool = False) -> None:
        super().__init__()
        self.wall_id = wall.id
        self._wall = wall
        self._interaction_only = interaction_only
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self._apply_wall_geometry()

    def _apply_wall_geometry(self) -> None:
        polygon = WallRenderingService.wall_polygon(self._wall)
        self.setPolygon(polygon)

        if self._interaction_only:
            self.setPen(QPen(Qt.PenStyle.NoPen))
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.setZValue(21)
            return

        self.setPen(self.default_pen())
        self.setBrush(self.default_brush())
        self.setZValue(self.default_z_value())

    @staticmethod
    def default_pen() -> QPen:
        """Return the default pen used by wall rendering."""
        color = QColor("#1F1608")
        pen = QPen(color)
        pen.setWidthF(1.6)
        pen.setCosmetic(True)
        return pen

    @staticmethod
    def default_brush() -> QBrush:
        """Return the default brush used by wall rendering."""
        brush = QBrush(QColor("#E9DFC8"))
        brush.setStyle(Qt.BrushStyle.BDiagPattern)
        return brush

    @staticmethod
    def default_z_value() -> float:
        """Return z-value used by wall rendering."""
        return 20.0
