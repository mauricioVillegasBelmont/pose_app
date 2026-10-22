# Directory Structure
```
pose_app/
│
├── .github/
│
│   └── workflows/
│
│       ├── ci.yml
│       ├── security.yml
│       └── slow-tests.yml
├── .opencode/
│
│   ├── agents/
│   │
│   │   └── hygiene.md
│   ├── .gitignore
│   ├── package-lock.json
│   └── package.json
├── assets/
│
│   └── particles/
│
│       └── sprites/
│
│           ├── demo.json
│           └── demo.png
├── data/
│
│   └── users.json
├── docs/
│
│   ├── adding_a_game_plugin.md
│   ├── audit_findings.md
│   ├── code_style.md
│   ├── coverage_baseline.md
│   ├── directory_structure.md
│   ├── ports_contract.md
│   ├── render_architecture.md
│   ├── render_refactor_status.md
│   ├── state_contract.md
│   └── system_learning.md
├── logs/
│
│   └── app.log
├── scripts/
│
│   ├── __init__.py
│   ├── check_coverage.py
│   └── coverage_check.sh
├── src/
│
│   └── pose_app/
│
│       ├── adapters/
│       │
│       │   ├── api/
│       │   │
│       │   │   ├── __init__.py
│       │   │   ├── auth_routes.py
│       │   │   ├── dependencies.py
│       │   │   ├── fastapi_adapter.py
│       │   │   ├── routes.py
│       │   │   ├── schemas.py
│       │   │   ├── user_routes.py
│       │   │   └── user_schemas.py
│       │   ├── auth/
│       │   │
│       │   │   ├── credentials_auth_provider.py
│       │   │   ├── in_memory_identity_repository.py
│       │   │   ├── in_memory_user_repository.py
│       │   │   ├── json_bootstrap.py
│       │   │   └── password_hasher.py
│       │   ├── camera/
│       │   │
│       │   │   ├── __init__.py
│       │   │   └── webcam_adapter.py
│       │   ├── mock/
│       │   │
│       │   │   ├── __init__.py
│       │   │   ├── mock_camera.py
│       │   │   ├── mock_pose.py
│       │   │   └── mock_render.py
│       │   ├── pose/
│       │   │
│       │   │   ├── models/
│       │   │   │
│       │   │   │   └── pose_landmarker_full.task
│       │   │   ├── __init__.py
│       │   │   └── mediapipe_adapter.py
│       │   ├── render/
│       │   │
│       │   │   ├── decorators/
│       │   │   │
│       │   │   │   └── pose_debug_overlay.py
│       │   │   ├── overlays/
│       │   │   │
│       │   │   │   ├── __init__.py
│       │   │   │   ├── fps_overlay.py
│       │   │   │   └── pose_overlay.py
│       │   │   ├── __init__.py
│       │   │   ├── pygame_base.py
│       │   │   ├── pygame_color.py
│       │   │   ├── pygame_color_adapter.py
│       │   │   ├── pygame_hud.py
│       │   │   ├── pygame_particles.py
│       │   │   └── pygame_scene.py
│       │   └── __init__.py
│       ├── app/
│       │
│       │   ├── plugins/
│       │   │
│       │   │   ├── __init__.py
│       │   │   ├── color_plugin.py
│       │   │   ├── gestures_plugin.py
│       │   │   └── particles_plugin.py
│       │   ├── __init__.py
│       │   ├── game_context.py
│       │   ├── main.py
│       │   ├── plugin_registry.py
│       │   └── state_registry.py
│       ├── config/
│       │
│       │   ├── __init__.py
│       │   └── settings.py
│       ├── domain/
│       │
│       │   ├── capabilities/
│       │   │
│       │   │   └── particles/
│       │   │
│       │   │       ├── __init__.py
│       │   │       ├── components.py
│       │   │       ├── lifespan.py
│       │   │       └── systems.py
│       │   ├── entities/
│       │   │
│       │   │   ├── __init__.py
│       │   │   ├── color.py
│       │   │   ├── gesture.py
│       │   │   ├── identity.py
│       │   │   ├── particle.py
│       │   │   ├── pose_landmark.py
│       │   │   └── user.py
│       │   ├── events/
│       │   │
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── game_events.py
│       │   │   └── pose_events.py
│       │   ├── games/
│       │   │
│       │   │   ├── color/
│       │   │   │
│       │   │   │   ├── main.py
│       │   │   │   └── state.py
│       │   │   ├── gestures/
│       │   │   │
│       │   │   │   ├── __init__.py
│       │   │   │   ├── main.py
│       │   │   │   └── state.py
│       │   │   └── particles/
│       │   │
│       │   │       ├── __init__.py
│       │   │       ├── geometry.py
│       │   │       ├── main.py
│       │   │       ├── scoring.py
│       │   │       ├── spawn.py
│       │   │       └── state.py
│       │   ├── plugins/
│       │   │
│       │   │   └── game_plugin.py
│       │   ├── ports/
│       │   │
│       │   │   ├── render/
│       │   │   │
│       │   │   │   ├── __init__.py
│       │   │   │   ├── color_render_port.py
│       │   │   │   ├── hud_render_port.py
│       │   │   │   ├── overlay_port.py
│       │   │   │   ├── particles_render_port.py
│       │   │   │   └── scene_port.py
│       │   │   ├── __init__.py
│       │   │   ├── auth_port.py
│       │   │   ├── camera_port.py
│       │   │   ├── event_bus_port.py
│       │   │   ├── identity_repository_port.py
│       │   │   ├── pose_estimator_port.py
│       │   │   ├── render_port.py
│       │   │   └── user_repository_port.py
│       │   ├── state/
│       │   │
│       │   │   ├── game_state_port.py
│       │   │   └── snapshot.py
│       │   └── __init__.py
│       ├── infrastructure/
│       │
│       │   ├── assets/
│       │   │
│       │   │   ├── __init__.py
│       │   │   ├── asset_loader.py
│       │   │   └── sprite_sheet_parser.py
│       │   ├── auth/
│       │   │
│       │   │   └── jwt_service.py
│       │   ├── di/
│       │   │
│       │   │   └── container.py
│       │   ├── errors/
│       │   │
│       │   │   ├── error_handler.py
│       │   │   └── exceptions.py
│       │   ├── events/
│       │   │
│       │   │   └── async_event_bus.py
│       │   ├── logging/
│       │   │
│       │   │   ├── __init__.py
│       │   │   └── logger.py
│       │   ├── __init__.py
│       │   └── paths.py
│       └── __init__.py
├── tests/
│
│   ├── integration/
│   │
│   │   ├── pose/
│   │   │
│   │   │   └── test_mediapipe_adapter.py
│   │   ├── __init__.py
│   │   ├── test_auth_endpoints.py
│   │   ├── test_gestures_plugin_e2e.py
│   │   ├── test_particles_ecs_integration.py
│   │   ├── test_plugin_system_e2e.py
│   │   ├── test_user_endpoints.py
│   │   ├── test_webcam_with_mediapipe.py
│   │   └── test_webcam_with_mock_pose.py
│   ├── manual/
│   │
│   │   └── webcam_manual.py
│   ├── property/
│   │
│   │   ├── __init__.py
│   │   ├── test_identity_properties.py
│   │   ├── test_particle_properties.py
│   │   ├── test_password_hasher_properties.py
│   │   ├── test_plugin_registry_properties.py
│   │   ├── test_pose_landmark_properties.py
│   │   ├── test_rgb_color_properties.py
│   │   └── test_user_properties.py
│   ├── unit/
│   │
│   │   ├── __init__.py
│   │   ├── test_builtin_plugins.py
│   │   ├── test_color_game.py
│   │   ├── test_console_formatter.py
│   │   ├── test_credentials_auth_provider.py
│   │   ├── test_debug_overlay_decorator.py
│   │   ├── test_game_context.py
│   │   ├── test_gestures_detection.py
│   │   ├── test_gestures_state.py
│   │   ├── test_identity_repository.py
│   │   ├── test_jwt_service.py
│   │   ├── test_mediapipe_adapter.py
│   │   ├── test_mirror_mode.py
│   │   ├── test_mock_render.py
│   │   ├── test_particle_ecs_components.py
│   │   ├── test_particle_ecs_systems.py
│   │   ├── test_particles_game.py
│   │   ├── test_particles_geometry.py
│   │   ├── test_particles_geometry_ecs.py
│   │   ├── test_particles_scoring.py
│   │   ├── test_particles_spawn.py
│   │   ├── test_particles_spawn_ecs.py
│   │   ├── test_paths.py
│   │   ├── test_plugin_registry.py
│   │   ├── test_pygame_particles_ecs.py
│   │   ├── test_render_adapters.py
│   │   ├── test_settings.py
│   │   ├── test_sprite_sheet_parser.py
│   │   ├── test_user_repository.py
│   │   └── test_webcam_adapter.py
│   └── __init__.py
├── .coverage
├── .env
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── AGENTS.md
├── README.md
├── architecture.md
├── check_structure.py
├── coverage.xml
├── debug_mediapipe_tasks.py
├── directory_tree_generator.py
├── opencode.json
├── pyproject.toml
├── requirements-dev.txt
├── requirements.txt
└── uv.lock
```
