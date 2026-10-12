"""
Verificación de estructura y arquitectura.

Corre: python check_structure.py

Verifica:
1. Estructura de carpetas requerida.
2. Imports de módulos clave.
3. Implementación correcta de puertos.
"""

import sys
from pathlib import Path

# ==========================================
# Estructura esperada
# ==========================================

REQUIRED_FILES = [
    # Domain
    "domain/entities/pose_landmark.py",
    "domain/entities/particle.py",
    "domain/entities/color.py",
    "domain/entities/gesture.py",
    "domain/state/game_state_port.py",
    "domain/plugins/game_plugin.py",
    "domain/ports/camera_port.py",
    "domain/ports/pose_estimator_port.py",
    "domain/ports/render_port.py",
    "domain/ports/render/color_render_port.py",
    "domain/ports/render/particles_render_port.py",
    "domain/ports/render/hud_render_port.py",
    "domain/ports/render/overlay_port.py",
    "domain/ports/render/scene_port.py",
    "domain/ports/event_bus_port.py",
    "domain/events/base.py",
    "domain/events/game_events.py",
    "domain/events/pose_events.py",
    # Games
    "domain/games/particles/main.py",
    "domain/games/particles/state.py",
    "domain/games/color/main.py",
    "domain/games/color/state.py",
    "domain/games/gestures/main.py",
    "domain/games/gestures/state.py",
    # App
    "app/main.py",
    "app/game_context.py",
    "app/plugin_registry.py",
    "app/state_registry.py",
    "app/plugins/__init__.py",
    "app/plugins/particles.py",
    "app/plugins/color_plugin.py",
    "app/plugins/gestures_plugin.py",
    # Adaptadores
    "adapters/camera/webcam_adapter.py",
    "adapters/pose/mediapipe_adapter.py",
    "adapters/render/pygame_particles_adapter.py",
    "adapters/render/pygame_color_adapter.py",
    "adapters/render/pygame_base.py",
    "adapters/render/pygame_color.py",
    "adapters/render/pygame_particles.py",
    "adapters/render/pygame_hud.py",
    "adapters/render/pygame_scene.py",
    "adapters/render/overlays/pose_overlay.py",
    "adapters/render/overlays/fps_overlay.py",
    "adapters/render/decorators/pose_debug_overlay.py",
    "adapters/mock/mock_camera.py",
    "adapters/mock/mock_pose.py",
    "adapters/mock/mock_render.py",
    "adapters/api/fastapi_adapter.py",
    "adapters/api/routes.py",
    "adapters/api/schemas.py",
    # Infraestructura
    "infrastructure/di/container.py",
    "infrastructure/events/async_event_bus.py",
    "infrastructure/logging/logger.py",
    "infrastructure/errors/exceptions.py",
    # Configuración
    "config/settings.py",
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
        ("domain.entities.gesture", "Gesture"),
        ("domain.state.game_state_port", "GameStatePort"),
        ("domain.plugins.game_plugin", "GamePlugin"),
        ("domain.ports.render_port", "ParticlesRenderPort"),
        ("domain.ports.event_bus_port", "EventBusPort"),
        ("domain.games.particles.main", "ParticlesGame"),
        ("domain.games.color.main", "ColorGame"),
        ("domain.games.gestures.main", "GesturesGame"),
        ("app.game_context", "GameContext"),
        ("app.plugin_registry", "PluginRegistry"),
        ("app.state_registry", "StateRegistry"),
        ("adapters.render.pygame_particles_adapter", "PygameParticlesAdapter"),
        ("adapters.render.pygame_color_adapter", "PygameColorAdapter"),
        ("adapters.render.decorators.pose_debug_overlay", "PoseDebugOverlay"),
        ("adapters.mock.mock_render", "MockParticlesRenderAdapter"),
        ("adapters.mock.mock_render", "MockColorRenderAdapter"),
        ("infrastructure.events.async_event_bus", "AsyncEventBus"),
    ]

    all_ok = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name}")
        except (ImportError, AttributeError) as e:
            print(f"   ❌ {module_name}.{class_name}: {e}")
            all_ok = False

    return all_ok


def check_plugin_registry() -> bool:
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DE PLUGINS")
    print("=" * 60)

    try:
        from app.plugin_registry import PluginRegistry
        from app.plugins import register_builtin_plugins

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
