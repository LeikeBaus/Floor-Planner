"""Editable properties panel for the currently selected floor object."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from models.dimension import Dimension
from models.door import Door
from models.opening import Opening
from models.roof_slope import RoofSlope
from models.room import Room
from models.stair import Stair
from models.wall import Wall, WallType
from models.window import Window
from views.scene.drawing_scene import DrawingScene


class ObjectPropertiesPanel(QWidget):
    """Display and edit parameters for exactly one selected object."""

    property_change_requested = pyqtSignal(object, dict, float, float)

    def __init__(self) -> None:
        super().__init__()
        self._form = QFormLayout()
        self._state_label = QLabel("Select exactly one object", self)
        self._suspend_updates = False

        layout = QVBoxLayout(self)
        layout.addWidget(self._state_label)
        layout.addLayout(self._form)
        layout.addStretch()
        self.setLayout(layout)

        self._current_editor_values: dict[str, object] = {}
        self._current_target: (
            Wall | Window | Door | Opening | Stair | RoofSlope | Dimension | Room | None
        ) = None
        self._on_changed: Callable[[], None] | None = None
        self._scene: DrawingScene | None = None
        self._default_exterior_wall_thickness: float = 300.0
        self._default_interior_wall_thickness: float = 110.0

    def set_wall_defaults(self, exterior_thickness: float, interior_thickness: float) -> None:
        """Set default thicknesses used when changing wall type."""
        self._default_exterior_wall_thickness = max(1.0, exterior_thickness)
        self._default_interior_wall_thickness = max(1.0, interior_thickness)

    def set_selection(
        self,
        scene: DrawingScene,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        """Render controls for selected object if exactly one item is selected."""
        self._clear_form()
        self._on_changed = on_changed
        self._scene = scene
        self._suspend_updates = True

        selected_targets: list[
            tuple[str, Wall | Window | Door | Opening | Stair | RoofSlope | Dimension | Room]
        ] = []
        selected_targets += [("wall", wall) for wall in scene.selected_walls()]
        selected_targets += [("window", window) for window in scene.selected_windows()]
        selected_targets += [("door", door) for door in scene.selected_doors()]
        selected_targets += [("opening", opening) for opening in scene.selected_openings()]
        selected_targets += [("stair", stair) for stair in scene.selected_stairs()]
        selected_targets += [("roof", slope) for slope in scene.selected_roof_slopes()]
        selected_targets += [
            ("dimension", dimension) for dimension in scene.selected_manual_dimensions()
        ]
        selected_targets += [("room", room) for room in scene.selected_rooms()]

        if len(selected_targets) != 1:
            self._state_label.setText("Select exactly one object")
            self._suspend_updates = False
            return

        kind, target = selected_targets[0]
        self._current_target = target
        self._state_label.setText(f"Selected: {kind}")

        if kind == "wall" and isinstance(target, Wall):
            self._add_combo(
                "wall_type",
                [WallType.EXTERIOR.value, WallType.INTERIOR.value],
                target.wall_type.value,
            )
            self._add_spin("start_x", target.start.x, -1_000_000.0, 1_000_000.0)
            self._add_spin("start_y", target.start.y, -1_000_000.0, 1_000_000.0)
            self._add_spin("end_x", target.end.x, -1_000_000.0, 1_000_000.0)
            self._add_spin("end_y", target.end.y, -1_000_000.0, 1_000_000.0)
            self._add_spin("length_mm", target.length, 1.0, 1_000_000.0)
            self._add_spin("thickness_mm", target.thickness, 10.0, 2000.0)
        elif kind == "window" and isinstance(target, Window):
            self._add_spin("position_mm", target.position, 0.0, 1_000_000.0)
            self._add_spin("width_mm", target.width, 100.0, 10_000.0)
            self._add_spin("height_mm", target.height, 100.0, 10_000.0)
        elif kind == "door" and isinstance(target, Door):
            self._add_spin("position_mm", target.position, 0.0, 1_000_000.0)
            self._add_spin("width_mm", target.width, 100.0, 10_000.0)
            self._add_spin("height_mm", target.height, 100.0, 10_000.0)
            self._add_combo(
                "swing_direction",
                ["left_out", "right_out", "left_in", "right_in"],
                target.swing_direction,
            )
        elif kind == "opening" and isinstance(target, Opening):
            self._add_spin("position_mm", target.position, 0.0, 1_000_000.0)
            self._add_spin("width_mm", target.width, 100.0, 10_000.0)
            self._add_spin("height_mm", target.height, 100.0, 10_000.0)
        elif kind == "stair" and isinstance(target, Stair):
            self._add_spin("position_x", target.position_x, -1_000_000.0, 1_000_000.0)
            self._add_spin("position_y", target.position_y, -1_000_000.0, 1_000_000.0)
            self._add_spin("width_mm", target.width, 100.0, 10_000.0)
            self._add_spin("depth_mm", target.depth, 100.0, 10_000.0)
            self._add_spin("orientation_deg", target.orientation_degrees, 0.0, 360.0)
        elif kind == "roof" and isinstance(target, RoofSlope):
            self._add_spin(
                "start_x",
                target.start_line_start.x,
                -1_000_000.0,
                1_000_000.0,
            )
            self._add_spin(
                "start_y",
                target.start_line_start.y,
                -1_000_000.0,
                1_000_000.0,
            )
            self._add_spin(
                "end_x",
                target.start_line_end.x,
                -1_000_000.0,
                1_000_000.0,
            )
            self._add_spin(
                "end_y",
                target.start_line_end.y,
                -1_000_000.0,
                1_000_000.0,
            )
            self._add_spin("length_mm", self._roof_slope_length(target), 1.0, 1_000_000.0)
            self._add_spin("height_start", target.height_start, 0.0, 10_000.0)
            self._add_spin("height_end", target.height_end, 0.0, 10_000.0)
        elif kind == "dimension" and isinstance(target, Dimension):
            self._add_spin("opacity", target.opacity, 0.0, 1.0)
        elif kind == "room" and isinstance(target, Room):
            self._add_editable_text("name", target.name)
            self._add_checkbox("include_in_living_area", target.include_in_living_area)

        self._suspend_updates = False

    def _add_spin(self, key: str, value: float, minimum: float, maximum: float) -> None:
        spin = QDoubleSpinBox(self)
        spin.setRange(minimum, maximum)
        spin.setDecimals(2)
        spin.setValue(float(value))
        spin.editingFinished.connect(self._apply_changes)
        self._form.addRow(key, spin)
        self._current_editor_values[key] = spin

    def _add_combo(self, key: str, options: list[str], selected: str) -> None:
        combo = QComboBox(self)
        for option in options:
            combo.addItem(option)
        index = max(0, options.index(selected) if selected in options else 0)
        combo.setCurrentIndex(index)
        combo.currentTextChanged.connect(self._apply_changes)
        self._form.addRow(key, combo)
        self._current_editor_values[key] = combo

    def _add_checkbox(self, key: str, checked: bool) -> None:
        checkbox = QCheckBox(self)
        checkbox.setChecked(checked)
        checkbox.toggled.connect(self._apply_changes)
        self._form.addRow(key, checkbox)
        self._current_editor_values[key] = checkbox

    def _add_editable_text(self, key: str, selected: str) -> None:
        """Add an editable text field backed by QComboBox."""
        combo = QComboBox(self)
        combo.setEditable(True)
        combo.addItem(selected)
        combo.setCurrentText(selected)
        line_edit = combo.lineEdit()
        if line_edit is not None:
            line_edit.editingFinished.connect(self._apply_changes)
        else:
            combo.currentTextChanged.connect(self._apply_changes)
        self._form.addRow(key, combo)
        self._current_editor_values[key] = combo

    def _apply_changes(self, *_: object) -> None:
        if self._suspend_updates:
            return
        target = self._current_target
        if target is None:
            return

        values: dict[str, float | str | bool] = {}
        for key, widget in self._current_editor_values.items():
            if isinstance(widget, QDoubleSpinBox):
                values[key] = float(widget.value())
            elif isinstance(widget, QComboBox):
                values[key] = str(widget.currentText())
            elif isinstance(widget, QCheckBox):
                values[key] = bool(widget.isChecked())

        self.property_change_requested.emit(
            target,
            values,
            self._default_exterior_wall_thickness,
            self._default_interior_wall_thickness,
        )

        if self._on_changed is not None:
            self._on_changed()

    def _clear_form(self) -> None:
        while self._form.rowCount() > 0:
            self._form.removeRow(0)
        self._current_editor_values.clear()
        self._current_target = None

    def _roof_slope_length(self, roof_slope: RoofSlope) -> float:
        """Return perpendicular distance between the roof slope boundary lines."""
        dx: float = roof_slope.end_line_start.x - roof_slope.start_line_start.x
        dy: float = roof_slope.end_line_start.y - roof_slope.start_line_start.y
        length: float = (dx * dx + dy * dy) ** 0.5
        return length
