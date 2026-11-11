# Estado del refactor de render

> **Estado**: Congelado (histórico) → ✅ migración completa en `feature/refactor/render-migrate-legacy`
> **Fecha de congelación**: 2026-10-12
> **Rama original**: `refactor/render-capacities` (mergeada a main)

## Fases completadas

- ✅ **Fase 1**: Puertos nuevos (`ColorRenderPort`, `ParticlesRenderPort`, `HudRenderPort`, `OverlayPort`).
- ✅ **Fase 2**: `ScenePort`.
- ✅ **Fase 3**: Adaptadores Pygame nuevos (`PygameColorRenderer`, `PygameParticlesRenderer`, `PygameHudRenderer`, `PygameSceneManager`).
- ✅ **Fase 4**: Overlays (`PoseOverlay`, `FpsOverlay`).
- ✅ **Fase 5**: Migración de `ParticlesGame` (con compat dual).

## Fases canceladas (completadas después)

- ✅ **Fase 6**: Migrar `ColorGame` y `GesturesGame` → `feature/refactor/render-migrate-legacy`.
- ✅ **Fase 7**: Actualizar mocks y tests → `feature/refactor/render-migrate-legacy`.
- ✅ **Fase 8**: Limpieza/deprecación → `feature/refactor/render-migrate-legacy`.

## Razón de la congelación

Los juegos actuales (ParticlesGame, ColorGame, GesturesGame) son mockups
y van a ser reescritos con lógica de negocio real. Completar el refactor
con compat dual generaría ~560 LOC de código legacy conviviendo + ~14 tests
verificando comportamiento obsoleto. No vale la pena invertir en código
que va a morir.

## Deuda técnica asumida

| Componente | Estado | Acción en el próximo ciclo |
|-----------|--------|---------------------------|
| `ParticlesGame` | ✅ Migrado (sin compat dual) | — |
| `ColorGame` | ✅ Migrado | Migrado a SceneManager + PygameColorRenderer |
| `GesturesGame` | ✅ Migrado | Migrado a SceneManager + PygameColorRenderer |
| ~~`PygameColorAdapter`~~ | 🔴 Eliminado | ✅ en `feature/refactor/render-migrate-legacy`. Reemplazado por PygameColorRenderer + SceneManager |
| ~~`PygameParticlesAdapter`~~ | 🔴 Eliminado | Nunca existió como archivo; el adapter real fue `PygameParticlesRenderer` |
| ~~`PoseDebugOverlay`~~ | ~~Decorador~~ | ✅ **Eliminado** en `feature/fix#pygame-single-window`. `PoseOverlay` ya lo reemplaza. |
| ~~`render_port.py`~~ | 🔴 Eliminado | ✅ en `feature/refactor/render-migrate-legacy`. Reemplazado por `domain/ports/render/` |

## Qué está disponible en `main`

**Nueva arquitectura lista para usar**:
- Puertos nuevos: `domain/ports/render/`.
- Adaptadores Pygame nuevos: `adapters/render/pygame_*.py`.
- Overlays: `adapters/render/overlays/`.
- `PygameSceneManager`: composición de capacidades + overlays.

**Uso en el próximo ciclo**: al escribir un juego nuevo, usar DIRECTAMENTE:
- `PygameSceneManager`.
- Capacidades (`PygameColorRenderer`, `PygameParticlesRenderer`, etc.).
- Overlays (`PoseOverlay`, `FpsOverlay`).
- **NO** usar los adaptadores legacy.

## Qué NO tocar (mientras esté congelado)

- Fases 6-8 quedaron completadas en `feature/refactor/render-migrate-legacy` (ver abajo).

**Histórico (ya coordinado en `feature/fix#pygame-single-window`)**:
- `PoseDebugOverlay` — 🔴 eliminado. `PoseOverlay` (`OverlayPort`) lo reemplaza.
- `render_port.py` — 🔴 `BaseRenderPort.show()` eliminado.

**Histórico (ya coordinado en `feature/refactor/render-migrate-legacy`)**:
- `PygameColorAdapter` — 🔴 eliminado. Reemplazado por `PygameColorRenderer` + `SceneManager`.
- `render_port.py` — 🔴 eliminado. Reemplazado por `domain/ports/render/`.
- `LandmarkAwareRenderPort` — 🔴 eliminado. Los landmarks los pasa `SceneManager.render_frame(landmarks)` a los overlays.

## Próximos pasos sugeridos

1. **Antes** de escribir un juego real, decidir:
   - ¿Se eliminan los mockups o se reescriben?
   - ¿Se mantiene la compat dual de `ParticlesGame`?
2. **Al empezar el juego real**:
   - Usar `PygameSceneManager` directamente.
   - Migrar tests al nuevo patrón.
   - Eliminar el path legacy del juego migrado.
3. **Cuando todos los juegos migren**: ✅ completado en `feature/refactor/render-migrate-legacy` (adaptadores legacy y `render_port.py` eliminados; `docs/ports_contract.md` actualizado).

---

## ✅ Migración completa (feature/refactor/render-migrate-legacy)

Todos los juegos (`ParticlesGame`, `ColorGame`, `GesturesGame`) usan la nueva arquitectura:
- SceneManager + capacidades + overlays.
- Puertos en `domain/ports/render/`.
- Adaptadores Pygame: `PygameColorRenderer`, `PygameParticlesRenderer`, `PygameHudRenderer`, `PygameInputCursorRenderer`.
- Adaptadores mock: `MockColorRenderAdapter`, `MockParticlesRenderAdapter`, `MockSceneManager` (headless).
- Eliminados: `render_port.py` (legacy), `pygame_color_adapter.py`, `PoseDebugOverlay`, `LandmarkAwareRenderPort`.

**No queda código legacy de render.**
