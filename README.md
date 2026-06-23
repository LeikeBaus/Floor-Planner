# Project architecture

Floor Planner/
├── src/
│   ├── app/
│   |   ├── actions/
|   |   |   ├── action_manager.py
|   |   |   └── action_registry.py
|   |   ├── application.py
|   |   └── main.py
|   ├── controller/
|   |   ├── command_controller.py
|   |   ├── drawing_controller.py
|   |   ├── export_controller.py
|   |   ├── project_controller.py
|   |   ├── settings_controller.py
|   |   ├── snap_controller.py
|   |   └── tool_controller.py
|   ├── export/
|   |   └── exporter_registry.py
|   ├── geometry/
|   |   ├── area_comparison_engine.py
|   |   ├── bounding_box.py
|   |   ├── dimension_engine.py
|   |   ├── living_area_engine.py
|   |   ├── overlay_engine.py
|   |   ├── point.py
|   |   ├── roof_slope_engine.py
|   |   ├── room_detector.py
|   |   ├── snap_eninge.py
|   |   └── vector.py
|   ├── models/
│   |   ├── state/
|   |   |   └── project_state.py
|   |   ├── building.py
|   |   ├── dimension.py
|   |   ├── door.py
|   |   ├── floor_snapshot.py
|   |   ├── floor.py
|   |   ├── height_zone.py
|   |   ├── opening.py
|   |   ├── overlay.py
|   |   ├── project_settings.py
|   |   ├── project.py
|   |   ├── roof_slope.py
|   |   ├── room.py
|   |   ├── stair.py
|   |   ├── types.py
|   |   ├── wall.py
|   |   └── window.py
|   ├── persistence/
│   |   ├── migration_manager.py
│   |   ├── project_loader.py
│   |   └── project_saver.py
|   ├── services/
│   |   ├── exporters
|   |   |   ├── comparison_pdf_exporter.py
|   |   |   ├── floor_csv_exporter.py
|   |   |   ├── floor_pdf_exporter.py
|   |   |   ├── floor_png_exporter.py
|   |   |   ├── floor_svg_exporter.py
|   |   |   ├── floor_txt_exporter.py
|   |   |   └── floor_xlsx_exporter.py
│   |   ├── autosave_service.py
│   |   ├── command_service.py
│   |   ├── crash_recovery_service.py
│   |   ├── drawing_service.py
│   |   ├── export_service.py
│   |   ├── project_service.py
│   |   ├── settings_service.py
│   |   ├── snap_service.py
│   |   ├── snapshot_manager.py
│   |   ├── wall_rendering_service.py
│   |   └── wall_service
|   ├── views/
│   |   ├── dialogs/
|   |   |   └── settings_dialog.py
│   |   ├── factory/
|   |   |   ├── dock_composer.py
|   |   |   ├── dock_factory.py
|   |   |   ├── main_view_factory.py
|   |   |   └── scene_factory.py
│   |   ├── main_window/
|   |   |   └── main_window.py
│   |   ├── objects/
|   |   |   ├── dimension_graphics_item.py
|   |   |   ├── door_graphics_item.py
|   |   |   ├── height_zone_graphics_item.py
|   |   |   ├── height_zone_legend.py
|   |   |   ├── opening_graphics_item.py
|   |   |   ├── overlay_graphics_item.py
|   |   |   ├── roof_slope_graphics_item.py
|   |   |   ├── room_graphics_item.py
|   |   |   ├── stair_graphics_item.py
|   |   |   ├── wall_graphics_item.py
|   |   |   ├── wall_merged_graphics_item.py
|   |   |   └── window_graphic_items.py
│   |   ├── panels/
|   |   |   ├── floor_summary_panel.py
|   |   |   ├── object_properties_panel.py
|   |   |   ├── project_tree_panel.py
|   |   |   └── snapshot_history_panel.py
│   |   ├── scene/
|   |   |   ├── drawing_scene.py
|   |   |   └── drawing_view.py
│   |   └── widgets/
|   |       ├── menubar.py
|   |       ├── statusbar.py
|   |       └── toolbar.py
|   └── wiring/
│       ├── action_wiring.py
│       ├── drawing_wiring.py
│       ├── project_wiring.py
│       ├── settings_wiring.py
│       ├── snapshot_wiring.py
│       └── tool_wiring.py
├── .gitignore
├── main.py
├── README.MD
└── requirements.py
