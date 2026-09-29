
# Directory Structure
````
pose_app/
│
├── adapters/
│   ├── api/   ├── __init__.py
│   │   ├── fastapi_adapter.py
│   │   ├── routes.back.py
│   │   ├── routes.py
│   │   └── schemas.py
│   │
│   ├── camera/
│   │   ├── __init__.py
│   │   └── webcam_adapter.py
│   │
│   ├── mock/
│   │   ├── __init__.py
│   │   ├── mock_camera.py
│   │   ├── mock_pose.py
│   │   └── mock_render.py
│   │
│   ├── pose/
│   │   ├── models/
│   │   │   └── pose_landmarker_full.task
│   │   ├── __init__.py
│   │   └── mediapipe_adapter.py
│   │
│   ├── render/
│   │   ├── decorators/
│   │   │   └── pose_debug_overlay.py
│   │   ├── overlays/
│   │   │   ├── __init__.py
│   │   │   └── pose_overlay.py
│   │   ├── __init__.py
│   │   ├── pygame_base.py
│   │   ├── pygame_color_adapter.py
│   │   └── pygame_particles_adapter.py
│   │
│   └── __init__.py
│
├── app/
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── color_plugin.py
│   │   ├── game_plugin.py
│   │   └── particles_plugin.py
│   ├── __init__.py
│   ├── game_context.py
│   ├── main.py
│   ├── plugin_registry.py
│   ├── state_contract.py
│   └── state_registry.py
│
├── config/
│   └── settings.py
│
├── docs/
│   └── ports_contract.md
│
├── domain/
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── color.py
│   │   ├── particle.py
│   │   └── pose_landmark.py
│   ├── events/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── game_events.py
│   │   └── pose_events.py
│   ├── games/
│   │   ├── color/
│   │   │   └── state.py
│   │   └── particles/
│   │       └── state.py
│   ├── plugins/
│   │   └── game_plugin.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── camera_port.py
│   │   ├── event_bus_port.py
│   │   ├── pose_estimator_port.py
│   │   └── render_port.py
│   ├── state/
│   │   ├── game_state_port.py
│   │   └── snapshot.py
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── color_game.py
│   │   └── particles_game.py
│   └── __init__.py
│
├── infrastructure/
│   ├── di/
│   │   └── container.py
│   │
│   ├── errors/
│   │   ├── error_handler.py
│   │   └── exceptions.py
│   │
│   ├── events/
│   │   └── async_event_bus.py
│   │
│   ├── lifecycle/
│   │   └── app_runner.py
│   │
│   ├── logging/
│   │   └── logger.py
│   │
│   ├── mediapipe/
│   └── pygame/
│
├── logs/
│   └── app.log
│
├── tests/
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   ├── test_full_integration.py
│   │   ├── test_plugin_system_e2e.py
│   │   ├── test_webcam_with_mediapipe.py
│   │   └── test_webcam_with_mock_pose.py
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_builtin_plugins.py
│   │   ├── test_color_game.py
│   │   ├── test_debug_overlay_decorator.py
│   │   ├── test_game_context.py
│   │   ├── test_mediapipe_adapter.py
│   │   ├── test_mock_render.py
│   │   ├── test_particles_game.py
│   │   ├── test_particles_game_integration.py
│   │   ├── test_plugin_registry.py
│   │   ├── test_pose_debug_overlay_with_mocks.py
│   │   ├── test_pygame_render_adapter.py
│   │   ├── test_render_adapters.py
│   │   └── test_state_generic.py
│   │
│   └── __init__.py
│
├── .env
├── .env.example
├── .gitignore
├── .python-version
├── README.md
├── architecture.md
├── check_structure.py
├── directory_tree_generator.py
├── main_particles.py
├── requirements.txt
├── test_minimal.py
├── test_settings.py
└── test_webcam.py
```