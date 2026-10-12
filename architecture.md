# Arquitectura — Pose AR App

Este documento es un índice. La documentación detallada está en `docs/`.

## Documentos clave

| Documento | Contenido |
|-----------|-----------|
| `docs/system_learning.md` | Guía completa: capas, flujos, catálogo por archivo, patrones. |
| `docs/ports_contract.md` | Contratos de todos los puertos del dominio. |
| `docs/render_architecture.md` | Arquitectura de render (capacidades + SceneManager). |
| `docs/render_refactor_status.md` | Estado del refactor de render (congelado). |
| `docs/adding_a_game_plugin.md` | Tutorial para añadir un juego nuevo. |
| `docs/code_style.md` | Guía de estilos y tipado. |
| `docs/directory_structure.md` | Estructura de carpetas del proyecto. |
| `docs/coverage_baseline.md` | Cobertura baseline. |
| `docs/audit_findings.md` | Hallazgos de la auditoría técnica en curso. |
| `AGENTS.md` | Reglas del proyecto (obligatorias). |

## Resumen arquitectónico

Estilo: Hexagonal (puertos y adaptadores) + sistema de plugins.

Capas (de dentro a fuera):

    domain/           → Entidades, puertos, eventos, estados, juegos.
    infrastructure/   → Servicios transversales (DI, bus, logging, JWT).
    adapters/         → Implementaciones concretas (OpenCV, pygame, FastAPI).
    app/              → Composition root: main, Container, plugins.
    config/           → Settings (pydantic-settings).

Regla de dependencias: `domain/` NO importa de `adapters/` ni de `app/`.

Para detalle completo: `docs/system_learning.md`.
