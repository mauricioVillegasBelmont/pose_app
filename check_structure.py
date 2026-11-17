"""
Verificación de estructura y arquitectura.

Corre: python check_structure.py

Verifica:
1. Estructura de carpetas requerida (domain, services, ECS particles,
   adapters, infrastructure, config).
2. Imports de módulos clave (incluye cursor system, services y ECS).
3. Implementación correcta de puertos.
4. Registro de los 3 plugins builtin.
"""

import sys
from pathlib import Path

# ==========================================
# Estructura esperada
# ==========================================

REQUIRED_FILES = [
    # Domain - entities
    "src/pose_app/domain/entities/pose_landmark.py",
    "src/pose_app/domain/entities/particle.py",
    "src/pose_app/domain/entities/color.py",
    "src/pose_app/domain/entities/gesture.py",
    "src/pose_app/domain/entities/input_cursor.py",
    "src/pose_app/domain/entities/hand_landmark_config.py",
    # Domain - entities/particles (ECS)
    "src/pose_app/domain/entities/particles/archetype.py",
    "src/pose_app/domain/entities/particles/components.py",
    "src/pose_app/domain/entities/particles/lifespan.py",
    "src/pose_app/domain/entities/particles/systems.py",
    "src/pose_app/domain/entities/particles/spawn/ports.py",
    "src/pose_app/domain/entities/particles/spawn/positions.py",
    "src/pose_app/domain/entities/particles/spawn/selectors.py",
    "src/pose_app/domain/entities/particles/spawn/strategies.py",
    # Domain - services
    "src/pose_app/domain/services/collision_handler.py",
    "src/pose_app/domain/services/pose_interaction_facade.py",
    # Domain - state / plugins
    "src/pose_app/domain/state/game_state_port.py",
    "src/pose_app/domain/plugins/game_plugin.py",
    # Domain - ports
    "src/pose_app/domain/ports/camera_port.py",
    "src/pose_app/domain/ports/pose_estimator_port.py",
    "src/pose_app/domain/ports/pose_interaction_port.py",
    "src/pose_app/domain/ports/render/color_render_port.py",
    "src/pose_app/domain/ports/render/particles_render_port.py",
    "src/pose_app/domain/ports/render/hud_render_port.py",
    "src/pose_app/domain/ports/render/overlay_port.py",
    "src/pose_app/domain/ports/render/scene_port.py",
    "src/pose_app/domain/ports/render/input_cursor_render_port.py",
    "src/pose_app/domain/ports/render/render_capability.py",
    "src/pose_app/domain/ports/event_bus_port.py",
    # Domain - events
    "src/pose_app/domain/events/base.py",
    "src/pose_app/domain/events/game_events.py",
    "src/pose_app/domain/events/pose_events.py",
    # Games
    "src/pose_app/domain/games/particles/main.py",
    "src/pose_app/domain/games/particles/state.py",
    "src/pose_app/domain/games/color/main.py",
    "src/pose_app/domain/games/color/state.py",
    "src/pose_app/domain/games/gestures/main.py",
    "src/pose_app/domain/games/gestures/state.py",
    # App
    "src/pose_app/app/main.py",
    "src/pose_app/app/game_context.py",
    "src/pose_app/app/plugin_registry.py",
    "src/pose_app/app/state_registry.py",
    "src/pose_app/app/plugins/__init__.py",
    "src/pose_app/app/plugins/particles_plugin.py",
    "src/pose_app/app/plugins/color_plugin.py",
    "src/pose_app/app/plugins/gestures_plugin.py",
    # Adaptadores - camera / pose / mock
    "src/pose_app/adapters/camera/webcam_adapter.py",
    "src/pose_app/adapters/pose/mediapipe_adapter.py",
    "src/pose_app/adapters/mock/mock_camera.py",
    "src/pose_app/adapters/mock/mock_pose.py",
    "src/pose_app/adapters/mock/mock_render.py",
    # Adaptadores - render
    "src/pose_app/adapters/render/pygame_base.py",
    "src/pose_app/adapters/render/pygame_color.py",
    "src/pose_app/adapters/render/pygame_particles.py",
    "src/pose_app/adapters/render/pygame_hud.py",
    "src/pose_app/adapters/render/pygame_scene.py",
    "src/pose_app/adapters/render/pygame_input_cursor.py",
    "src/pose_app/adapters/render/overlays/pose_overlay.py",
    "src/pose_app/adapters/render/overlays/fps_overlay.py",
    # Adaptadores - api
    "src/pose_app/adapters/api/fastapi_adapter.py",
    "src/pose_app/adapters/api/routes.py",
    "src/pose_app/adapters/api/schemas.py",
    # Infraestructura
    "src/pose_app/infrastructure/di/container.py",
    "src/pose_app/infrastructure/events/async_event_bus.py",
    "src/pose_app/infrastructure/logging/logger.py",
    "src/pose_app/infrastructure/errors/exceptions.py",
    "src/pose_app/infrastructure/assets/asset_loader.py",
    "src/pose_app/infrastructure/assets/sprite_sheet_parser.py",
    "src/pose_app/infrastructure/paths.py",
    # Configuración
    "src/pose_app/config/settings.py",
    "src/pose_app/config/game_profile.py",
]


