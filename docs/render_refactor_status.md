# Estado del refactor de render

> **Estado**: Congelado
> **Fecha de congelación**: 2026-10-12
> **Rama original**: `refactor/render-capacities` (mergeada a main)

## Fases completadas

- ✅ **Fase 1**: Puertos nuevos (`ColorRenderPort`, `ParticlesRenderPort`, `HudRenderPort`, `OverlayPort`).
- ✅ **Fase 2**: `ScenePort`.
- ✅ **Fase 3**: Adaptadores Pygame nuevos (`PygameColorRenderer`, `PygameParticlesRenderer`, `PygameHudRenderer`, `PygameSceneManager`).
- ✅ **Fase 4**: Overlays (`PoseOverlay`, `FpsOverlay`).
- ✅ **Fase 5**: Migración de `ParticlesGame` (con compat dual).

## Fases canceladas

- ⏸️ **Fase 6**: Migrar `ColorGame` y `GesturesGame`.
- ⏸️ **Fase 7**: Actualizar mocks y tests.
- ⏸️ **Fase 8**: Limpieza/deprecación.

## Razón de la congelación

Los juegos actuales (ParticlesGame, ColorGame, GesturesGame) son mockups
y van a ser reescritos con lógica de negocio real. Completar el refactor
con compat dual generaría ~560 LOC de código legacy conviviendo + ~14 tests
verificando comportamiento obsoleto. No vale la pena invertir en código
que va a morir.

## Deuda técnica asumida

| Componente | Estado | Acción en el próximo ciclo |
|-----------|--------|---------------------------|
| `ParticlesGame` | Compat dual (nuevo + legacy) | Rehacer sin dual |
| `ColorGame` | Legacy | Rehacer con nueva arquitectura |
| `GesturesGame` | Legacy | Rehacer con nueva arquitectura |
| `PygameColorAdapter` | Legacy vivo | Eliminar cuando los juegos usen `PygameColorRenderer` |
| `PygameParticlesAdapter` | Legacy vivo | Eliminar cuando los juegos usen `PygameParticlesRenderer` |
| `PoseDebugOverlay` | Decorador | Eliminar cuando `PoseOverlay` lo reemplace |
| `render_port.py` | Legacy vivo | Eliminar cuando todos los juegos migren |

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

- NO modificar `PygameParticlesAdapter`, `PygameColorAdapter`,
  `PoseDebugOverlay`, `render_port.py` sin coordinar.
- NO completar Fases 6-8 sin decidir primero si los mockups van a reescribirse.

## Próximos pasos sugeridos

1. **Antes** de escribir un juego real, decidir:
   - ¿Se eliminan los mockups o se reescriben?
   - ¿Se mantiene la compat dual de `ParticlesGame`?
2. **Al empezar el juego real**:
   - Usar `PygameSceneManager` directamente.
   - Migrar tests al nuevo patrón.
   - Eliminar el path legacy del juego migrado.
3. **Cuando todos los juegos migren**:
   - Eliminar adaptadores legacy.
   - Eliminar `render_port.py`.
   - Actualizar `docs/ports_contract.md`.
