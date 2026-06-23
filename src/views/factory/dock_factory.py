"""dock_factory.py"""
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from views.panels.project_tree_panel import ProjectTreePanel
from views.panels.snapshot_history_panel import SnapshotHistoryPanel
from views.panels.object_properties_panel import ObjectPropertiesPanel
from views.panels.floor_summary_panel import FloorSummaryPanel


@dataclass
class DockBundle:
    project_tree: ProjectTreePanel
    snapshot_history: SnapshotHistoryPanel
    properties: ObjectPropertiesPanel
    floor_summary: FloorSummaryPanel


class DockFactory:
    """Creates and groups all dock widgets."""

    @staticmethod
    def create_all(main_window, snapshot_manager=None) -> DockBundle:

        # --- Project Tree ---
        project_dock = QDockWidget("Project", main_window)
        project_tree = ProjectTreePanel()
        project_dock.setWidget(project_tree)

        main_window.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            project_dock,
        )

        # --- Snapshot History ---
        snapshot_dock = QDockWidget("Snapshots", main_window)
        snapshot_history = SnapshotHistoryPanel()
        snapshot_dock.setWidget(snapshot_history)

        main_window.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            snapshot_dock,
        )

        # --- Properties ---
        properties_dock = QDockWidget("Properties", main_window)
        properties = ObjectPropertiesPanel()
        properties_dock.setWidget(properties)

        main_window.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            properties_dock,
        )

        # --- Floor Summary ---
        summary_dock = QDockWidget("Summary", main_window)
        floor_summary = FloorSummaryPanel()
        summary_dock.setWidget(floor_summary)

        main_window.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            summary_dock,
        )

        # optional layout grouping
        main_window.splitDockWidget(snapshot_dock, properties_dock, Qt.Orientation.Vertical)
        main_window.splitDockWidget(properties_dock, summary_dock, Qt.Orientation.Vertical)

        return DockBundle(
            project_tree=project_tree,
            snapshot_history=snapshot_history,
            properties=properties,
            floor_summary=floor_summary,
        )