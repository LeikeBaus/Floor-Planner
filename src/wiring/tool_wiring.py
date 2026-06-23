def wire_tool_signals(pc, tool_controller):
    tool_controller.activate_tool("select")
    pc.project_created.connect(lambda _project, _floor: tool_controller.activate_tool("select"))
    pc.project_loaded.connect(lambda _project, _floor: tool_controller.activate_tool("select"))