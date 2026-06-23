"""Project settings dialog for editing defaults and behavior options."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from models.project_settings import ProjectSettings
from models.types import UnitSystem


class SettingsDialog(QDialog):
    """Dialog for editing project settings values."""

    def __init__(self, settings: ProjectSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Project Settings")
        self.setModal(True)
        self.resize(420, 360)

        self._exterior_wall_spin = QDoubleSpinBox(self)
        self._exterior_wall_spin.setRange(10.0, 2000.0)
        self._exterior_wall_spin.setDecimals(1)
        self._exterior_wall_spin.setSuffix(" mm")
        self._exterior_wall_spin.setValue(settings.default_exterior_wall_thickness)

        self._interior_wall_spin = QDoubleSpinBox(self)
        self._interior_wall_spin.setRange(10.0, 2000.0)
        self._interior_wall_spin.setDecimals(1)
        self._interior_wall_spin.setSuffix(" mm")
        self._interior_wall_spin.setValue(settings.default_interior_wall_thickness)

        self._grid_opacity_spin = QDoubleSpinBox(self)
        self._grid_opacity_spin.setRange(0.05, 1.0)
        self._grid_opacity_spin.setDecimals(2)
        self._grid_opacity_spin.setSingleStep(0.05)
        self._grid_opacity_spin.setValue(settings.grid_opacity)

        self._angle_snap_spin = QDoubleSpinBox(self)
        self._angle_snap_spin.setRange(1.0, 90.0)
        self._angle_snap_spin.setDecimals(1)
        self._angle_snap_spin.setSuffix(" deg")
        self._angle_snap_spin.setValue(settings.angle_snap_increment)

        self._snap_enabled_checkbox = QCheckBox(self)
        self._snap_enabled_checkbox.setChecked(settings.snap_enabled)

        self._show_dimensions_checkbox = QCheckBox(self)
        self._show_dimensions_checkbox.setChecked(settings.show_dimensions)

        self._dimension_opacity_spin = QDoubleSpinBox(self)
        self._dimension_opacity_spin.setRange(0.0, 1.0)
        self._dimension_opacity_spin.setDecimals(2)
        self._dimension_opacity_spin.setSingleStep(0.05)
        self._dimension_opacity_spin.setValue(settings.dimension_opacity)

        self._dimension_font_size_spin = QDoubleSpinBox(self)
        self._dimension_font_size_spin.setRange(48.0, 180.0)
        self._dimension_font_size_spin.setDecimals(1)
        self._dimension_font_size_spin.setSingleStep(12.0)
        self._dimension_font_size_spin.setValue(settings.dimension_font_size)

        self._lower_level_opacity_spin = QDoubleSpinBox(self)
        self._lower_level_opacity_spin.setRange(0.0, 1.0)
        self._lower_level_opacity_spin.setDecimals(2)
        self._lower_level_opacity_spin.setSingleStep(0.05)
        self._lower_level_opacity_spin.setValue(settings.lower_level_opacity)

        self._autosave_interval_spin = QSpinBox(self)
        self._autosave_interval_spin.setRange(10, 86_400)
        self._autosave_interval_spin.setSuffix(" s")
        self._autosave_interval_spin.setValue(settings.autosave_interval)

        self._unit_system_combo = QComboBox(self)
        self._unit_system_combo.addItem("Metric", UnitSystem.METRIC.value)
        index = self._unit_system_combo.findData(settings.unit_system.value)
        self._unit_system_combo.setCurrentIndex(index if index >= 0 else 0)

        form_layout = QFormLayout()
        form_layout.addRow("Exterior Wall Thickness", self._exterior_wall_spin)
        form_layout.addRow("Interior Wall Thickness", self._interior_wall_spin)
        form_layout.addRow("Grid Opacity", self._grid_opacity_spin)
        form_layout.addRow("Snap Enabled", self._snap_enabled_checkbox)
        form_layout.addRow("Angle Snap Increment", self._angle_snap_spin)
        form_layout.addRow("Show Dimensions", self._show_dimensions_checkbox)
        form_layout.addRow("Dimension Opacity", self._dimension_opacity_spin)
        form_layout.addRow("Dimension Font Size", self._dimension_font_size_spin)
        form_layout.addRow("Lower Level Opacity", self._lower_level_opacity_spin)
        form_layout.addRow("Autosave Interval", self._autosave_interval_spin)
        form_layout.addRow("Unit System", self._unit_system_combo)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def build_settings(self, base_settings: ProjectSettings) -> ProjectSettings:
        """Create updated ProjectSettings instance from dialog values."""
        unit_system = UnitSystem(str(self._unit_system_combo.currentData()))
        return ProjectSettings(
            default_exterior_wall_thickness=self._exterior_wall_spin.value(),
            default_interior_wall_thickness=self._interior_wall_spin.value(),
            grid_size=base_settings.grid_size,
            grid_opacity=self._grid_opacity_spin.value(),
            snap_enabled=self._snap_enabled_checkbox.isChecked(),
            snap_distance=base_settings.snap_distance,
            angle_snap_increment=self._angle_snap_spin.value(),
            autosave_interval=self._autosave_interval_spin.value(),
            lower_level_opacity=self._lower_level_opacity_spin.value(),
            show_dimensions=self._show_dimensions_checkbox.isChecked(),
            dimension_opacity=self._dimension_opacity_spin.value(),
            dimension_font_size=self._dimension_font_size_spin.value(),
            unit_system=unit_system,
        )
