"""
Verifica umbrales de cobertura por capa.

Uso:
    uv run python scripts/check_coverage.py

Requiere que coverage.xml exista (generado con --cov-report=xml).

Sale con código 0 si todo pasa, 1 si algún umbral no se cumple.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ==========================================
# Configuración de umbrales
# ==========================================

# Mapeo: prefijo de ruta → umbral mínimo (%)
COVERAGE_THRESHOLDS: dict[str, float] = {
    "domain/entities": 90.0,
    "domain/games": 70.0,  # ← 74% real, sobra margen
    "domain/ports": 70.0,  # ← 80% real, sobra margen
    "domain/events": 60.0,  # ← 63% real, poco margen
    "domain/plugins": 70.0,  # ← 88% real, sobra margen
    "domain/state": 90.0,
    "app": 55.0,  # ← 60% real, poco margen
    "adapters/mock": 75.0,  # ← 80% real, sobra margen
    "adapters/render": 40.0,  # ← 42% real, MUY POCO margen
    "adapters/camera": 55.0,  # ← 80% real, sobra margen
    "adapters/pose": 55.0,  # ← 82% real, sobra margen
    "adapters/api": 55.0,  # ← 59% real, MUY POCO margen
    "infrastructure": 45.0,  # ← 50% real, poco margen
    "config": 90.0,  # ← 98% real, sobra margen
}

# Umbral global (aplica a todo el proyecto)
GLOBAL_THRESHOLD = 60.0


# ==========================================
# Parseo del reporte XML
# ==========================================


def parse_coverage_xml(xml_path: Path) -> dict[str, dict[str, float]]:
    """
    Lee coverage.xml y devuelve cobertura por carpeta.

    Returns:
        {
            "domain/entities": {"covered": 100, "total": 110, "rate": 90.9},
            ...
        }
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # coverage.xml agrupa por <package name="...">
    folder_stats: dict[str, dict[str, float]] = {}

    for package in root.findall(".//package"):
        # El name usa puntos: "domain.entities" → "domain/entities"
        pkg_name = package.get("name", "")
        folder = pkg_name.replace(".", "/")

        # Suma líneas cubiertas y totales del package
        total = 0
        covered = 0

        for cls in package.findall(".//class"):
            for line in cls.findall(".//line"):
                total += 1
                if int(line.get("hits", "0")) > 0:
                    covered += 1

        if total > 0:
            folder_stats[folder] = {
                "covered": covered,
                "total": total,
                "rate": (covered / total) * 100,
            }

    return folder_stats


# ==========================================
# Verificación
# ==========================================


def check_thresholds(folder_stats: dict[str, dict[str, float]]) -> int:
    """
    Verifica umbrales por carpeta y global.

    Returns:
        0 si todo pasa, 1 si algo falla.
    """
    failures: list[str] = []
    checks: list[tuple[str, float, float, bool]] = []  # (nombre, actual, umbral, ok)

    # ---------------------------------------------
    # Verificación por carpeta
    # ---------------------------------------------
    print("\n" + "=" * 70)
    print("📊 COBERTURA POR CAPA")
    print("=" * 70)

    for prefix, threshold in COVERAGE_THRESHOLDS.items():
        # Suma todas las subcarpetas que empiezan con el prefijo
        total = 0
        covered = 0

        for folder, stats in folder_stats.items():
            if folder == prefix or folder.startswith(prefix + "/"):
                total += stats["total"]
                covered += stats["covered"]

        if total == 0:
            # Sin archivos en esta capa → skip
            continue

        rate = (covered / total) * 100
        ok = rate >= threshold
        checks.append((prefix, rate, threshold, ok))

        status = "✅" if ok else "❌"
        print(f"  {status} {prefix:30s} " f"{rate:6.2f}% (min {threshold:5.1f}%)")

        if not ok:
            failures.append(f"{prefix}: {rate:.2f}% < {threshold:.1f}%")

    # ---------------------------------------------
    # Verificación global
    # ---------------------------------------------
    total_all = sum(s["total"] for s in folder_stats.values())
    covered_all = sum(s["covered"] for s in folder_stats.values())
    global_rate = (covered_all / total_all * 100) if total_all > 0 else 0
    global_ok = global_rate >= GLOBAL_THRESHOLD

    print("\n" + "=" * 70)
    print("🌍 COBERTURA GLOBAL")
    print("=" * 70)

    status = "✅" if global_ok else "❌"
    print(
        f"  {status} {'GLOBAL':30s} "
        f"{global_rate:6.2f}% (min {GLOBAL_THRESHOLD:5.1f}%)"
    )

    if not global_ok:
        failures.append(f"GLOBAL: {global_rate:.2f}% < {GLOBAL_THRESHOLD:.1f}%")

    # ---------------------------------------------
    # Resumen
    # ---------------------------------------------
    print("\n" + "=" * 70)

    if failures:
        print(f"❌ {len(failures)} capa(s) no alcanzan el umbral:")
        for failure in failures:
            print(f"   - {failure}")
        print("=" * 70)
        return 1

    print("🎉 Todas las capas alcanzan sus umbrales.")
    print("=" * 70)
    return 0


# ==========================================
# Main
# ==========================================


def main() -> int:
    coverage_xml = Path("coverage.xml")

    if not coverage_xml.exists():
        print(
            "❌ No se encontró coverage.xml.\n"
            "   Corre primero: uv run pytest --cov=. --cov-report=xml",
            file=sys.stderr,
        )
        return 1

    folder_stats = parse_coverage_xml(coverage_xml)
    return check_thresholds(folder_stats)


if __name__ == "__main__":
    sys.exit(main())
