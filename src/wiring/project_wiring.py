def wire_project_signals(pc, ui):
    pc.project_created.connect(ui.load_new_project)
    pc.project_loaded.connect(ui.load_project)

    pc.window_title_changed.connect(ui.setWindowTitle)