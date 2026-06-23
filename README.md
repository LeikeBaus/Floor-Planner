# Floor Planner

## 1. Project Purpose
Floor Planner is a desktop CAD-like floor planning application for quickly modeling residential layouts and deriving useful outputs from them. It focuses on practical planning workflows:

- draw and edit walls, openings, windows, doors, stairs, and roof slopes
- compute room, floor, and living areas
- manage multiple levels in one project
- export floor data and reports to several file formats

## 2. Key Features
- Multi-floor project model (Basement, Ground floor, First floor, Second floor)
- Wall-based room detection and automatic area calculation
- Height-zone and living-area calculations for sloped roofs
- Manual and auto-generated dimensions
- Undo/redo via command pattern (QUndoStack)
- Overlay reference of adjacent levels (lower and upper, one level each)
- Project snapshots, autosave, and crash-recovery support
- Exports: PDF, CSV, PNG, SVG, XLSX, TXT, and area-comparison PDF

## 3. Architecture
The codebase follows a layered MVC + Service architecture:

- Models: domain entities and state containers in src/models
- Views: Qt widgets/graphics scene items in src/views
- Controllers: UI orchestration and flow coordination in src/controllers
- Services: business/domain logic in src/services
- Wiring: explicit signal/slot composition in src/wiring
- App bootstrap: dependency graph assembly in src/app/application.py

### 3.1 Startup Flow
1. main.py starts the Qt application.
2. src/app/main.py creates Application.
3. Application builds actions, services, controllers, and MainWindow.
4. Wiring modules connect actions, controller signals, and view updates.
5. MainWindow initializes the scene/view and dock panels.
6. Default project interactions become available (new/open/save, tools, drawing).

### 3.2 Wiring
Wiring modules keep dependencies explicit and avoid hidden cross-layer coupling:

- src/wiring/action_wiring.py: QAction -> controller/view entry points
- src/wiring/project_wiring.py: project lifecycle + summary-panel overlay toggles
- src/wiring/drawing_wiring.py: drawing-view status feedback to UI
- src/wiring/snapshot_wiring.py: snapshot panel events to project controller
- src/wiring/tool_wiring.py: default tool setup and project lifecycle tool reset

### 3.3 Factories
Factories isolate UI composition details and keep MainWindow focused:

- src/views/factory/scene_factory.py creates the drawing scene
- src/views/factory/main_view_factory.py creates menu/toolbar/statusbar/view
- src/views/factory/dock_factory.py creates panel widgets
- src/views/factory/dock_composer.py places dock widgets in the main window

## 4. Development Setup
### Python Version
- Python 3.10+ required

### Install
```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run
```bash
python main.py
```

### Validate
```bash
py -3 -m compileall src main.py
```

### Dependencies
See requirements.txt. Core runtime dependencies include:
- PyQt6
- Shapely
- numpy
- openpyxl
- reportlab

## 5. Known Design Decisions and Trade-offs
- Qt signal/slot orchestration over global event bus:
	- Pro: explicit wiring, easier tracing
	- Con: more boilerplate wiring code
- Service layer for domain logic:
	- Pro: testable and UI-independent business operations
	- Con: additional indirection between UI and model updates
- Recalculation-driven derived state (rooms/zones/dimensions) after geometry changes:
	- Pro: consistent outputs
	- Con: can cost more CPU on very large plans
- Overlay references are limited to one adjacent floor above and below:
	- Pro: simpler UX and predictable context
	- Con: no direct multi-level stack visualization

## 6. Future Improvements
- Add unit/integration tests around room split/merge metadata retention
- Improve room label placement with polygon-inside best-point heuristics
- Add optional overlay styling controls per source level
- Add project-level performance profiling for large floor plans
- Introduce richer plugin/export extension hooks

## 7. License
No license file is currently included in this repository.

