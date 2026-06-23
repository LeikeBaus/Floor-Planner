from app.actions.action_registry import ActionID
from PyQt6.QtWidgets import QMessageBox
from services.file_dialog_service import FileDialogService
from views.dialogs.settings_dialog import SettingsDialog


def wire_actions(action_manager, controllers, main_window, project_state):

    ec = controllers["export"]
    dc = controllers["drawing"]
    pc = controllers["project"]
    sc = controllers["settings"]
    tc = controllers["tool"]

    if main_window is None:
        return
    
    get = action_manager.get_action
    file_dialog_service = FileDialogService(main_window)

    def _save_current_project() -> bool:
        if pc.needs_save_path():
            path = file_dialog_service.pick_save_project_path()
            if path is None:
                return False
            pc.handle_save_project_as_action(path)
        else:
            pc.handle_save_project_action()
        main_window.mark_project_clean()
        return True

    def _confirm_discard_or_save_changes(action_description: str) -> bool:
        if project_state.project is None or not main_window.has_unsaved_changes():
            return True

        choice = QMessageBox.question(
            main_window,
            "Unsaved Changes",
            (
                f"You have unsaved changes.\n"
                f"Do you want to save before you {action_description}?"
            ),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if choice == QMessageBox.StandardButton.Save:
            return _save_current_project()
        if choice == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _handle_export_floor(export_format: str) -> None:
        floor = project_state.active_floor
        if floor is None:
            return
        path = file_dialog_service.pick_export_path(
            title=f"Export Floor as {export_format.upper()}",
            extension=export_format,
        )
        if path is None:
            return
        ec.export_floor(floor, export_format, path)

    def _open_settings_dialog() -> None:
        project = project_state.project
        floor = project_state.active_floor
        if project is None or floor is None:
            return

        dialog = SettingsDialog(project.settings, main_window)
        if not dialog.exec():
            return

        updated = dialog.build_settings(project.settings)
        project.settings = updated
        main_window.apply_project_settings(updated)
        dc.recalculate_floor(project, floor)
        main_window.refresh_active_floor_view()
        main_window.mark_project_dirty()

    def _handle_new_project_action() -> None:
        if not _confirm_discard_or_save_changes("create a new project"):
            return
        pc.handle_new_project_action()
        main_window.mark_project_clean()

    def _handle_open_project_action() -> None:
        if not _confirm_discard_or_save_changes("open another project"):
            return
        path = file_dialog_service.pick_open_project_path()
        if path is None:
            return
        pc.handle_open_project_action(path)
        main_window.mark_project_clean()

    def _handle_close_request() -> bool:
        return _confirm_discard_or_save_changes("close the project")

    main_window.set_close_request_handler(_handle_close_request)

    # --- Command wiring -----------------------------------------------------------------
    get(ActionID.UNDO).triggered.connect(lambda _checked=False: main_window.perform_undo())
    get(ActionID.REDO).triggered.connect(lambda _checked=False: main_window.perform_redo())
    get(ActionID.DELETE).triggered.connect(lambda _checked=False: main_window.perform_delete_selection())

    # --- Export wiring ------------------------------------------------------------------
    get(ActionID.EXPORT_PDF).triggered.connect(lambda _checked=False: _handle_export_floor("pdf"))
    get(ActionID.EXPORT_CSV).triggered.connect(lambda _checked=False: _handle_export_floor("csv"))
    get(ActionID.EXPORT_PNG).triggered.connect(lambda _checked=False: _handle_export_floor("png"))
    get(ActionID.EXPORT_SVG).triggered.connect(lambda _checked=False: _handle_export_floor("svg"))
    get(ActionID.EXPORT_XLSX).triggered.connect(lambda _checked=False: _handle_export_floor("xlsx"))
    get(ActionID.EXPORT_TXT).triggered.connect(lambda _checked=False: _handle_export_floor("txt"))
    get(ActionID.EXPORT_AREA_COMPARISON).triggered.connect(
        lambda _checked=False: (
            ec.export_comparison_report(project_state.active_floor, path)
            if (project_state.active_floor is not None)
            and (path := file_dialog_service.pick_export_path("Export Area Comparison", "pdf")) is not None
            else None
        )
    )
    get(ActionID.CREATE_SNAPSHOT).triggered.connect(lambda _checked=False: pc.handle_create_snapshot_action())

    # --- Project wiring -----------------------------------------------------------------
    get(ActionID.NEW_PROJECT).triggered.connect(lambda _checked=False: _handle_new_project_action())
    get(ActionID.OPEN_PROJECT).triggered.connect(lambda _checked=False: _handle_open_project_action())
    get(ActionID.SAVE_PROJECT).triggered.connect(lambda _checked=False: _save_current_project())
    get(ActionID.BASEMENT).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action("Basement"))
    get(ActionID.GROUND_FLOOR).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action("Ground floor"))
    get(ActionID.FIRST_FLOOR).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action("First floor"))
    get(ActionID.SECOND_FLOOR).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action("Second floor"))

    # --- Settings wiring ----------------------------------------------------------------
    get(ActionID.SETTINGS).triggered.connect(lambda _checked=False: _open_settings_dialog())
    get(ActionID.TOGGLE_GRID).triggered.connect(
        lambda enabled=False: (
            sc.toggle_grid(project_state.project, enabled)
            if project_state.project is not None
            else None,
            main_window.set_grid_enabled(enabled),
        )
    )
    get(ActionID.TOGGLE_SNAP).triggered.connect(
        lambda enabled=False: (
            sc.toggle_snap(project_state.project, enabled)
            if project_state.project is not None
            else None,
            main_window.set_snap_enabled(
                enabled,
                project_state.project.settings.snap_distance if project_state.project is not None else 200.0,
            ),
        )
    )
    get(ActionID.SHOW_DIMENSIONS).triggered.connect(
        lambda enabled=False: (
            sc.toggle_dimensions(project_state.project, enabled)
            if project_state.project is not None
            else None,
            main_window.set_dimensions_visible(enabled),
        )
    )
    get(ActionID.SHOW_HEIGHT_ZONES).triggered.connect(
        lambda enabled=False: main_window.set_height_zones_visible(enabled)
    )

    # --- Snapshot wiring ----------------------------------------------------------------
    get(ActionID.DEBUG_SNAP_MODE).triggered.connect(lambda enabled=False: main_window.set_debug_snap_enabled(enabled))

    # --- View panel wiring ---------------------------------------------------------------
    get(ActionID.SHOW_PROJECT_PANEL).triggered.connect(
        lambda enabled=False: main_window.set_panel_visibility("project", enabled)
    )
    get(ActionID.SHOW_SNAPSHOT_PANEL).triggered.connect(
        lambda enabled=False: main_window.set_panel_visibility("snapshot", enabled)
    )
    get(ActionID.SHOW_PROPERTIES_PANEL).triggered.connect(
        lambda enabled=False: main_window.set_panel_visibility("properties", enabled)
    )
    get(ActionID.SHOW_SUMMARY_PANEL).triggered.connect(
        lambda enabled=False: main_window.set_panel_visibility("summary", enabled)
    )

    # --- Tool wiring --------------------------------------------------------------------
    get(ActionID.SELECT).triggered.connect(lambda _checked=False: tc.handle_tool_action("select"))
    get(ActionID.WALL).triggered.connect(lambda _checked=False: tc.handle_tool_action("wall_exterior"))
    get(ActionID.INTERIOR_WALL).triggered.connect(lambda _checked=False: tc.handle_tool_action("wall_interior"))
    get(ActionID.DIMENSION).triggered.connect(lambda _checked=False: tc.handle_tool_action("dimension"))
    get(ActionID.WINDOW).triggered.connect(lambda _checked=False: tc.handle_tool_action("window"))
    get(ActionID.DOOR).triggered.connect(lambda _checked=False: tc.handle_tool_action("door"))
    get(ActionID.OPENING).triggered.connect(lambda _checked=False: tc.handle_tool_action("opening"))
    get(ActionID.STAIR).triggered.connect(lambda _checked=False: tc.handle_tool_action("stair"))
    get(ActionID.ROOF_SLOPE).triggered.connect(lambda _checked=False: tc.handle_tool_action("roof_slope"))

    

    

    