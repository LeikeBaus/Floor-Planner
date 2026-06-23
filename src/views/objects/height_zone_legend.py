"""Height zone legend widget displaying zone types with colors and weight factors."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from models.height_zone import HeightZoneType


class ZoneTypeItem(QWidget):
    """Display a single zone type with color swatch and weight factor."""

    def __init__(self, zone_type: HeightZoneType, color_hex: str, weight_factor: float) -> None:
        super().__init__()
        self._zone_type = zone_type
        self._color_hex = color_hex
        self._weight_factor = weight_factor

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        color_swatch = QLabel(self)
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color_hex))
        color_swatch.setPixmap(pixmap)

        label_text = f"{zone_type.value} — {weight_factor:.1f}x"
        type_label = QLabel(label_text, self)

        layout.addWidget(color_swatch)
        layout.addWidget(type_label)
        layout.addStretch()
        self.setLayout(layout)


class HeightZoneLegend(QWidget):
    """Display legend of height zone types with colors and weight factors."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("Height Zone Types", self)
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self._items = [
            ZoneTypeItem(HeightZoneType.UNDER_1M, "#EF4444", 0.0),
            ZoneTypeItem(HeightZoneType.BETWEEN_1M_AND_2M, "#F59E0B", 0.5),
            ZoneTypeItem(HeightZoneType.ABOVE_2M, "#10B981", 1.0),
        ]

        for item in self._items:
            layout.addWidget(item)

        layout.addStretch()
        self.setLayout(layout)