# ==========================================
# Checks
# ==========================================


def check_structure() -> bool:
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE ESTRUCTURA")
    print("=" * 60)

    missing = []
    for file_path in REQUIRED_FILES:
        if not Path(file_path).exists():
            missing.append(file_path)

    total = len(REQUIRED_FILES)
    present = total - len(missing)
    print(f"\n✅ Archivos presentes: {present}/{total}")

    if missing:
        print(f"\n❌ Archivos faltantes ({len(missing)}):")
        for file in missing:
            print(f"   - {file}")
        return False

    print("\n🎉 Estructura completa.")
    return True


def check_imports() -> bool:
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DE IMPORTS")
    print("=" * 60)

    modules = [
        # Domain - entities
        ("pose_app.domain.entities.gesture", "Gesture"),
        ("pose_app.domain.entities.input_cursor", "InputCursor"),
        # Domain - ECS particles
        ("pose_app.domain.entities.particles.lifespan", "LifespanCapability"),
        ("pose_app.domain.entities.particles.systems", "MovementSystem"),
        (
            "pose_app.domain.entities.particles.spawn.strategies",
            "ComposedSpawnStrategy",
        ),
        # Domain - services
        ("pose_app.domain.services.collision_handler", "CentroidCollisionHandler"),
        ("pose_app.domain.services.pose_interaction_facade", "PoseInteractionFacade"),
        # Domain - state / plugins
        ("pose_app.domain.state.game_state_port", "GameStatePort"),
        ("pose_app.domain.plugins.game_plugin", "GamePlugin"),
        # Domain - ports
        ("pose_app.domain.ports.render.render_capability", "RenderCapability"),
        ("pose_app.domain.ports.event_bus_port", "EventBusPort"),
        # Games
        ("pose_app.domain.games.particles.main", "ParticlesGame"),
        ("pose_app.domain.games.color.main", "ColorGame"),
        ("pose_app.domain.games.gestures.main", "GesturesGame"),
        # App
        ("pose_app.app.game_context", "GameContext"),
        ("pose_app.app.plugin_registry", "PluginRegistry"),
        ("pose_app.app.state_registry", "StateRegistry"),
        # Adapters
        (
            "pose_app.adapters.render.pygame_input_cursor",
            "PygameInputCursorRenderer",
        ),
        ("pose_app.adapters.mock.mock_render", "MockParticlesRenderAdapter"),
        ("pose_app.adapters.mock.mock_render", "MockColorRenderAdapter"),
        # Infrastructure
        ("pose_app.infrastructure.events.async_event_bus", "AsyncEventBus"),
        (
            "pose_app.infrastructure.assets.sprite_sheet_parser",
            "SpriteSheetParser",
        ),
        ("pose_app.infrastructure.assets.asset_loader", "AssetLoader"),
        # Config
        ("pose_app.config.game_profile", "GameProfileConfig"),
    ]

    all_ok = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"   ❌ {module_name}.{class_name}: {e}")
            all_ok = False

    return all_ok


def check_plugin_registry() -> bool:
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DE PLUGINS")
    print("=" * 60)

    try:
        from pose_app.app.plugin_registry import PluginRegistry
        from pose_app.app.plugins import register_builtin_plugins

        registry = PluginRegistry()
        register_builtin_plugins(registry)

        expected = {"particles", "color", "gestures"}
        registered = set(registry.list_ids())

        print(f"   Plugins registrados: {sorted(registered)}")
        missing = expected - registered
        if missing:
            print(f"   ❌ Faltan plugins: {sorted(missing)}")
            return False

        print("   ✅ Todos los plugins builtin registrados.")
        return True
    except Exception as e:
        print(f"   ❌ Error verificando plugins: {e}")
        return False


# ==========================================
# Main
# ==========================================

if __name__ == "__main__":
    ok = True
    ok &= check_structure()
    if ok:
        ok &= check_imports()
    if ok:
        ok &= check_plugin_registry()

    print("\n" + "=" * 60)
    if ok:
        print("🎉 ¡Todo en orden!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("⚠️ Corrige los errores arriba.")
        print("=" * 60)
        sys.exit(1)
