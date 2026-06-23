"""Controller orchestrating project workflows."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from models.floor_snapshot import FloorSnapshot
from models.state.project_state import ProjectState
from services.autosave_service import AutosaveService
from services.command_service import CommandService
from services.drawing_service import DrawingService
from services.project_service import ProjectService
from services.snapshot_manager import SnapshotManager

class ProjectController(QObject):
    """Coordinates project lifecycle operations for UI callers."""

    # --- Project lifecycle --------------------------------------------------------------
    project_created = pyqtSignal(object, object)   # project, active_floor
    project_loaded = pyqtSignal(object, object)
    window_title_changed = pyqtSignal(str)
    clear_undo_requested = pyqtSignal()

    # --- Floor / Drawing state ----------------------------------------------------------
    active_floor_changed = pyqtSignal(object, list)  # floor, all_floors
    floor_toolbar_sync = pyqtSignal(str)

    # --- Snapshots ----------------------------------------------------------------------
    snapshots_changed = pyqtSignal(list)

    # --- Settings -----------------------------------------------------------------------
    project_settings_changed = pyqtSignal(bool, bool)

    # --- Initialization -----------------------------------------------------------------

    def __init__(
        self,
        autosave_service: AutosaveService,
        command_service: CommandService,
        drawing_service: DrawingService,
        project_service: ProjectService,
        project_state: ProjectState,
        snapshot_manager: SnapshotManager,
    ) -> None:
        super().__init__()
        
        self._autosave_service = autosave_service
        self._command_service = command_service
        self._drawing_service = drawing_service
        self._project_service = project_service
        self._project_state = project_state
        self._snapshot_manager = snapshot_manager

    
    # --- Action handlers ----------------------------------------------------------------

    def handle_new_project_action(self) -> None:
        self._project_state.project, self._project_state.active_floor = (
            self._project_service.create_default_project()
        )

        if self._project_state.project is not None:
            ground_floor = self._project_service.find_floor(
                self._project_state.project,
                "Ground floor",
            )
            if ground_floor is not None:
                self._project_state.active_floor = ground_floor

        self._project_state.project_file_path = None

        self._snapshot_manager.clear_all_snapshots()
        self.clear_undo_requested.emit()

        self._configure_autosave()

        self._bind_active_floor()

        self.project_created.emit(
            self._project_state.project,
            self._project_state.active_floor,
        )

        self.window_title_changed.emit(
            "FloorPlanner - Untitled Project"
        )
        self.project_settings_changed.emit(
            self._project_state.show_lower_level_overlay,
            self._project_state.show_upper_level_overlay,
        )

    def handle_open_project_action(
        self,
        file_path: str | Path,
    ) -> None:
        self._project_state.project = self._project_service.load_project(file_path)

        self._project_state.active_floor = self._project_service.find_first_floor(
            self._project_state.project
        )

        if self._project_state.project is not None:
            ground_floor = self._project_service.find_floor(
                self._project_state.project,
                "Ground floor",
            )
            if ground_floor is not None:
                self._project_state.active_floor = ground_floor

        if self._project_state.active_floor is None:
            return

        self.clear_undo_requested.emit()

        self._project_state.project_file_path = Path(file_path)

        if self._project_state.project.snapshots:
            snapshots_data = [snapshot.to_dict() for snapshot in self._project_state.project.snapshots]
            self._snapshot_manager.load_snapshots(snapshots_data)
        else:
            self._snapshot_manager.clear_all_snapshots()

        self._bind_active_floor()

        self.project_loaded.emit(
            self._project_state.project,
            self._project_state.active_floor,
        )

        self.window_title_changed.emit(
            f"FloorPlanner - {self._project_state.project.name}"
        )
        self.refresh_snapshot_list()
        self.project_settings_changed.emit(
            self._project_state.show_lower_level_overlay,
            self._project_state.show_upper_level_overlay,
        )

    def handle_save_project_action(self) -> None:
        if (
            self._project_state.project is None
            or self._project_state.project_file_path is None
        ):
            return

        self._project_service.save_project(
            self._project_state.project,
            self._project_state.project_file_path,
        )

    def handle_save_project_as_action(self, file_path: str | Path) -> None:
        """Save project to a selected path and update project title context."""
        if self._project_state.project is None:
            return
        self._project_state.project_file_path = Path(file_path)
        self._project_service.save_project(
            self._project_state.project,
            self._project_state.project_file_path,
        )
        self.window_title_changed.emit(
            f"FloorPlanner - {self._project_state.project.name}"
        )

    def needs_save_path(self) -> bool:
        """Return True if save action currently needs a file-path selection first."""
        return self._project_state.project_file_path is None

    def handle_switch_floor_action(
        self,
        floor_name: str,
    ) -> None:
        if self._project_state.project is None:
            return

        floor = self._project_service.find_floor(
            self._project_state.project,
            floor_name,
        )

        if floor is None:
            return

        self._project_state.active_floor = floor

        self._bind_active_floor()

    def _bind_active_floor(self) -> None:
        if (
            self._project_state.project is None
            or self._project_state.active_floor is None
        ):
            return

        floors = self._project_service.all_floors(
            self._project_state.project
        )

        self._project_service.configure_overlay(
            self._project_state.active_floor,
            floors,
            self._project_state.show_lower_level_overlay,
            self._project_state.show_upper_level_overlay,
        )

        self._drawing_service.recalculate_floor(
            self._project_state.active_floor,
            self._project_state.project.settings,
        )

        self.active_floor_changed.emit(
            self._project_state.active_floor,
            floors,
        )

    def _configure_autosave(self) -> None:
        if self._project_state.project is None:
            return

        self._autosave_service.set_project(
            self._project_state.project,
            self._project_state.project_file_path,
        )

        self._autosave_service.start(
            self._project_state.project.settings.autosave_interval,
        )

    def refresh_snapshot_list(self) -> None:
        snapshots_data = self._snapshot_manager.save_snapshots()

        if self._project_state.project is not None:
            self._project_state.project.snapshots = [
                FloorSnapshot.from_dict(item)
                for item in snapshots_data
            ]

        self.snapshots_changed.emit(
            self._snapshot_manager.get_all_snapshots()
        )

    def handle_create_snapshot_action(self, notes: str = "") -> None:
        """Create snapshot for active floor and publish updated snapshot list."""
        if self._project_state.active_floor is None:
            return
        self._snapshot_manager.create_snapshot(self._project_state.active_floor, notes)
        self.refresh_snapshot_list()

    def handle_delete_snapshot_action(self, snapshot_id: str) -> None:
        """Delete one snapshot by id and publish updated snapshot list."""
        self._snapshot_manager.delete_snapshot(snapshot_id)
        self.refresh_snapshot_list()

    def handle_restore_snapshot_action(self, snapshot: FloorSnapshot) -> None:
        """Restore active floor content from snapshot and refresh all floor-dependent views."""
        if self._project_state.project is None:
            return

        restored_floor = deepcopy(snapshot.floor)
        floors = self._project_service.all_floors(self._project_state.project)
        replaced = False
        for floor in floors:
            if floor.id == restored_floor.id or floor.name == restored_floor.name:
                floor.walls = restored_floor.walls
                floor.rooms = restored_floor.rooms
                floor.height_zones = restored_floor.height_zones
                floor.dimensions = restored_floor.dimensions
                floor.windows = restored_floor.windows
                floor.doors = restored_floor.doors
                floor.openings = restored_floor.openings
                floor.stairs = restored_floor.stairs
                floor.roof_slopes = restored_floor.roof_slopes
                floor.overlays = restored_floor.overlays
                floor.floor_area_total = restored_floor.floor_area_total
                floor.living_area_total = restored_floor.living_area_total
                self._project_state.active_floor = floor
                replaced = True
                break

        if not replaced and floors:
            self._project_state.active_floor = floors[0]

        self._bind_active_floor()

    def handle_toggle_lower_level_overlay(self, enabled: bool) -> None:
        """Toggle lower-level overlay state and refresh active floor presentation."""
        self._project_state.show_lower_level_overlay = enabled
        self.project_settings_changed.emit(
            self._project_state.show_lower_level_overlay,
            self._project_state.show_upper_level_overlay,
        )
        self._bind_active_floor()

    def handle_toggle_upper_level_overlay(self, enabled: bool) -> None:
        """Toggle upper-level overlay state and refresh active floor presentation."""
        self._project_state.show_upper_level_overlay = enabled
        self.project_settings_changed.emit(
            self._project_state.show_lower_level_overlay,
            self._project_state.show_upper_level_overlay,
        )
        self._bind_active_floor()