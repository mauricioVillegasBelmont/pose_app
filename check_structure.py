"""
Script de verificación de estructura.
Ejecuta: python check_structure.py
"""

import sys
from pathlib import Path


REQUIRED_FILES = [
    # Entidades
    "domain/__init__.py",
    "domain/entities/__init__.py",
    "domain/entities/pose_landmark.py",
    "domain/entities/particle.py",
    "domain/entities/color.py",

    # Puertos
    "domain/ports/__init__.py",
    "domain/ports/camera_port.py",
    "domain/ports/pose_estimator_port.py",
    "domain/ports/render_port.py",

    # Casos de uso
    "domain/use_cases/__init__.py",
    "domain/use_cases/color_game.py",
    "domain/use_cases/particles_game.py",

    # Adaptadores mock
    "adapters/mock/__init__.py",
    "adapters/mock/mock_camera.py",
    "adapters/mock/mock_pose.py",
    "adapters/mock/mock_render.py",

    # Adaptadores reales
    "adapters/__init__.py",
    "adapters/camera/__init__.py",
    "adapters/camera/webcam_adapter.py",

    "adapters/pose/__init__.py",
    "adapters/pose/mediapipe_adapter.py",

    "adapters/render/__init__.py",
    "adapters/render/pygame_render_adapter.py",
]


def check_structure():
    """Verifica que todos los archivos requeridos existen."""
    missing = []
    present = []

    for file_path in REQUIRED_FILES:
        path = Path(file_path)
        if path.exists():
            present.append(file_path)
        else:
            missing.append(file_path)

    print("=" * 60)
    print("🔍 VERIFICACIÓN DE ESTRUCTURA DEL PROYECTO")
    print("=" * 60)

    print(f"\n✅ Archivos presentes: {len(present)}/{len(REQUIRED_FILES)}")

    if missing:
        print(f"\n❌ Archivos faltantes ({len(missing)}):")
        for file in missing:
            print(f"   - {file}")
        return False
    else:
        print("\n🎉 ¡Estructura completa! Todos los archivos están presentes.")
        return True


def check_imports():
    """Verifica que los módulos se pueden importar sin errores."""
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DE IMPORTS")
    print("=" * 60)

    modules_to_test = [
        ("domain.entities.pose_landmark", "PoseLandmark"),
        ("domain.entities.particle", "Particle"),
        ("domain.entities.color", "RGBColor"),
        ("domain.ports.camera_port", "CameraPort"),
        ("domain.ports.pose_estimator_port", "PoseEstimatorPort"),
        ("domain.ports.render_port", "RenderPort"),
        ("domain.use_cases.particles_game", "ParticlesGame"),
        ("domain.use_cases.color_game", "ColorGame"),
    ]

    all_ok = True
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name}")
        except ImportError as e:
            print(f"   ❌ {module_name}.{class_name}: {e}")
            all_ok = False
        except AttributeError as e:
            print(f"   ❌ {module_name}.{class_name}: clase no encontrada")
            all_ok = False

    return all_ok


def check_adapters():
    """Verifica que los adaptadores mock funcionan sin dependencias externas."""
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DE ADAPTADORES MOCK")
    print("=" * 60)

    try:
        from adapters.mock.mock_camera import MockCameraAdapter
        from adapters.mock.mock_pose import MockPoseAdapter
        from adapters.mock.mock_render import MockRenderAdapter

        # Instancia cada mock
        camera = MockCameraAdapter()
        pose = MockPoseAdapter()
        render = MockRenderAdapter()

        print("   ✅ MockCameraAdapter")
        print("   ✅ MockPoseAdapter")
        print("   ✅ MockRenderAdapter")

        # Verifica que los mocks implementan los puertos
        from domain.ports.camera_port import CameraPort
        from domain.ports.pose_estimator_port import PoseEstimatorPort
        from domain.ports.render_port import RenderPort

        assert isinstance(camera, CameraPort), "MockCamera no implementa CameraPort"
        assert isinstance(pose, PoseEstimatorPort), "MockPose no implementa PoseEstimatorPort"
        assert isinstance(render, RenderPort), "MockRender no implementa RenderPort"

        print("   ✅ Todos los mocks implementan sus puertos correctamente")
        return True

    except ImportError as e:
        print(f"   ❌ Error de importación: {e}")
        return False
    except AssertionError as e:
        print(f"   ❌ {e}")
        return False


if __name__ == "__main__":
    structure_ok = check_structure()
    print()

    if structure_ok:
        imports_ok = check_imports()
        print()

        if imports_ok:
            adapters_ok = check_adapters()
            print()

            if adapters_ok:
                print("=" * 60)
                print("🎉 ¡Todo listo! Puedes ejecutar las pruebas de integración.")
                print("=" * 60)
                sys.exit(0)

    print("=" * 60)
    print("⚠️ Corrige los errores arriba antes de continuar.")
    print("=" * 60)
    sys.exit(1)