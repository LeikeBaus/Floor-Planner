def wire_drawing_signals(pc, drawing_scene, drawing_controller):
    pc.active_floor_changed.connect(
        drawing_scene.set_active_floor
    )

    pc.active_floor_changed.connect(
        drawing_controller.on_floor_changed
    )