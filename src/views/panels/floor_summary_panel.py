"""Properties panel widget for displaying floor summary information."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from models.floor import Floor
from models.height_zone import HeightZoneType
from views.objects.height_zone_legend import HeightZoneLegend


class FloorSummaryPanel(QWidget):
    """Display floor-level summary information including area totals and zone breakdown."""

    one_level_overlay_toggled = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._floor_name_label = QLabel("Floor: -", self)
        self._floor_area_label = QLabel("Floor Area: 0.00 m²", self)
        self._living_area_label = QLabel("Living Area: 0.00 m²", self)
        self._room_count_label = QLabel("Rooms: 0", self)
        self._wall_count_label = QLabel("Walls: 0", self)
        self._zone_count_label = QLabel("Height Zones: 0", self)

        zone_stats_title = QLabel("Zone Breakdown", self)
        zone_stats_font = zone_stats_title.font()
        zone_stats_font.setBold(True)
        zone_stats_title.setFont(zone_stats_font)

        self._under_1m_label = QLabel("Under 1m: 0", self)
        self._between_1m_2m_label = QLabel("1m–2m: 0", self)
        self._above_2m_label = QLabel("Above 2m: 0", self)
        self._one_level_overlay_checkbox = QCheckBox("Show lower level", self)
        self._one_level_overlay_checkbox.toggled.connect(self.one_level_overlay_toggled.emit)

        legend = HeightZoneLegend()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self._floor_name_label)
        layout.addWidget(self._floor_area_label)
        layout.addWidget(self._living_area_label)
        layout.addWidget(self._room_count_label)
        layout.addWidget(self._wall_count_label)
        layout.addWidget(self._zone_count_label)
        layout.addWidget(zone_stats_title)
        layout.addWidget(self._under_1m_label)
        layout.addWidget(self._between_1m_2m_label)
        layout.addWidget(self._above_2m_label)
        layout.addWidget(self._one_level_overlay_checkbox)
        layout.addWidget(legend)
        layout.addStretch()
        self.setLayout(layout)

    def update_floor_info(self, floor: Floor) -> None:
        """Update all labels to reflect current floor state."""
        self._floor_name_label.setText(f"Floor: {floor.name}")
        floor_area_m2 = floor.floor_area_total / 1_000_000.0
        living_area_m2 = floor.living_area_total / 1_000_000.0
        self._floor_area_label.setText(f"Floor Area: {floor_area_m2:.2f} m²")
        self._living_area_label.setText(f"Living Area: {living_area_m2:.2f} m²")
        self._room_count_label.setText(f"Rooms: {len(floor.rooms)}")
        self._wall_count_label.setText(f"Walls: {len(floor.walls)}")
        self._zone_count_label.setText(f"Height Zones: {len(floor.height_zones)}")

        under_1m_count = sum(
            1 for zone in floor.height_zones
            if zone.zone_type == HeightZoneType.UNDER_1M
        )
        between_1m_2m_count = sum(
            1 for zone in floor.height_zones
            if zone.zone_type == HeightZoneType.BETWEEN_1M_AND_2M
        )
        above_2m_count = sum(
            1 for zone in floor.height_zones
            if zone.zone_type == HeightZoneType.ABOVE_2M
        )

        self._under_1m_label.setText(f"Under 1m: {under_1m_count}")
        self._between_1m_2m_label.setText(f"1m–2m: {between_1m_2m_count}")
        self._above_2m_label.setText(f"Above 2m: {above_2m_count}")

    def set_one_level_overlay_enabled(self, enabled: bool) -> None:
        """Update checkbox state without emitting duplicate updates."""
        self._one_level_overlay_checkbox.blockSignals(True)
        self._one_level_overlay_checkbox.setChecked(enabled)
        self._one_level_overlay_checkbox.blockSignals(False)
