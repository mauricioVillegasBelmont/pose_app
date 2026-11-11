# Sistema de Spawn Data-Driven

**Estado:** 🟢 Completado
**Fecha:** Octubre 2026
**Versión:** 1.0

## Resumen

Implementación completa del sistema de spawn de partículas basado en estrategias y configuración data-driven desde JSON.

## Arquitectura

### Componentes principales

1. **ParticleArchetype** (`domain/entities/particles/archetype.py`)
   - Value Object inmutable que define el "ADN" de un tipo de partícula
   - Campos: name, weight, size, color, sprite_config
   - Validación estricta en `__post_init__`

2. **Protocolos de Spawn** (`domain/entities/particles/spawn/ports.py`)
   - `ArchetypeSelector`: decide QUÉ partícula generar
   - `PositionStrategy`: decide DÓNDE colocarla
   - `SpawnStrategy`: orquesta la creación completa

3. **Implementaciones** (`domain/entities/particles/spawn/`)
   - `selectors.py`: WeightedSelector, SequentialSelector
   - `positions.py`: RandomPositionStrategy, GridPositionStrategy
   - `strategies.py`: ComposedSpawnStrategy (composición)

4. **Integración con ParticlesGame** (`domain/games/particles/main.py`)
   - Constructor simplificado: recibe `spawn_strategy` + `archetypes`
   - Elimina parámetros sueltos: particle_size, particle_color, particle_min_distance, sprite_config
   - Método `_start_new_round()` usa `spawn_strategy.spawn()`

5. **Plugin Data-Driven** (`app/plugins/particles_plugin.py`)
   - Lee `particle_archetypes` y `spawn_config` del JSON
   - Construye estrategias según configuración
   - Validación estricta con `ConfigurationError`

### Diagrama de flujo

```mermaid
flowchart TD
    A[JSON: game_profiles/particles/normal.json] --> B[ParticlesPlugin.create_game]
    B --> C[Leer particle_archetypes]
    B --> D[Leer spawn_config]
    C --> E[Construir list[ParticleArchetype]]
    D --> F[Construir ArchetypeSelector]
    D --> G[Construir PositionStrategy]
    F --> H[ComposedSpawnStrategy]
    G --> H
    E --> I[ParticlesGame]
    H --> I
```

## Archivos creados/modificados

### Nuevos archivos
- `src/pose_app/domain/entities/particles/archetype.py`
- `src/pose_app/domain/entities/particles/spawn/__init__.py`
- `src/pose_app/domain/entities/particles/spawn/ports.py`
- `src/pose_app/domain/entities/particles/spawn/selectors.py`
- `src/pose_app/domain/entities/particles/spawn/positions.py`
- `src/pose_app/domain/entities/particles/spawn/strategies.py`
- `tests/unit/test_particle_archetype.py`
- `tests/unit/test_spawn_ports.py`
- `tests/unit/test_selectors.py`
- `tests/unit/test_position_strategies.py`
- `tests/unit/test_spawn_strategies.py`
- `tests/unit/test_particles_plugin_spawn.py`

### Archivos modificados
- `src/pose_app/domain/games/particles/main.py` (refactor constructor)
- `src/pose_app/app/plugins/particles_plugin.py` (construcción desde JSON)
- `game_profiles/particles/normal.json` (nueva estructura)
- `tests/unit/test_particles_game.py` (actualizar fixture)

## Cobertura de tests

- **ParticleArchetype**: 11 tests (creación, validación, inmutabilidad)
- **Spawn Ports**: 12 tests (protocolos, runtime checkable)
- **Selectors**: 12 tests (weighted, sequential, distribución, errores)
- **Position Strategies**: 8 tests (random, grid, min_distance, capacidad)
- **Spawn Strategies**: 5 tests (composición, ensamblaje ECS, acumulación)
- **Plugin Integration**: 5 tests (construcción desde JSON, errores)

**Total: 53 tests, todos pasando ✅**

## Principios de diseño aplicados

1. **Composición sobre herencia**: `ComposedSpawnStrategy` compone selector + posicionador
2. **Principio de Responsabilidad Única**: Cada estrategia hace una sola cosa
3. **Fail-Fast**: Validación estricta al cargar JSON, errores claros con contexto
4. **Data-Driven**: Todo configurable desde JSON sin tocar código
5. **Inmutabilidad por defecto**: Todos los archetypes y estrategias son `frozen=True`
6. **Separación de preocupaciones**: El archetype no sabe de spawn, la estrategia no sabe de archetypes

## Ejemplos de uso

### Configuración JSON básica

```json
{
  "particle_archetypes": [
    {"name": "default", "weight": 1.0, "size": 20.0, "color": [255, 200, 50]}
  ],
  "spawn_config": {
    "archetype_selector": "weighted",
    "position_strategy": "random",
    "min_distance": 0.15
  }
}
```

### Configuración JSON avanzada (múltiples tipos)

```json
{
  "particle_archetypes": [
    {"name": "fire", "weight": 0.7, "size": 25.0, "color": [255, 100, 0]},
    {"name": "ice", "weight": 0.3, "size": 20.0, "color": [100, 200, 255]}
  ],
  "spawn_config": {
    "archetype_selector": "weighted",
    "position_strategy": "random",
    "min_distance": 0.2,
    "max_attempts": 100
  }
}
```

## Extensibilidad

### Añadir nueva estrategia de selección

1. Crear clase en `selectors.py` que implemente `ArchetypeSelector`
2. Añadir tests en `test_selectors.py`
3. Actualizar plugin para soportar el nuevo tipo en `spawn_config.archetype_selector`

### Añadir nueva estrategia de posición

1. Crear clase en `positions.py` que implemente `PositionStrategy`
2. Añadir tests en `test_position_strategies.py`
3. Actualizar plugin para soportar el nuevo tipo en `spawn_config.position_strategy`

## Roadmap futuro

- [ ] `FixedPositionStrategy`: posiciones fijas orquestadas
- [ ] `SequentialSelector` integrado en plugin
- [ ] Soporte para `stages` (secuencias de configuraciones)
- [ ] Hot-reload de configuración JSON sin reiniciar
