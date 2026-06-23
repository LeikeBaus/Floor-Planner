from enum import Enum

class ActionID(Enum):
    """Enum for action identifiers."""
    NEW_PROJECT = "new_project"
    OPEN_PROJECT = "open_project"
    SAVE_PROJECT = "save_project"

    # Export actions
    EXPORT_PDF = "export_pdf"
    EXPORT_CSV = "export_csv"
    EXPORT_PNG = "export_png"
    EXPORT_SVG = "export_svg"
    EXPORT_XLSX = "export_xlsx"
    EXPORT_TXT = "export_txt"
    EXPORT_AREA_COMPARISON = "export_area_comparison"

    # Actions for undo/redo
    DELETE = "delete"
    UNDO = "undo"
    REDO = "redo"

    # Snapshot action
    CREATE_SNAPSHOT = "create_snapshot"
    
    # Settings action
    SETTINGS = "settings"

    # Grid actions
    TOGGLE_GRID = "toggle_grid"
    TOGGLE_SNAP = "toggle_snap"
    DEBUG_SNAP_MODE = "debug_snap_mode"
    SHOW_DIMENSIONS = "show_dimensions"
    SHOW_HEIGHT_ZONES = "show_height_zones"

    # View actions
    SHOW_PROJECT_PANEL = "show_project_panel"
    SHOW_SNAPSHOT_PANEL = "show_snapshot_panel"
    SHOW_PROPERTIES_PANEL = "show_properties_panel"
    SHOW_SUMMARY_PANEL = "show_summary_panel"

    # Actions for placing objects
    SELECT = "select"
    WALL = "wall"
    INTERIOR_WALL = "interior_wall"
    DIMENSION = "dimension"
    WINDOW = "window"
    DOOR = "door"
    OPENING = "opening"
    STAIR = "stair"
    ROOF_SLOPE = "roof_slope"

    # Floor actions
    BASEMENT = "basement"
    GROUND_FLOOR = "ground_floor"
    FIRST_FLOOR = "first_floor"
    SECOND_FLOOR = "second_floor"