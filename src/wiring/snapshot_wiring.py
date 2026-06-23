def wire_snapshot_signals(pc, snapshot_panel):
    pc.snapshots_changed.connect(
        snapshot_panel.set_snapshots
    )

    snapshot_panel.snapshot_restore_requested.connect(
        pc.handle_restore_snapshot_action
    )
    snapshot_panel.snapshot_delete_requested.connect(
        pc.handle_delete_snapshot_action
    )