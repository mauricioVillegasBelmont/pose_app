# Auditoría técnica — Hallazgos y plan de acción

> **Fecha**: [12-10-2026]
> **Estado**: Post-refactor de render (Fases 1-5 congeladas)
> **Objetivo**: dejar el backend sólido sin tocar lógica de negocio

## Contexto

Tras completar las Fases 1-5 del refactor de render (nueva arquitectura de
capacidades + SceneManager), se hace una auditoría de higiene técnica
antes de reescribir los juegos mockup.

**Prioridad**: aprender + backend sólido.
**NO objetivo**: migrar juegos mockup a la nueva arquitectura (deuda aceptada).

## Hallazgos por severidad

### 🔴 ALTA

1. `GamePlugin` duplicado (domain/plugins + app/plugins) — 30 min
2. `AGENST.md` typo — 2 min
3. `fastapi_adapter.back.py` en el repo — 2 min
4. `tests/manual/test_webcam.py` mal nombrado — 5 min
5. `architecture.md` desactualizado — 15 min

### 🟡 MEDIA

6. `app_runner.py` huérfano — 5 min
7. `domain/use_cases/` vacía — 2 min
8. `state_contract.py` sin efecto — 20 min
9. Falta `[tool.mypy]` + `[tool.ruff]` en pyproject — 30 min
10. `ConsoleFormatter` sin detección TTY — 20 min
11. Falta `docs/render_refactor_status.md` — 30 min

### 🟢 BAJA (deuda aceptada)

12. `PoseOverlayRenderer` + `PoseOverlay` conviven
13. `GameContext` con 4 campos (crecerá)
14. Umbrales de gestos hardcodeados
15. `ParticlesGame` con `_use_new_render` (compat dual)
16. `tests/manual/` sin `__init__.py`
17. `opencode.json` con `rm:*: deny`
18. Verificar que `.env` no está commiteado

### 🔴 Deuda técnica DELIBERADA (no atacar)

- Doble arquitectura de render (legacy + nueva).
- Compat dual en `ParticlesGame`.
- Los 3 juegos mockup usarán la vieja hasta reescribirse.

**Decisión documentada en** `docs/render_refactor_status.md`.

## Plan de ejecución

### Sesión 1: Top 5 (severidad ALTA)

- [ ] Fix 1: Unificar `GamePlugin`
- [ ] Fix 2: `git mv AGENST.md AGENTS.md`
- [ ] Fix 3: `rm adapters/api/fastapi_adapter.back.py`
- [ ] Fix 4: Renombrar `tests/manual/test_webcam.py`
- [ ] Fix 5: Reescribir `architecture.md` (índice)

### Sesión 2: Severidad MEDIA (parte 1)

- [ ] Fix 6: Eliminar `app_runner.py`
- [ ] Fix 7: Eliminar `domain/use_cases/`
- [ ] Fix 8: Mover `state_contract.py` a docs

### Sesión 3: Severidad MEDIA (parte 2) + setup

- [ ] Fix 9: `[tool.mypy]` + `[tool.ruff]` en `pyproject.toml`
- [ ] Fix 10: `ConsoleFormatter` con TTY detection
- [ ] Fix 11: `docs/render_refactor_status.md`
