# Sistema de Cursores de Interacción

> **Estado**: Implementado (rama `feature/CollisionHandlers`)
> **Última actualización**: [fecha]
> **Documentos relacionados**: `docs/render_architecture.md`, `docs/particles_ecs_system.md`

---

## 🎯 Visión General

Un `InputCursor` representa un **punto de interacción del usuario** (mano, pie,
cadera, etc.) que el juego usa para detectar colisiones con objetivos
(partículas, botones, zonas).

**No es una entidad ECS**. La distinción es deliberada:

| Aspecto | `Particle` (ECS-lite) | `InputCursor` |
|---|---|---|
| Participa en sistemas | ✅ Movimiento, lifespan, animación | ❌ No |
| Tiene física propia | ✅ Velocidad, gravedad | ❌ No |
| Es un objeto del juego | ✅ | ❌ Es una **herramienta de interacción** |
| Estado mutable | ✅ | ✅ Posición / visibilidad / `last_seen` |
| Componentes frozen | ✅ | ✅ Ver `CursorAppearance`, `CursorCollision` |

El cursor **se alimenta de landmarks de pose** y expone consultas de colisión.
La lógica del juego decide qué hacer cuando hay contacto; el cursor no muta
partículas ni conoce reglas de puntuación.

Su configuración es **data-driven**: se declara en el JSON del game profile.

---

## 🏛️ Arquitectura en capas

```text
┌─────────────────────────────────────────────────────────────────┐
│ app/plugins/particles_plugin.py                                 │
│  _build_cursors(raw_cursors, opts)                              │
│    ├── HandLandmarkConfig  (landmarks + offset)                │
│    └── InputCursor         (appearance + collision)            │
└───────────────┬─────────────────────────────────────────────────┘
                │ inyecta
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ domain/services/pose_interaction_facade.py                     │
│  PoseInteractionFacade                                          │
│    ├── dict[str, InputCursor]                                  │
│    ├── dict[str, HandLandmarkConfig]                           │
│    ├── CollisionHandler                                        │
│    └── EMA + timeout                                           │
└───────────────┬─────────────────────────────────────────────────┘
                │ usa
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ domain/services/collision_handler.py                            │
│  CollisionHandler (Protocol)                                    │
│  CentroidCollisionHandler                                      │
└───────────────┬─────────────────────────────────────────────────┘
                │ calcula punto
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ domain/entities/input_cursor.py                                 │
│  InputCursor + CursorAppearance + CursorCollision              │
│ domain/entities/hand_landmark_config.py                        │
│  HandLandmarkConfig                                            │
└───────────────┬─────────────────────────────────────────────────┘
                │ renderiza
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ adapters/render/pygame_input_cursor.py                          │
│  PygameInputCursorRenderer (InputCursorRenderPort)              │
│  = RenderCapability (no overlay)                                │
└─────────────────────────────────────────────────────────────────┘
```

Flujo resumido:

1. El plugin lee `game_options.cursors` del JSON y construye configuraciones.
2. `PoseInteractionFacade.update()` calcula el punto de cada cursor con el
   `CollisionHandler`, aplica EMA y actualiza `InputCursor`.
3. El juego consulta `is_touching(...)` para resolver colisiones.
4. `PygameInputCursorRenderer` dibuja los cursores como capacidad de la escena.

---

## 🧩 Componentes del cursor

### `InputCursor`

`domain/entities/input_cursor.py`

Combina **estado mutable** con **componentes de configuración frozen**:

| Campo | Tipo | Mutable | Descripción |
|---|---|---|---|
| `cursor_id` | `str` | ❌ | Identificador (`"left_hand"`, `"right_hand"`, `"feet"`, ...) |
| `position` | `tuple[float, float] \| None` | ✅ | Posición normalizada 0-1 |
| `is_visible` | `bool` | ✅ | Visibilidad actual |
| `last_seen` | `float` | ✅ | Timestamp de última detección (segundos) |
| `appearance` | `CursorAppearance` | ❌ | Configuración visual |
| `collision` | `CursorCollision` | ❌ | Configuración de colisión |
| `sprite_config` | `SpriteConfig \| None` | ❌ | Sprite opcional (reutiliza el de partículas) |
| `sprite_state` | `SpriteState \| None` | ✅ | Frame actual del sprite |

Métodos clave:

- `update(new_position, current_time, timeout)`: actualiza posición y aplica
  timeout. Si no hay detección pero no ha vencido el timeout, **mantiene la
  última posición** (persistencia ante oclusiones).
- `get_position_pixels(screen_w, screen_h)`: convierte la posición normalizada
  a píxeles.
- `get_collision_radius_pixels(screen_w, screen_h)`: convierte el radio
  porcentual a píxeles.

### `CursorAppearance`

Componente visual, análogo a `Appearance` de `Particle`:

