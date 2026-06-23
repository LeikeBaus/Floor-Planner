"""Project tree panel showing placed objects on the active floor."""

from __future__ import annotations

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from models.floor import Floor
from models.project import Project


class ProjectTreePanel(QWidget):
    """Read-only tree view for project hierarchy and floor objects."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tree = QTreeWidget(self)
        self._tree.setHeaderLabels(["Object", "Details"])
        self._tree.setColumnCount(2)
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(True)

        from PyQt6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)
        self.setLayout(layout)

    def set_project(self, project: Project, active_floor: Floor | None) -> None:
        """Refresh tree contents from current project and active floor models."""
        self._tree.clear()

        project_item = QTreeWidgetItem(["Project", project.name])
        self._tree.addTopLevelItem(project_item)

        floors_root = QTreeWidgetItem(["Buildings", str(len(project.buildings))])
        project_item.addChild(floors_root)

        for building in project.buildings:
            building_item = QTreeWidgetItem(["Building", building.name])
            floors_root.addChild(building_item)
            for floor in building.floors:
                details = f"{floor.name} ({len(floor.walls)} walls)"
                floor_item = QTreeWidgetItem(["Floor", details])
                building_item.addChild(floor_item)

        if active_floor is not None:
            placed_root = QTreeWidgetItem(["Active Floor Objects", active_floor.name])
            project_item.addChild(placed_root)

            self._add_collection(
                parent=placed_root,
                title="Walls",
                items=[
                    (wall.id, f"{wall.wall_type} | {wall.length / 1000.0:.2f} m")
                    for wall in active_floor.walls
                ],
            )
            self._add_collection(
                parent=placed_root,
                title="Rooms",
                items=[
                    (room.id, f"{room.name} | {room.floor_area / 1_000_000.0:.2f} m2")
                    for room in active_floor.rooms
                ],
            )
            self._add_collection(
                parent=placed_root,
                title="Dimensions",
                items=[
                    (dimension.id, f"{dimension.value / 1000.0:.2f} m")
                    for dimension in active_floor.dimensions
                ],
            )
            self._add_collection(
                parent=placed_root,
                title="Windows",
                items=[
                    (window.id, f"wall={window.wall_id[:8]} width={window.width:.0f} mm")
                    for window in active_floor.windows
                ],
            )
            self._add_collection(
                parent=placed_root,
                title="Doors",
                items=[
                    (door.id, f"wall={door.wall_id[:8]} width={door.width:.0f} mm")
                    for door in active_floor.doors
                ],
            )
            self._add_collection(
                parent=placed_root,
                title="Openings",
                items=[
                    (
                        opening.id,
                        f"wall={opening.wall_id[:8]} width={opening.width:.0f} mm",
                    )
                    for opening in active_floor.openings
                ],
            )
            self._add_collection(
                parent=placed_root,
                title="Stairs",
                items=[
                    (
                        stair.id,
                        (
                            f"{stair.width:.0f}x{stair.depth:.0f} mm "
                            f"@ ({stair.position_x:.0f}, {stair.position_y:.0f})"
                        ),
                    )
                    for stair in active_floor.stairs
                ],
            )
            self._add_collection(
                parent=placed_root,
                title="Roof Slopes",
                items=[
                    (slope.id, f"{slope.height_start:.0f} -> {slope.height_end:.0f} mm")
                    for slope in active_floor.roof_slopes
                ],
            )

        self._tree.expandToDepth(2)

    def _add_collection(
        self,
        parent: QTreeWidgetItem,
        title: str,
        items: list[tuple[str, str]],
    ) -> None:
        node = QTreeWidgetItem([title, str(len(items))])
        parent.addChild(node)

        for item_id, details in items:
            node.addChild(QTreeWidgetItem([item_id[:8], details]))
