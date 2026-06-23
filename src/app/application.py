"""Application factory and lifecycle helpers."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from app.actions.action_manager import ActionManager
from app.actions.action_registry import ActionID
from controllers.command_controller import CommandController
from controllers.drawing_controller import DrawingController
from controllers.export_controller import ExportController
from controllers.project_controller import ProjectController
from controllers.settings_controller import SettingsController
from controllers.snap_controller import SnapController
from controllers.tool_controller import ToolController
from models.state.project_state import ProjectState
from persistence.project_loader import ProjectLoader
from persistence.project_saver import ProjectSaver
from services.autosave_service import AutosaveService
from services.drawing_service import DrawingService
from services.export_service import ExportService
from services.command_service import CommandService
from services.crash_recovery_service import CrashRecoveryService
from services.project_service import ProjectService
from services.settings_service import SettingsService
from services.snapshot_manager import SnapshotManager
from views.main_window.main_window import MainWindow


class FloorPlannerApplication:
    """Coordinates application startup and top-level window creation."""

    def __init__(self) -> None:
        self._qt_app: QApplication | None = None
        self._main_window: MainWindow | None = None
        self._project_loader: ProjectLoader | None = None
        self._project_saver: ProjectSaver | None = None

    def run(self) -> int:
        """Start Qt event loop and return process exit code."""
        self._qt_app = QApplication(sys.argv)
        self._project_state = ProjectState()

        # Services
        self.autosave_service = AutosaveService(self._project_saver)
        self.command_service = CommandService()
        self.drawing_service = DrawingService()
        self.export_service = ExportService()
        self.project_service = ProjectService(
            loader=self._project_loader,
            saver=self._project_saver
            )
        self.settings_service = SettingsService()
        self.snapshot_manager = SnapshotManager()

        # Controllers
        self.action_manager = ActionManager()
        self.command_controller = CommandController()
        self.drawing_controller = DrawingController(self.drawing_service)
        self.export_controller = ExportController(self.export_service)
        self.project_controller = ProjectController(
            autosave_service=self.autosave_service,
            command_service=self.command_service,
            drawing_service=self.drawing_service,
            project_service=self.project_service,
            project_state=self._project_state,
            snapshot_manager=self.snapshot_manager,
        )
        self.settings_controller = SettingsController(self.settings_service)
        self.snap_controller = SnapController()
        self.tool_controller = ToolController()

        # Main window
        self._main_window = MainWindow(self.action_manager)
        self._connect_actions() # Connect User Actions to Controller Methods
        self._connect_signals() # Connect Controller Signals to View Slots
        self._process_crash_recovery()
        self._main_window.show()
        return self._qt_app.exec()
    
    def _connect_actions(self) -> None:
        """Connect actions to their respective controller methods."""
        main_window = self._main_window
        if main_window is None:
            return

        get_action = self.action_manager.get_action

        get_action(ActionID.NEW_PROJECT).triggered.connect(
            lambda _checked=False: self.project_controller.handle_new_project_action()
        )
        get_action(ActionID.OPEN_PROJECT).triggered.connect(
            lambda _checked=False: self.project_controller.handle_open_project_action()
        )
        get_action(ActionID.SAVE_PROJECT).triggered.connect(
            lambda _checked=False: self.project_controller.handle_save_project_action()
        )

        get_action(ActionID.EXPORT_PDF).triggered.connect(
            lambda _checked=False: self.export_controller.handle_export_floor_action(
                main_window, "pdf"
            )
        )
        get_action(ActionID.EXPORT_CSV).triggered.connect(
            lambda _checked=False: self.export_controller.handle_export_floor_action(
                main_window, "csv"
            )
        )
        get_action(ActionID.EXPORT_PNG).triggered.connect(
            lambda _checked=False: self.export_controller.handle_export_floor_action(
                main_window, "png"
            )
        )
        get_action(ActionID.EXPORT_SVG).triggered.connect(
            lambda _checked=False: self.export_controller.handle_export_floor_action(
                main_window, "svg"
            )
        )
        get_action(ActionID.EXPORT_XLSX).triggered.connect(
            lambda _checked=False: self.export_controller.handle_export_floor_action(
                main_window, "xlsx"
            )
        )
        get_action(ActionID.EXPORT_TXT).triggered.connect(
            lambda _checked=False: self.export_controller.handle_export_floor_action(
                main_window, "txt"
            )
        )
        get_action(ActionID.EXPORT_AREA_COMPARISON).triggered.connect(
            lambda _checked=False: self.export_controller.handle_export_comparison_action(
                main_window
            )
        )
        get_action(ActionID.CREATE_SNAPSHOT).triggered.connect(
            lambda _checked=False: self.export_controller.handle_create_snapshot_action(main_window)
        )

        get_action(ActionID.UNDO).triggered.connect(
            lambda _checked=False: self.command_controller.handle_undo_action(main_window)
        )
        get_action(ActionID.REDO).triggered.connect(
            lambda _checked=False: self.command_controller.handle_redo_action(main_window)
        )
        get_action(ActionID.DELETE).triggered.connect(
            lambda _checked=False: self.command_controller.handle_delete_action(main_window)
        )

        get_action(ActionID.SETTINGS).triggered.connect(
            lambda _checked=False: self.settings_controller.handle_open_settings_action(main_window)
        )
        get_action(ActionID.TOGGLE_GRID).triggered.connect(
            lambda enabled=False: self.settings_controller.handle_toggle_grid_action(
                main_window, enabled
            )
        )
        get_action(ActionID.TOGGLE_SNAP).triggered.connect(
            lambda enabled=False: self.settings_controller.handle_toggle_snap_action(
                main_window, enabled
            )
        )
        get_action(ActionID.DEBUG_SNAP_MODE).triggered.connect(
            lambda enabled=False: self.snap_controller.handle_toggle_debug_snap_action(
                main_window, enabled
            )
        )
        get_action(ActionID.SHOW_DIMENSIONS).triggered.connect(
            lambda enabled=False: self.settings_controller.handle_toggle_dimensions_action(
                main_window, enabled
            )
        )
        get_action(ActionID.SHOW_HEIGHT_ZONES).triggered.connect(
            lambda enabled=False: self.settings_controller.handle_toggle_height_zones_action(
                main_window, enabled
            )
        )

        get_action(ActionID.SELECT).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("select")
        )
        get_action(ActionID.WALL).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("wall_exterior")
        )
        get_action(ActionID.INTERIOR_WALL).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("wall_interior")
        )
        get_action(ActionID.DIMENSION).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("dimension")
        )
        get_action(ActionID.WINDOW).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("window")
        )
        get_action(ActionID.DOOR).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("door")
        )
        get_action(ActionID.OPENING).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("opening")
        )
        get_action(ActionID.STAIR).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("stair")
        )
        get_action(ActionID.ROOF_SLOPE).triggered.connect(
            lambda _checked=False: self.tool_controller.handle_tool_action("roof_slope")
        )

        get_action(ActionID.BASEMENT).triggered.connect(
            lambda _checked=False: self.project_controller.handle_switch_floor_action(
                main_window, "Basement"
            )
        )
        get_action(ActionID.GROUND_FLOOR).triggered.connect(
            lambda _checked=False: self.project_controller.handle_switch_floor_action(
                main_window, "Ground floor"
            )
        )
        get_action(ActionID.FIRST_FLOOR).triggered.connect(
            lambda _checked=False: self.project_controller.handle_switch_floor_action(
                main_window, "First floor"
            )
        )
        get_action(ActionID.SECOND_FLOOR).triggered.connect(
            lambda _checked=False: self.project_controller.handle_switch_floor_action(
                main_window, "Second floor"
            )
        )
    
    def _connect_signals(self) -> None:
        """Connect controller signals to UI components."""
        win = self._main_window
        pc = self.project_controller
        if win is None:
            return

        # --- Project lifecycle signals ------------------------------------------------------
        pc.project_created.connect(win.load_new_project)
        pc.project_loaded.connect(win.load_project)
        pc.window_title_changed.connect(
            win.setWindowTitle
        )

    def _process_crash_recovery(self) -> None:
        """Detect and optionally restore autosaved recovery files on startup."""
        main_window = self._main_window
        if main_window is None:
            return

        recovery_service = CrashRecoveryService(ProjectLoader())
        recovery_files = recovery_service.list_recovery_files()
        if not recovery_files:
            return

        for recovery_path in recovery_files:
            choice = QMessageBox.question(
                main_window,
                "Crash Recovery",
                "A recovery file was found:\n"
                f"{recovery_path.name}\n\n"
                "Yes: Restore this recovery file\n"
                "No: Discard this recovery file\n"
                "Cancel: Decide later",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )

            if choice == QMessageBox.StandardButton.Yes:
                try:
                    project = recovery_service.load_recovery_project(recovery_path)
                except Exception as error:
                    QMessageBox.critical(
                        main_window,
                        "Recovery Failed",
                        f"Could not load recovery file {recovery_path.name}:\n{error}",
                    )
                    continue

                main_window.load_recovered_project(project)
                recovery_service.discard_recovery_file(recovery_path)
                break

            if choice == QMessageBox.StandardButton.No:
                recovery_service.discard_recovery_file(recovery_path)
                continue

            break
