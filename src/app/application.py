"""Application factory and lifecycle helpers."""

from __future__ import annotations

import sys

from app.actions.action_manager import ActionManager
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
from views.factory.dock_factory import DockFactory
from views.factory.main_view_factory import MainViewFactory
from views.factory.scene_factory import SceneFactory
from views.main_window.main_window import MainWindow
from wiring.action_wiring import wire_actions
from wiring.drawing_wiring import wire_drawing_signals
from wiring.project_wiring import wire_project_signals
from wiring.settings_wiring import wire_settings_signals
from wiring.snapshot_wiring import wire_snapshot_signals
from wiring.tool_wiring import wire_tool_signals

from PyQt6.QtWidgets import QApplication, QMessageBox


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
        self._build_services()
        self._build_controllers()
        self._main_window = MainWindow(self._action_manager)
        print("UI built.")
        self._wire_all()
        print("Signals wired.")
        self._process_crash_recovery()
        self._main_window.show()
        return self._qt_app.exec()
    
    def _build_services(self) -> None:
        self._action_manager = ActionManager()
        self._project_state = ProjectState()

        self._autosave_service = AutosaveService(self._project_saver)
        self._command_service = CommandService()
        self._drawing_service = DrawingService()
        self._export_service = ExportService()
        self._project_service = ProjectService()
        self._settings_service = SettingsService()
        self._snapshot_manager = SnapshotManager()

    def _build_controllers(self) -> None:
        self._command_controller = CommandController(self._command_service)
        self._drawing_controller = DrawingController(self._drawing_service)
        self._export_controller = ExportController(self._export_service)
        self._project_controller = ProjectController(
            self._autosave_service,
            self._command_service,
            self._drawing_service,
            self._project_service,
            self._project_state,
            self._snapshot_manager,
        )
        self._settings_controller = SettingsController(self._settings_service)
        self._snap_controller = SnapController()
        self._tool_controller = ToolController()

        self._controllers = {
            "command": self._command_controller,
            "drawing": self._drawing_controller,
            "export": self._export_controller,
            "project": self._project_controller,
            "settings": self._settings_controller,
            "snap": self._snap_controller,
            "tool": self._tool_controller,
        }

    def _wire_all(self) -> None:
        wire_actions(self._action_manager, self._controllers, self._main_window)

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
