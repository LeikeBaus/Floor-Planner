"""Controller orchestrating project workflows."""

from __future__ import annotations

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

    # --- Floor / Drawing state ----------------------------------------------------------
    active_floor_changed = pyqtSignal(object, list)  # floor, all_floors
    floor_toolbar_sync = pyqtSignal(str)

    # --- Snapshots ----------------------------------------------------------------------
    snapshots_changed = pyqtSignal(list)

    # --- Settings -----------------------------------------------------------------------
    project_settings_changed = pyqtSignal(object)

    # --- Autosave -----------------------------------------------------------------------
    window_title_changed = pyqtSignal(str)

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

        self._show_lower_level_overlay: bool = False
    
    # --- Action handlers ----------------------------------------------------------------

    def handle_new_project_action(self) -> None:
        self._project_state.project, self._project_state.active_floor = (
            self._project_service.create_default_project()
        )

        self._project_state.project_file_path = None

        self._snapshot_manager.clear_all_snapshots()
        #self._command_service.clear()

        self._configure_autosave()

        self.project_created.emit(
            self._project_state.project,
            self._project_state.active_floor,
        )

        self.window_title_changed.emit(
            "FloorPlanner - Untitled Project"
        )

    def handle_open_project_action(
        self,
        file_path: str | Path,
    ) -> None:
        self._project_state.project = self._project_service.load_project(file_path)

        self._project_state.active_floor = self._project_service.find_first_floor(
            self._project_state.project
        )

        if self._project_state.active_floor is None:
            return

        self._project_state.project_file_path = Path(file_path)

        self._bind_active_floor()

        self.project_loaded.emit(
            self._project_state.project,
            self._project_state.active_floor,
        )

        self.window_title_changed.emit(
            f"FloorPlanner - {self._project_state.project.name}"
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