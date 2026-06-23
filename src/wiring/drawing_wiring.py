def wire_drawing_signals(pc, drawing_scene, drawing_view, drawing_controller):
    pc.active_floor_changed.connect(
        drawing_scene.set_active_floor
    )

    drawing_view.cursor_world_changed.connect(
        drawing_controller.on_cursor_world_changed
    )
    drawing_view.wall_preview_length_changed.connect(
        drawing_controller.on_wall_preview_length_changed
    )
    drawing_view.snap_debug_changed.connect(
        drawing_controller.on_snap_debug_changed
    )