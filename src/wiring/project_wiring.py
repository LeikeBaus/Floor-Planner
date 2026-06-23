def wire_project_signals(pc, ui):
    pc.project_created.connect(ui.on_project_bound)
    pc.project_loaded.connect(ui.on_project_bound)
    pc.active_floor_changed.connect(ui.on_active_floor_changed)
    pc.clear_undo_requested.connect(ui.clear_undo_history)

    pc.window_title_changed.connect(ui.set_window_title)
    pc.project_settings_changed.connect(ui.set_one_level_overlay_enabled)

    summary_panel = ui.get_floor_summary_panel()
    summary_panel.one_level_overlay_toggled.connect(pc.handle_toggle_lower_level_overlay)
    summary_panel.upper_level_overlay_toggled.connect(pc.handle_toggle_upper_level_overlay)