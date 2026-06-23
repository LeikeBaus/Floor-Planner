from dataclasses import dataclass

from views.panels.project_tree_panel import ProjectTreePanel
from views.panels.snapshot_history_panel import SnapshotHistoryPanel
from views.panels.object_properties_panel import ObjectPropertiesPanel
from views.panels.floor_summary_panel import FloorSummaryPanel


@dataclass(frozen=True)
class DockWidgets:
    project_tree: ProjectTreePanel
    snapshot_history: SnapshotHistoryPanel
    properties: ObjectPropertiesPanel
    floor_summary: FloorSummaryPanel


class DockFactory:
    """Creates widgets"""

    @staticmethod
    def create_widgets() -> DockWidgets:
        return DockWidgets(
            project_tree=ProjectTreePanel(),
            snapshot_history=SnapshotHistoryPanel(),
            properties=ObjectPropertiesPanel(),
            floor_summary=FloorSummaryPanel(),
        )