def wire_tool_signals(drawing_scene, tool_controller):
    drawing_scene.tool_changed.connect(
        tool_controller.on_tool_changed
    )