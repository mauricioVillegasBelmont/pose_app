# Documentación — Pose AR App

Índice de la documentación del proyecto, organizada por tipo.

## 📖 Guías

Para desarrolladores nuevos o para aprender a extender el sistema.

- [system_learning.md](./guides/system_learning.md) — Guía de aprendizaje completa del sistema (arquitectura, módulos, patrones).
- [adding_a_game_plugin.md](./guides/adding_a_game_plugin.md) — Tutorial paso a paso para añadir un juego nuevo.

## 🏛️ Arquitectura

Diseño de subsistemas específicos. Estables (fases cerradas).

- [render_architecture.md](./architecture/render_architecture.md) — Arquitectura de render (SceneManager + capacidades + overlays).
- [particles_ecs_system.md](./architecture/particles_ecs_system.md) — Sistema ECS-lite de partículas (componentes, sistemas, spawn).
- [cursor_system.md](./architecture/cursor_system.md) — Sistema de cursores de interacción (multi-cursor, EMA, timeout).
- [spawn_system.md](./architecture/spawn_system.md) — Sistema de spawn data-driven (archetypes, selectors, positioners).

## 📜 Contratos y convenciones

Fuente de verdad. Cambian con cada puerto o setting nuevo.

- [ports_contract.md](./contracts/ports_contract.md) — Contratos de puertos (ABC, Protocol, firmas, changelog).
- [state_contract.md](./contracts/state_contract.md) — Contratos de estado (qué publica cada juego a la API).
- [code_style.md](./contracts/code_style.md) — Guía de estilo, tipado y convenciones.

## 🔄 Refactors

Documentación histórica de refactors cerrados.

- [render_refactor_status.md](./refactors/render_refactor_status.md) — Estado del refactor de render (histórico, migración completa).

## 🔍 Auditorías y cobertura

- [audit_findings.md](./audits/audit_findings.md) — Hallazgos pendientes de auditoría.
- [coverage_baseline.md](./audits/coverage_baseline.md) — Baseline de cobertura por capa.

## 📚 Referencia

Auto-generado. No editar a mano.

- [directory_structure.md](./reference/directory_structure.md) — Árbol actual del proyecto (regenerado con `scripts/directory_tree_generator.py`).
