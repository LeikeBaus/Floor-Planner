"""Service for managing floor design snapshots."""

from __future__ import annotations

from datetime import datetime

from models.floor import Floor
from models.floor_snapshot import FloorSnapshot


class SnapshotManager:
    """Manage creation, storage, and retrieval of floor design snapshots."""

    def __init__(self) -> None:
        """Initialize snapshot manager with empty snapshot list."""
        self._snapshots: list[FloorSnapshot] = []

    def create_snapshot(self, floor: Floor, notes: str = "") -> FloorSnapshot:
        """Create and store a new snapshot of the current floor state."""
        from copy import deepcopy

        floor_copy = deepcopy(floor)
        snapshot = FloorSnapshot(
            floor=floor_copy,
            timestamp=datetime.now().timestamp(),
            notes=notes,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_all_snapshots(self) -> list[FloorSnapshot]:
        """Return all stored snapshots sorted by timestamp (newest first)."""
        return sorted(self._snapshots, key=lambda s: s.timestamp, reverse=True)

    def get_snapshot(self, snapshot_id: str) -> FloorSnapshot | None:
        """Retrieve a specific snapshot by ID."""
        for snapshot in self._snapshots:
            if snapshot.id == snapshot_id:
                return snapshot
        return None

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot by ID. Returns True if found and deleted."""
        for index, snapshot in enumerate(self._snapshots):
            if snapshot.id == snapshot_id:
                del self._snapshots[index]
                return True
        return False

    def update_snapshot_notes(self, snapshot_id: str, notes: str) -> bool:
        """Update revision notes for a snapshot. Returns True if found and updated."""
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is not None:
            snapshot.notes = notes
            return True
        return False

    def clear_all_snapshots(self) -> None:
        """Remove all snapshots."""
        self._snapshots.clear()

    def load_snapshots(self, snapshots_data: list[dict[str, object]]) -> None:
        """Load snapshots from persisted data."""
        self._snapshots = []
        for data in snapshots_data:
            if isinstance(data, dict):
                try:
                    snapshot = FloorSnapshot.from_dict(data)
                    self._snapshots.append(snapshot)
                except Exception:
                    pass

    def save_snapshots(self) -> list[dict[str, object]]:
        """Export all snapshots to persistable format."""
        return [snapshot.to_dict() for snapshot in self._snapshots]
