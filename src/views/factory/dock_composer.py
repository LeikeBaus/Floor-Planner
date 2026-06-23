from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QDockWidget

from views.factory.dock_factory import DockWidgets


class DockComposer:
    """Responsible for placing dock widgets into MainWindow."""

    def __init__(self, main_window: QMainWindow):
        self._mw = main_window

    def compose(self, widgets: DockWidgets) -> dict[str, QDockWidget]:
        # Project Tree
        project_dock = QDockWidget("Project", self._mw)
        project_dock.setWidget(widgets.project_tree)
        self._mw.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, project_dock)

        # Snapshot History
        snapshot_dock = QDockWidget("Snapshots", self._mw)
        snapshot_dock.setWidget(widgets.snapshot_history)
        self._mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, snapshot_dock)

        # Properties
        properties_dock = QDockWidget("Properties", self._mw)
        properties_dock.setWidget(widgets.properties)
        self._mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, properties_dock)

        # Summary
        summary_dock = QDockWidget("Summary", self._mw)
        summary_dock.setWidget(widgets.floor_summary)
        self._mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, summary_dock)

        # Layout grouping
        self._mw.splitDockWidget(snapshot_dock, properties_dock, Qt.Orientation.Vertical)
        self._mw.splitDockWidget(properties_dock, summary_dock, Qt.Orientation.Vertical)

        return {
            "project": project_dock,
            "snapshot": snapshot_dock,
            "properties": properties_dock,
            "summary": summary_dock,
        }