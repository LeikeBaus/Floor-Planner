"""Controller for drawing-focused application workflows."""

from __future__ import annotations

from collections.abc import Mapping

from PyQt6.QtCore import QObject, pyqtSignal

from models.floor import Floor
from models.project import Project
from services.drawing_service import DrawingService
from views.scene.drawing_scene import DrawingScene
from views.widgets.statusbar import StatusBar


class DrawingController(QObject):
    """Coordinates drawing domain updates requested by views."""

    properties_refresh_requested = pyqtSignal()

    def __init__(self, service: DrawingService) -> None:
        super().__init__()
        self._service = service
        self._status_bar: StatusBar | None = None

    def configure_status_bar(self, status_bar: StatusBar) -> None:
        """Attach status bar to publish drawing feedback events."""
        self._status_bar = status_bar

    def recalculate_floor(self, project: Project, floor: Floor) -> None:
        """Recalculate all derived floor data based on current project settings."""
        self._service.recalculate_floor(floor, project.settings)

    def on_cursor_world_changed(self, x_mm: float, y_mm: float) -> None:
        """Update status bar cursor location text."""
        if self._status_bar is not None:
            self._status_bar.set_cursor_position(x_mm, y_mm)

    def on_wall_preview_length_changed(self, length_mm: float) -> None:
        """Update status bar with wall preview length feedback."""
        if self._status_bar is not None:
            self._status_bar.set_preview_length(length_mm)

    def on_snap_debug_changed(self, enabled: bool, x_mm: float, y_mm: float) -> None:
        """Update status bar with snap debug feedback."""
        if self._status_bar is not None:
            self._status_bar.set_snap_debug(enabled, x_mm, y_mm)

    def handle_properties_changed(
        self,
        project: Project | None,
        scene: DrawingScene,
        target: object,
        values: Mapping[str, float | str | bool],
        default_exterior_wall_thickness: float,
        default_interior_wall_thickness: float,
    ) -> None:
        """Apply edited object properties and orchestrate scene refresh."""
        result = self._service.apply_object_properties(
            target=target,
            values=dict(values),
            default_exterior_wall_thickness=default_exterior_wall_thickness,
            default_interior_wall_thickness=default_interior_wall_thickness,
        )

        if result.requires_recalculation:
            floor = scene.active_floor
            if project is not None and floor is not None:
                self._service.recalculate_floor(floor, project.settings)

        if result.target_kind == "wall":
            scene.on_wall_updated(target)
            return
        if result.target_kind == "window":
            scene.on_window_updated(target)
            return
        if result.target_kind == "door":
            scene.on_door_updated(target)
            return
        if result.target_kind == "opening":
            scene.on_opening_updated(target)
            return
        if result.target_kind == "stair":
            scene.on_stair_updated(target)
            return
        if result.target_kind == "roof_slope":
            scene.on_roof_slope_updated(target)
            return
        if result.target_kind == "dimension":
            scene.on_dimension_updated(target)
            return
        if result.target_kind == "room":
            scene.refresh_rooms()
            scene.refresh_height_zones()
            scene.refresh_dimensions()

        self.properties_refresh_requested.emit()