| Campo | Default | Validación |
|---|---|---|
| `size` | `40.0` | Debe ser `> 0` |
| `color` | `(255, 255, 0)` | RGB, cada canal `0-255` |
| `padding_x` | `0.0` | No afecta a la colisión |
| `padding_y` | `0.0` | No afecta a la colisión |

### `CursorCollision`

| Campo | Default | Descripción |
|---|---|---|
| `radius` | `20.0` | Radio como **porcentaje del mínimo de pantalla** (`0-100`) |

El radio en píxeles se obtiene con:

```python
radius_px = collision.radius * min(screen_w, screen_h) / 100.0
```

Esto mantiene la sensación de colisión independientemente de la resolución.

### `HandLandmarkConfig`

`domain/entities/hand_landmark_config.py`

| Campo | Tipo | Default | Validación |
|---|---|---|---|
| `landmark_names` | `tuple[str, ...]` | — | No puede estar vacío |
| `offset_x` | `float` | `0.0` | Rango `[-1.0, 1.0]` |
| `offset_y` | `float` | `0.0` | Rango `[-1.0, 1.0]` |

Los offsets están en **coordenadas normalizadas 0-1**, no en píxeles.

---

## 🎯 `CollisionHandler`

`domain/services/collision_handler.py`

### Protocolo

```python
class CollisionHandler(Protocol):
    def calculate_point(
        self,
        landmarks: list[PoseLandmark],
        config: HandLandmarkConfig,
    ) -> tuple[float, float] | None: ...
```

### `CentroidCollisionHandler`

Implementación por defecto:

1. Filtra los landmarks cuyo nombre esté en `config.landmark_names` y que sean
   visibles (`PoseLandmark.is_visible()` → `visibility > 0.5`).
2. Si no queda ninguno, devuelve `None`.
3. Calcula el centroide (promedio de `x` e `y`).
4. Aplica `offset_x` / `offset_y`.

**¿Por qué ignorar landmarks invisibles?** MediaPipe puede perder puntos
parcialmente ocluidos (p. ej. el pulgar detrás del cuerpo). Incluirlos
arrastraría el centroide hacia posiciones falsas. Filtrarlos hace el cursor
**tolerante a oclusiones**.

---

## 🔄 `PoseInteractionFacade` refactorizada

`domain/services/pose_interaction_facade.py`

La fachada pasó de gestionar manos sueltas a gestionar un **diccionario de
cursores**:

| Antes | Ahora |
|---|---|
| Variables para mano izquierda/derecha | `dict[str, InputCursor]` |
| Configuración hardcodeada | `cursor_configs: dict[str, HandLandmarkConfig]` |
| Un único timeout implícito | `hand_timeout: float` configurable |
| `is_touching` solo para manos | `is_touching(..., cursor_id=None)` multi-cursor |

Constructor:

```python
PoseInteractionFacade(
    smoothing_factor=0.3,
    hand_timeout=2.0,
    cursor_configs=cursor_configs,
    collision_handler=CentroidCollisionHandler(),
    cursors=cursors,
)
```

Comportamiento:

- Si `cursor_configs` es `None`, usa defaults para `left_hand` y `right_hand`
  (`left_wrist` / `right_wrist`).
- Si `cursors` no trae un cursor declarado, la fachada crea un `InputCursor`
  de fallback con el mismo `cursor_id`.
- `update(landmarks, current_time=None)` usa `time.monotonic()` si no se pasa
  timestamp.

### `is_touching`

```python
def is_touching(
    self,
    target_x: float,
    target_y: float,
    radius: float,
    screen_w: int,
    screen_h: int,
    cursor_id: str | None = None,
) -> bool: ...
```

- `cursor_id=None` → comprueba **todos** los cursores.
- `cursor_id="left_hand"` → comprueba solo ese cursor.
- La colisión es `distancia <= cursor_radius_px + target_radius`.
- Un cursor invisible o sin posición nunca colisiona.

> Nota: `cursor_id` va **al final y con default** para no romper las llamadas
> existentes (`ParticlesGame._update_logic`).

### Flujo de actualización

```mermaid
flowchart LR
    L[landmarks: list[PoseLandmark]] --> C[CollisionHandler.calculate_point]
    C -->|punto crudo o None| E[EMA smoothing]
    E -->|posición suavizada| U[InputCursor.update]
    U --> T{timeout superado?}
    T -->|no| P[mantiene última posición]
    T -->|sí| H[is_visible=False / position=None]
    U --> R[PoseInteractionFacade.get_all_cursors]
    R --> D[PygameInputCursorRenderer]
```

Métodos de consulta:

- `get_hand_position(hand, screen_w, screen_h)`: compatibilidad hacia atrás.
- `get_cursor(cursor_id)`: un cursor concreto.
- `get_all_cursors()`: todos los cursores (usado por el renderer).

---

## 🖼️ `PygameInputCursorRenderer`

