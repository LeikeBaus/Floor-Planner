from app.actions.action_registry import ActionID


def wire_actions(action_manager, controllers, main_window):

    cc = controllers["command"]
    ec = controllers["export"]
    pc = controllers["project"]
    sc = controllers["settings"]
    snc = controllers["snap"]
    tc = controllers["tool"]

    if main_window is None:
        return
    
    get = action_manager.get_action

    # --- Command wiring -----------------------------------------------------------------
    get(ActionID.UNDO).triggered.connect(lambda _checked=False: cc.handle_undo_action(main_window))
    get(ActionID.REDO).triggered.connect(lambda _checked=False: cc.handle_redo_action(main_window))
    get(ActionID.DELETE).triggered.connect(lambda _checked=False: cc.handle_delete_action(main_window))

    # --- Export wiring ------------------------------------------------------------------
    get(ActionID.EXPORT_PDF).triggered.connect(lambda _checked=False: ec.handle_export_floor_action(main_window, "pdf"))
    get(ActionID.EXPORT_CSV).triggered.connect(lambda _checked=False: ec.handle_export_floor_action(main_window, "csv"))
    get(ActionID.EXPORT_PNG).triggered.connect(lambda _checked=False: ec.handle_export_floor_action(main_window, "png"))
    get(ActionID.EXPORT_SVG).triggered.connect(lambda _checked=False: ec.handle_export_floor_action(main_window, "svg"))
    get(ActionID.EXPORT_XLSX).triggered.connect(lambda _checked=False: ec.handle_export_floor_action(main_window, "xlsx"))
    get(ActionID.EXPORT_TXT).triggered.connect(lambda _checked=False: ec.handle_export_floor_action(main_window, "txt"))
    get(ActionID.EXPORT_AREA_COMPARISON).triggered.connect(lambda _checked=False: ec.handle_export_comparison_action(main_window))
    get(ActionID.CREATE_SNAPSHOT).triggered.connect(lambda _checked=False: ec.handle_create_snapshot_action(main_window))

    # --- Project wiring -----------------------------------------------------------------
    get(ActionID.NEW_PROJECT).triggered.connect(lambda _checked=False: pc.handle_new_project_action())
    get(ActionID.OPEN_PROJECT).triggered.connect(lambda _checked=False: pc.handle_open_project_action())
    get(ActionID.SAVE_PROJECT).triggered.connect(lambda _checked=False: pc.handle_save_project_action())
    get(ActionID.BASEMENT).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action(main_window, "Basement"))
    get(ActionID.GROUND_FLOOR).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action(main_window, "Ground floor"))
    get(ActionID.FIRST_FLOOR).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action(main_window, "First floor"))
    get(ActionID.SECOND_FLOOR).triggered.connect(lambda _checked=False: pc.handle_switch_floor_action(main_window, "Second floor"))

    # --- Settings wiring ----------------------------------------------------------------
    get(ActionID.SETTINGS).triggered.connect(lambda _checked=False: sc.handle_open_settings_action(main_window))
    get(ActionID.TOGGLE_GRID).triggered.connect(lambda enabled=False: sc.handle_toggle_grid_action(main_window, enabled))
    get(ActionID.TOGGLE_SNAP).triggered.connect(lambda enabled=False: sc.handle_toggle_snap_action(main_window, enabled))
    get(ActionID.SHOW_DIMENSIONS).triggered.connect(lambda enabled=False: sc.handle_toggle_dimensions_action(main_window, enabled))
    get(ActionID.SHOW_HEIGHT_ZONES).triggered.connect(lambda enabled=False: sc.handle_toggle_height_zones_action(main_window, enabled))

    # --- Snapshot wiring ----------------------------------------------------------------
    get(ActionID.DEBUG_SNAP_MODE).triggered.connect(lambda enabled=False: snc.handle_toggle_debug_snap_action(main_window, enabled))

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

    

    

    