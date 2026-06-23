from dataclasses import dataclass
from pathlib import Path

from models.floor import Floor
from models.project import Project


@dataclass
class ProjectState:
    project: Project | None = None
    project_name: str | None = None
    active_floor: Floor | None = None
    project_file_path: Path | None = None

    show_lower_level_overlay: bool = False
    show_upper_level_overlay: bool = False