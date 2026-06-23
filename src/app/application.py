"""Application factory and lifecycle helpers."""

from __future__ import annotations

import sys

from app.actions.action_registry import ActionID
from app.actions.action_manager import ActionManager
from controllers.command_controller import CommandController
from controllers.drawing_controller import DrawingController
from controllers.export_controller import ExportController
from controllers.project_controller import ProjectController
from controllers.settings_controller import SettingsController
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
from wiring.action_wiring import wire_actions
from wiring.drawing_wiring import wire_drawing_signals
from wiring.project_wiring import wire_project_signals
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
        self._project_state = ProjectState()
        self._project_loader = ProjectLoader()
        self._project_saver = ProjectSaver()
        
        self._build_services()
        self._main_window = MainWindow(self._action_manager)
        self._build_controllers()
        self._wire_all()
        self._process_crash_recovery()

        self._main_window.show()
        return self._qt_app.exec()
    
    def _build_services(self) -> None:
        self._action_manager = ActionManager()
        

        self._autosave_service = AutosaveService(self._project_saver)
        self._command_service = CommandService()
        self._drawing_service = DrawingService()
        self._export_service = ExportService()
        self._project_service = ProjectService(
            loader=self._project_loader,
            saver=self._project_saver,
        )
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
        self._tool_controller = ToolController()

        self._controllers = {
            "command": self._command_controller,
            "drawing": self._drawing_controller,
            "export": self._export_controller,
            "project": self._project_controller,
            "settings": self._settings_controller,
            "tool": self._tool_controller,
        }

    def _wire_all(self) -> None:
        main_window = self._main_window
        if main_window is None:
            return

        drawing_scene = main_window.get_scene()
        drawing_view = main_window.get_view()
        snapshot_panel = main_window.get_snapshot_history_panel()
        properties_panel = main_window.get_properties_panel()

        tool_actions = {
            "select": self._action_manager.get_action(ActionID.SELECT),
            "wall_exterior": self._action_manager.get_action(ActionID.WALL),
            "wall_interior": self._action_manager.get_action(ActionID.INTERIOR_WALL),
            "dimension": self._action_manager.get_action(ActionID.DIMENSION),
            "window": self._action_manager.get_action(ActionID.WINDOW),
            "door": self._action_manager.get_action(ActionID.DOOR),
            "opening": self._action_manager.get_action(ActionID.OPENING),
            "stair": self._action_manager.get_action(ActionID.STAIR),
            "roof_slope": self._action_manager.get_action(ActionID.ROOF_SLOPE),
        }
        self._tool_controller.configure(
            drawing_view=drawing_view,
            tool_actions=tool_actions,
            status_bar=main_window.statusBar(),
        )
        self._drawing_controller.configure_status_bar(main_window.statusBar())

        wire_actions(
            self._action_manager,
            self._controllers,
            main_window,
            self._project_state,
        )
        wire_project_signals(self._project_controller, main_window)
        wire_drawing_signals(
            self._project_controller,
            drawing_scene,
            drawing_view,
            self._drawing_controller,
        )
        wire_snapshot_signals(self._project_controller, snapshot_panel)
        wire_tool_signals(self._project_controller, self._tool_controller)

        def _refresh_properties_panel() -> None:
            properties_panel.set_selection(drawing_scene)

        drawing_scene.selectionChanged.connect(_refresh_properties_panel)
        self._project_controller.active_floor_changed.connect(
            lambda _floor, _floors: _refresh_properties_panel()
        )
        self._drawing_controller.properties_refresh_requested.connect(_refresh_properties_panel)
        properties_panel.property_change_requested.connect(
            lambda target, values, default_exterior, default_interior: self._drawing_controller.handle_properties_changed(
                project=self._project_state.project,
                scene=drawing_scene,
                target=target,
                values=values,
                default_exterior_wall_thickness=default_exterior,
                default_interior_wall_thickness=default_interior,
            )
        )

        def _sync_floor_after_command_index_change(_index: int) -> None:
            project = self._project_state.project
            floor = drawing_scene.active_floor
            if project is None or floor is None:
                return
            self._drawing_controller.recalculate_floor(project, floor)
            main_window.refresh_active_floor_view()

        main_window.get_undo_stack().indexChanged.connect(_sync_floor_after_command_index_change)

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
