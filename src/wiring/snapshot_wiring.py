def wire_snapshot_signals(pc, snapshot_panel):
    pc.snapshots_changed.connect(
        snapshot_panel.set_snapshots
    )