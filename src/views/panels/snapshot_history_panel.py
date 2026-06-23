"""Snapshot history panel for viewing and managing design versions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QListView,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from models.floor_snapshot import FloorSnapshot


class SnapshotListModel(QStandardItemModel):
    """Model for displaying snapshots in a list view."""

    def __init__(self) -> None:
        super().__init__()
        self._snapshots: list[FloorSnapshot] = []

    def set_snapshots(self, snapshots: list[FloorSnapshot]) -> None:
        """Update snapshot list."""
        self.clear()
        self._snapshots = snapshots
        for snapshot in snapshots:
            notes_text = f" — {snapshot.notes}" if snapshot.notes else ""
            display_text = f"{snapshot.display_timestamp}{notes_text}"
            item = QStandardItem(display_text)
            self.appendRow(item)

    def get_snapshot_at(self, row: int) -> FloorSnapshot | None:
        """Get snapshot at row index."""
        if 0 <= row < len(self._snapshots):
            return self._snapshots[row]
        return None


class SnapshotHistoryPanel(QWidget):
    """Panel for viewing, managing, and restoring floor design snapshots."""

    snapshot_selected = pyqtSignal(object)
    snapshot_restore_requested = pyqtSignal(object)
    snapshot_delete_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._snapshot_model = SnapshotListModel()
        self._snapshot_list = QListView(self)
        self._snapshot_list.setModel(self._snapshot_model)
        selection_model = self._snapshot_list.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_snapshot_selected)

        self._notes_edit = QTextEdit(self)
        self._notes_edit.setPlaceholderText("Select a snapshot to view notes")
        self._notes_edit.setReadOnly(True)
        self._notes_edit.setMaximumHeight(80)

        self._restore_button = QPushButton("Restore Snapshot", self)
        self._restore_button.clicked.connect(self._on_restore_clicked)
        self._restore_button.setEnabled(False)

        self._delete_button = QPushButton("Delete Snapshot", self)
        self._delete_button.clicked.connect(self._on_delete_clicked)
        self._delete_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self._snapshot_list)
        layout.addWidget(self._notes_edit)
        layout.addWidget(self._restore_button)
        layout.addWidget(self._delete_button)
        self.setLayout(layout)

        self._current_snapshot: FloorSnapshot | None = None

    def set_snapshots(self, snapshots: list[FloorSnapshot]) -> None:
        """Update snapshot list display."""
        self._snapshot_model.set_snapshots(snapshots)
        self._current_snapshot = None
        self._notes_edit.clear()
        self._restore_button.setEnabled(False)
        self._delete_button.setEnabled(False)

    def _on_snapshot_selected(self, selected: object, deselected: object) -> None:
        """Handle snapshot selection in list."""
        indexes = self._snapshot_list.selectedIndexes()
        if not indexes:
            self._current_snapshot = None
            self._notes_edit.clear()
            self._restore_button.setEnabled(False)
            self._delete_button.setEnabled(False)
            return

        row = indexes[0].row()
        snapshot = self._snapshot_model.get_snapshot_at(row)
        if snapshot is not None:
            self._current_snapshot = snapshot
            self._notes_edit.setText(snapshot.notes)
            self._restore_button.setEnabled(True)
            self._delete_button.setEnabled(True)
            self.snapshot_selected.emit(snapshot)

    def _on_restore_clicked(self) -> None:
        """Emit restore request for selected snapshot."""
        if self._current_snapshot is not None:
            self.snapshot_restore_requested.emit(self._current_snapshot)

    def _on_delete_clicked(self) -> None:
        """Emit delete request for selected snapshot."""
        if self._current_snapshot is not None and hasattr(self._current_snapshot, "id"):
            self.snapshot_delete_requested.emit(self._current_snapshot.id)
            self._current_snapshot = None