`adapters/render/pygame_input_cursor.py`

Es una **capacidad de render**, **no un overlay**:

- Los overlays son opcionales y de debug (`PoseOverlay`, `FpsOverlay`).
- Los cursores son parte de la jugabilidad: sin ellos el usuario no puede
  interactuar. Por eso se registran en `SceneManager` junto a color, partículas
  y HUD.

Implementa `InputCursorRenderPort`, que a su vez hereda de `RenderCapability`:

```python
class InputCursorRenderPort(RenderCapability):
    def set_cursors(self, cursors: list[InputCursor]) -> None: ...
    def render_cursors(self) -> None: ...
    def close(self) -> None: ...
```

`render()` (método unificado de `RenderCapability`) delega en `render_cursors()`.

Características:

- **Círculos**: borde de 3 px + relleno translúcido (`alpha=80`).
- **Sprites animados**: extrae el frame actual del sprite sheet y lo escala al
  tamaño de `CursorAppearance`.
- **Cache de sprites** por `SpriteConfig.path`.
- **Fallback a círculo** si `pygame.image.load` falla (`pygame.error`).
- **Mirror opcional** (`mirror=True`) para cámaras en espejo.
- Solo dibuja cursores con `is_visible=True` y `position is not None`.

Flujo en el juego:

```python
# ParticlesGame._render_frame
if hasattr(self._pose_interaction, "get_all_cursors"):
    current_cursors = self._pose_interaction.get_all_cursors()
    for capability in getattr(self._scene, "_capabilities", []):
        if isinstance(capability, PygameInputCursorRenderer):
            capability.set_cursors(current_cursors)
            break

await asyncio.to_thread(self._scene.render_frame, landmarks)
```

> Nota: El código usa `hasattr` y `getattr` como patrón defensivo para
> mantener compatibilidad con versiones anteriores de la fachada y del
> `SceneManager`. En un refactor futuro, esto podría simplificarse
> inyectando el `cursor_capability` directamente al juego.

---

## 📜 Configuración JSON

Los cursores se declaran en `game_profiles/<juego>/<perfil>.json`, dentro de
`game_options`:

```json
{
  "pose_smoothing_factor": 0.3,
  "game_options": {
    "cursor_timeout": 2.0,
    "cursors": {
      "left_hand": {
        "landmark_names": ["left_wrist", "left_pinky", "left_index", "left_thumb"],
        "offset_x": 0.02,
        "offset_y": -0.03,
        "appearance": {
          "size": 40.0,
          "color": [255, 255, 0],
          "padding_x": 0.0,
          "padding_y": 0.0
        },
        "collision": {
          "radius": 5.0
        }
      },
      "right_hand": {
        "landmark_names": ["right_wrist", "right_pinky", "right_index", "right_thumb"],
        "offset_x": -0.02,
        "offset_y": -0.03,
        "appearance": {
          "size": 40.0,
          "color": [0, 255, 255],
          "padding_x": 0.0,
          "padding_y": 0.0
        },
        "collision": {
          "radius": 5.0
        }
      }
    }
  }
}
```

### Claves

| Clave | Tipo | Default | Descripción |
|---|---|---|---|
| `cursor_timeout` | `float` | `2.0` | Segundos antes de perder un cursor |
| `cursors` | `dict[str, object]` | `left_hand` / `right_hand` | Cursores declarados |
| `cursors.<id>.landmark_names` | `list[str]` | `["<id>_wrist"]` | Landmarks usados |
| `cursors.<id>.offset_x` | `float` | `0.0` | Offset normalizado |
| `cursors.<id>.offset_y` | `float` | `0.0` | Offset normalizado |
| `cursors.<id>.appearance.size` | `float` | `40.0` | Tamaño visual |
| `cursors.<id>.appearance.color` | `[int, int, int]` | `[255, 255, 0]` | Color RGB |
| `cursors.<id>.appearance.padding_x/y` | `float` | `0.0` | Padding visual |
| `cursors.<id>.collision.radius` | `float` | `5.0` | Radio de colisión (% del mínimo de pantalla) |

`ParticlesPlugin._build_cursors()` valida y convierte esta sección en
`(cursor_configs, cursors)`. Si `cursors` no existe, usa los defaults de
`left_hand` y `right_hand` con `left_wrist` / `right_wrist`.

---

## 🧪 Tests

| Archivo | Cobertura |
|---|---|
| `tests/unit/test_input_cursor.py` | Estado mutable, timeout, conversión a píxeles |
| `tests/unit/test_collision_handler.py` | Centroide, filtrado por visibilidad, offsets |
| `tests/unit/test_pose_interaction_facade.py` | Multi-cursor, EMA, `is_touching` |
| `tests/unit/test_pygame_input_cursor.py` | Círculos, sprites, fallback, cache |
| `tests/unit/test_particles_plugin_cursors.py` | Parseo data-driven del JSON |
