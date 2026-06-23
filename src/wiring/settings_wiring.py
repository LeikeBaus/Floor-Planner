def wire_settings_signals(pc, settings_controller):
    pc.active_floor_changed.connect(
        settings_controller.on_floor_changed
    )