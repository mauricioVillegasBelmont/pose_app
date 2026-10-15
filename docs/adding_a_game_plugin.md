# Manual: Cómo añadir un nuevo juego como plugin

> **Audiencia**: desarrolladores que quieren añadir un juego nuevo a Pose AR
> sin conocer los detalles internos de la plataforma.
>
> **Versión del documento**: 1.0
> **Última actualización**: [fecha]
> **Compatible con**: arquitectura hexagonal v0.5+

---

## 📚 Tabla de contenidos

1. [Introducción](#introducción)
2. [Conceptos previos](#conceptos-previos)
3. [Arquitectura en 5 minutos](#arquitectura-en-5-minutos)
4. [Anatomía de un plugin](#anatomía-de-un-plugin)
5. [Tutorial: Juego "Saludo" paso a paso](#tutorial-juego-saludo-paso-a-paso)
6. [Referencia de puertos y contratos](#referencia-de-puertos-y-contratos)
7. [Patrones recomendados](#patrones-recomendados)
8. [Testing](#testing)
9. [Checklist final](#checklist-final)
10. [Preguntas frecuentes](#preguntas-frecuentes)

---

## Introducción

Pose AR permite añadir **juegos nuevos** sin modificar el núcleo de la
aplicación. Cada juego vive en su propio **plugin** que se registra
automáticamente al iniciar.

**Filosofía del sistema**:

- **El núcleo no conoce los juegos**. Solo conoce el contrato `GamePlugin`.
- **Añadir un juego no requiere tocar `main.py`, `Container`, ni rutas**.
- **Cada juego es independiente**: su estado, su lógica, sus adaptadores.

Si puedes escribir tu juego como una clase que cumple el contrato `GameProtocol`
y una factory que cumple `GamePlugin`, ya tienes un plugin.

---

## Conceptos previos

Si vienes de programación "clásica" (todo en un solo módulo), estos conceptos
te ayudarán:

| Concepto | Significado en este proyecto |
|----------|-------------------------------|
| **Puerto** | Interfaz abstracta que define QUÉ hace algo |
| **Adaptador** | Implementación concreta de un puerto |
| **Plugin** | Factory que sabe construir un juego y su estado |
| **Dominio** | Lógica pura, sin dependencias externas |
| **Dependencias compartidas** | Recursos únicos (cámara, pose, bus de eventos) |

**Regla de oro**: el dominio NO conoce los adaptadores. Los puertos sí.

---

## Arquitectura en 5 minutos

```
┌─────────────────────────────────────────────────────┐
│                      NÚCLEO                         │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────┐ │
│  │  Container   │  │ PluginRegistry│  │ Main.py   │ │
│  └──────┬───────┘  └──────┬────────┘  └─────┬─────┘ │
│         │                 │                 │       │
│         └─────────────────┼─────────────────┘       │
│                           │                         │
└───────────────────────────┼─────────────────────────┘
                            │ usa el contrato
                            ▼
                   ┌──────────────────┐
                   │   GamePlugin     │  ← Interfaz que TÚ implementas
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
      ┌─────────────┐ ┌──────────┐ ┌────────────┐
      │ Particles   │ │  Color   │ │  TU JUEGO  │
      │ Plugin      │ │  Plugin  │ │  Plugin    │
      └─────────────┘ └──────────┘ └────────────┘
```

**Flujo al iniciar**:

1. `Container` carga `PluginRegistry` (que auto-registra plugins builtin).
2. `main.py` pide al `Container`: `create_game()`.
3. `Container` consulta `settings.game.type` (ej: "tu_juego").
4. `Container` pide al `PluginRegistry` el plugin con ese `game_id`.
5. El plugin construye el juego con las dependencias compartidas.
6. El juego corre en un `asyncio.Task` en paralelo con la API.

---

## Anatomía de un plugin

Un plugin completo son **4 archivos**:

```
app/plugins/
├── __init__.py              ← Registra tu plugin (1 línea)
└── tu_juego_plugin.py       ← Tu plugin (implementa GamePlugin)

domain/games/
└── tu_juego/
    └── state.py             ← Tu estado (implementa GameStatePort)

domain/use_cases/
└── tu_juego.py              ← Tu juego (implementa GameProtocol)
```

**Opcional pero recomendado**:

```
domain/entities/                ← Entidades específicas de tu juego
└── tu_entidad.py

domain/events/                  ← Eventos que tu juego publica/escucha
└── tu_juego_events.py
```

### 🧩 Los 4 contratos que debes cumplir

#### 1. `GameProtocol` (estructural, no hereda)

Tu juego debe tener:

```python
class TuJuego:
    @property
    def state(self) -> GameStatePort: ...

    async def run_async(
        self, should_stop: Callable[[], bool] | None = None
    ) -> None: ...
```

#### 2. `GameStatePort` (ABC)

Tu estado debe implementar:

```python
class TuEstado(GameStatePort):
    @property
    def game_id(self) -> str: ...

    def snapshot(self) -> dict[str, Any]: ...

    def stats(self) -> dict[str, Any]: ...
```

#### 3. `GamePlugin` (ABC)

Tu plugin debe implementar:

```python
class TuPlugin(GamePlugin):
    @property
    def game_id(self) -> str: ...

    @property
    def display_name(self) -> str: ...

    def create_state(self) -> GameStatePort: ...

    def create_game(self, context: GameContext) -> GameProtocol: ...
```

#### 4. `GameContext` (lo recibes, no lo implementas)

Es un `dataclass` inmutable con las dependencias compartidas:

```python
@dataclass(frozen=True)
class GameContext:
    camera: CameraPort
    pose_estimator: PoseEstimatorPort
    event_bus: EventBusPort
    settings: Settings
```

**Úsalo durante `create_game()`**, no lo guardes globalmente.

---

## Tutorial: Juego "Saludo" paso a paso

Vamos a crear un juego que detecta cuando la mano derecha está cerca de la
cabeza (un "saludo") y cambia el color de fondo a verde.

### Paso 1: Definir el estado

**Archivo**: `domain/games/saludo/state.py`

```python
"""
Estado del juego de saludo.
"""

from threading import Lock
from typing import Any

from domain.entities.color import RGBColor
from domain.state.game_state_port import GameStatePort


class SaludoState(GameStatePort):
    """Estado consultable del juego de saludo."""

    def __init__(self):
        self._lock = Lock()
        self._greeting_detected: bool = False
        self._greeting_count: int = 0
        self._background_color: RGBColor = RGBColor(20, 20, 20)

    @property
    def game_id(self) -> str:
        return "saludo"

    # ==========================================
    # API de escritura (la usa tu juego)
    # ==========================================

    def set_greeting(self, detected: bool, color: RGBColor) -> None:
        with self._lock:
            self._greeting_detected = detected
            self._background_color = color
            if detected:
                self._greeting_count += 1

    # ==========================================
    # GameStatePort
    # ==========================================

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "greeting_detected": self._greeting_detected,
                "greeting_count": self._greeting_count,
                "background_color": self._background_color.to_hex(),
            }

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "greetings": self._greeting_count,
            }
```

### Paso 2: Definir el juego

**Archivo**: `domain/use_cases/saludo_game.py`

```python
"""
Juego de saludo.

Detecta cuando la mano derecha está cerca de la cabeza (un "saludo")
y cambia el color de fondo a verde.
"""

import asyncio
from collections.abc import Callable

from domain.entities.color import RGBColor
from domain.entities.pose_landmark import PoseLandmark
from domain.games.saludo.state import SaludoState
from domain.ports.camera_port import CameraPort
from domain.ports.event_bus_port import EventBusPort
from domain.ports.pose_estimator_port import PoseEstimatorPort
from domain.ports.render_port import ColorRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("use_cases.saludo")


class SaludoGame:
    """Juego que detecta un saludo con la mano."""

    # Colores
    IDLE_COLOR = RGBColor(20, 20, 20)
    GREETING_COLOR = RGBColor(0, 200, 100)

    # Umbrales (reglas de negocio)
    MAX_DISTANCE_TO_HEAD = 0.15  # Distancia euclidiana normalizada

    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        renderer: ColorRenderPort,
        state: SaludoState,
        event_bus: EventBusPort,
    ):
        self._camera = camera
        self._pose_estimator = pose_estimator
        self._renderer = renderer
        self._state = state
        self._event_bus = event_bus
        self._frame_count = 0

    @property
    def state(self) -> SaludoState:
        return self._state

    async def run_async(self, should_stop: Callable[[], bool] | None = None) -> None:
        should_stop = should_stop or (lambda: False)

        await asyncio.to_thread(self._camera.start)
        logger.info("Juego de saludo iniciado")

        try:
            while not should_stop():
                frame = await asyncio.to_thread(self._camera.get_frame)
                if frame is None:
                    await asyncio.sleep(0.001)
                    continue

                try:
                    landmarks = await asyncio.to_thread(
                        self._pose_estimator.estimate, frame
                    )
                except Exception as e:
                    logger.warning(f"Error estimando pose: {e}")
                    continue

                # Lógica del juego
                greeting = self._detect_greeting(landmarks)
                color = self.GREETING_COLOR if greeting else self.IDLE_COLOR
                self._state.set_greeting(greeting, color)

                # Render
                try:
                    await asyncio.to_thread(
                        self._renderer.render_background, color, landmarks
                    )
                except Exception as e:
                    logger.error(f"Error renderizando: {e}")
                    break

                self._frame_count += 1
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info("Juego de saludo cancelado")
            raise
        finally:
            try:
                self._renderer.close()
            except Exception as e:
                logger.error(f"Error cerrando renderer: {e}")
            try:
                await asyncio.to_thread(self._camera.stop)
            except Exception as e:
                logger.error(f"Error cerrando cámara: {e}")
            logger.info(f"Juego saludo terminado. Frames: {self._frame_count}")

    # ==========================================
    # Reglas de negocio
    # ==========================================

    def _detect_greeting(self, landmarks: list[PoseLandmark]) -> bool:
        """Regla de negocio: mano derecha cerca de la cabeza."""
        if not landmarks:
            return False

        right_wrist = self._find(landmarks, "right_wrist")
        nose = self._find(landmarks, "nose")

        if not right_wrist or not nose:
            return False

        if not right_wrist.is_visible() or not nose.is_visible():
            return False

        distance = right_wrist.distance_to(nose)
        return distance < self.MAX_DISTANCE_TO_HEAD

    def _find(self, landmarks: list[PoseLandmark], name: str) -> PoseLandmark | None:
        for lm in landmarks:
            if lm.name and lm.name.lower() == name.lower():
                return lm
        return None
```

### Paso 3: Definir el plugin

**Archivo**: `app/plugins/saludo_plugin.py`

```python
"""
Plugin del juego de saludo.
"""

from app.game_context import GameContext
from domain.games.saludo.state import SaludoState
from domain.plugins.game_plugin import GamePlugin, GameProtocol
from domain.state.game_state_port import GameStatePort
from domain.use_cases.saludo_game import SaludoGame
from infrastructure.errors.exceptions import ConfigurationError
from infrastructure.logging.logger import get_logger

logger = get_logger("app.plugins.saludo")


class SaludoPlugin(GamePlugin):
    """Plugin que construye el juego de saludo."""

    @property
    def game_id(self) -> str:
        return "saludo"

    @property
    def display_name(self) -> str:
        return "Saludo Game"

    @property
    def description(self) -> str:
        return "Detecta cuando saludas con la mano derecha."

    def create_state(self) -> GameStatePort:
        return SaludoState()

    def create_game(self, context: GameContext) -> GameProtocol:
        renderer = self._create_renderer(context)
        state = SaludoState()

        return SaludoGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            renderer=renderer,
            state=state,
            event_bus=context.event_bus,
        )

    def _create_renderer(self, context: GameContext):
        cfg = context.settings.render

        if cfg.provider == "mock":
            from adapters.mock.mock_render import MockColorRenderAdapter

            return MockColorRenderAdapter()

        if cfg.provider == "pygame":
            from adapters.render.pygame_color_adapter import PygameColorAdapter

            return PygameColorAdapter(
                width=cfg.width,
                height=cfg.height,
                title="Saludo Game",
                target_fps=cfg.target_fps,
            )

        raise ConfigurationError(
            f"Proveedor de render desconocido: {cfg.provider}",
            context={"provider": cfg.provider, "plugin": self.game_id},
        )
```

### Paso 4: Registrar el plugin

**Archivo**: `app/plugins/__init__.py` (editar)

```python
def register_builtin_plugins(registry: PluginRegistry) -> None:
    from app.plugins.color_plugin import ColorPlugin
    from app.plugins.particles_plugin import ParticlesPlugin
    from app.plugins.saludo_plugin import SaludoPlugin  # ← AÑADIR

    registry.register(ParticlesPlugin())
    registry.register(ColorPlugin())
    registry.register(SaludoPlugin())  # ← AÑADIR

    logger.info(f"Plugins builtin registrados: {registry.list_ids()}")
```

### Paso 5: Probar

```bash
GAME_TYPE=saludo POSE_PROVIDER=mock RENDER_PROVIDER=mock python -m app.main
```

Deberías ver en logs:

```
[HH:MM:SS.mmm] INFO  pose_ar.app.plugins | Plugin registrado: saludo (Saludo Game)
[HH:MM:SS.mmm] INFO  pose_ar.di          | Creando juego desde plugin: saludo
[HH:MM:SS.mmm] INFO  pose_ar.use_cases.saludo | Juego de saludo iniciado
```

Y en otra terminal:

```bash
curl http://localhost:8000/api/v1/state
# {"games": {"saludo": {"greeting_detected": false, ...}}, "active_games": ["saludo"]}
```

**¡Listo!** Añadiste un juego sin tocar `Container`, `main.py`, ni `routes.py`.

---

## Referencia de puertos y contratos

### Puertos de entrada

| Puerto | Método principal | Uso |
|--------|------------------|-----|
| `CameraPort` | `get_frame() -> np.ndarray \| None` | Obtener frames de video |
| `PoseEstimatorPort` | `estimate(frame) -> list[PoseLandmark]` | Extraer pose |

### Puertos de salida

| Puerto | Método principal | Uso |
|--------|------------------|-----|
| `ParticlesRenderPort` | `render_particles(particles)` | Dibujar partículas |
| `ColorRenderPort` | `render_background(color, landmarks)` | Fondo + esqueleto |
| `LandmarkAwareRenderPort` | `update_landmarks(landmarks)` | Recibir landmarks (opcional) |

### Puertos de comunicación

| Puerto | Método principal | Uso |
|--------|------------------|-----|
| `EventBusPort` | `publish(event)` / `subscribe(type, handler)` | Eventos async |
| `GameStatePort` | `snapshot()` / `stats()` | Estado consultable |

### Entidades del dominio

| Entidad | Campos clave | Uso |
|---------|--------------|-----|
| `PoseLandmark` | `x, y, z, visibility, name` | Un punto de la pose |
| `Particle` | `x, y, vx, vy, life, size, color` | Una partícula |
| `RGBColor` | `r, g, b` | Color RGB inmutable |

---

## Patrones recomendados

### 🎯 Patrón 1: Separar reglas de negocio

**Mal**:

```python
async def run_async(self, should_stop=None):
    while not should_stop():
        # 200 líneas mezclando IO con lógica
        ...
```

**Bien**:

```python
async def run_async(self, should_stop=None):
    while not should_stop():
        # 1. IO
        landmarks = await self._get_landmarks()
        # 2. Lógica pura (testeable)
        result = self._apply_rules(landmarks)
        # 3. IO
        await self._render(result)


def _apply_rules(self, landmarks: list[PoseLandmark]) -> Result:
    """Función pura, testeable sin mocks."""
    ...
```

**Beneficio**: puedes testear `_apply_rules` con listas de landmarks sin cámara.

### 🎯 Patrón 2: Usar `asyncio.to_thread` para IO bloqueante

Pygame, OpenCV y Mediapipe son **síncronos**. No los llames directo en async.

**Mal**:

```python
frame = self._camera.get_frame()  # Bloquea el loop
```

**Bien**:

```python
frame = await asyncio.to_thread(self._camera.get_frame)
```

### 🎯 Patrón 3: Escribir al estado con locks

El estado es leído por la API (otro thread). Protege con `Lock`.

```python
class TuEstado(GameStatePort):
    def __init__(self):
        self._lock = Lock()
        self._data = ...

    def update(self, value):
        with self._lock:  # ← siempre
            self._data = value

    def snapshot(self):
        with self._lock:  # ← siempre
            return dict(self._data)
```

### 🎯 Patrón 4: Suscribirse a eventos en `__init__`, no en `run_async`

**Mal**:

```python
async def run_async(self, should_stop=None):
    self._event_bus.subscribe(...)  # Se duplica si run_async se llama 2 veces
```

**Bien**:

```python
def __init__(self, ..., event_bus):
    ...
    event_bus.subscribe(GameResetRequested, self._on_reset)
```

### 🎯 Patrón 5: Usar banderas en handlers, no mutar directamente

Los handlers de eventos pueden correr en otro thread. **No muten estado compartido directamente**.

**Bien**:

```python
def __init__(self):
    self._reset_requested = False


async def _on_reset(self, event):
    self._reset_requested = True  # Bandera


async def run_async(self, should_stop=None):
    while not should_stop():
        if self._reset_requested:
            self._do_reset()
            self._reset_requested = False
        ...
```

---

## Testing

### Test unitario de reglas de negocio

```python
# tests/unit/test_saludo_rules.py

from domain.entities.pose_landmark import PoseLandmark
from domain.use_cases.saludo_game import SaludoGame


def test_greeting_detected_when_hand_near_head():
    """Mano derecha a 0.05 de la nariz → saludo."""
    game = _create_game_for_testing()
    landmarks = [
        PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose"),
        PoseLandmark(x=0.53, y=0.5, z=0.0, visibility=1.0, name="right_wrist"),
    ]
    assert game._detect_greeting(landmarks) is True


def test_no_greeting_when_hand_far():
    """Mano derecha a 0.5 de la nariz → no saludo."""
    game = _create_game_for_testing()
    landmarks = [
        PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, name="nose"),
        PoseLandmark(x=0.9, y=0.9, z=0.0, visibility=1.0, name="right_wrist"),
    ]
    assert game._detect_greeting(landmarks) is False
```

### Test de integración con mocks

```python
# tests/integration/test_saludo_plugin_e2e.py


def test_saludo_plugin_loads(monkeypatch):
    monkeypatch.setenv("GAME_TYPE", "saludo")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    reset_settings()
    settings = Settings()

    container = Container(settings)
    game = container.create_game()

    assert game.state.game_id == "saludo"
```

---

## Checklist final

Antes de considerar tu plugin terminado:

- [ ] `TuEstado` implementa `GameStatePort` y usa `Lock`.
- [ ] `TuJuego` expone `state` property y `run_async`.
- [ ] `TuJuego` cierra renderer y cámara en `finally`.
- [ ] `TuPlugin` implementa `GamePlugin`.
- [ ] Registraste el plugin en `app/plugins/__init__.py`.
- [ ] El juego corre con `GAME_TYPE=tu_juego ... python -m app.main`.
- [ ] `curl /api/v1/state` muestra tu juego.
- [ ] Tienes al menos 1 test unitario de reglas de negocio.
- [ ] Documentaste tu juego en `docs/games/tu_juego.md` (opcional).

---

## Preguntas frecuentes

### ❓ ¿Cómo añado un nuevo puerto (input)?

1. Créalo en `domain/ports/tu_puerto.py` como ABC.
2. Implementa un adaptador en `adapters/`.
3. Añádelo a `GameContext` si es compartido.
4. Inyecta en tu juego desde `create_game()`.

### ❓ ¿Cómo publico un evento?

```python
from domain.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class TuEvento(DomainEvent):
    payload: str


# En el juego:
await self._event_bus.publish(TuEvento(payload="hola"))
```

### ❓ ¿Cómo escucho un evento global?

```python
def __init__(self, ..., event_bus):
    event_bus.subscribe(GameResetRequested, self._on_reset)

async def _on_reset(self, event: GameResetRequested) -> None:
    self._reset_requested = True
```

### ❓ ¿Cómo accedo a la configuración?

```python
def create_game(self, context: GameContext) -> GameProtocol:
    my_setting = context.settings.game.some_field
    ...
```

Si necesitas un campo nuevo, añádelo a `Settings` en `config/settings.py`.

### ❓ ¿Cómo añado un tipo de render nuevo?

1. Define un puerto (o reutiliza uno existente).
2. Implementa el adaptador (ej: `WebSocketParticlesAdapter`).
3. En tu plugin, decide qué adaptador crear según `context.settings.render.provider`.

### ❓ ¿Puedo correr dos juegos simultáneamente?

Sí. Registra ambos plugins y modifica `Container.create_game` para devolver
una lista, o crea un `MultiGame` que componga ambos. **5.4 lo explora.**

### ❓ ¿Dónde van los assets (imágenes, sonidos)?

```
assets/
└── tu_juego/
    ├── sprite.png
    └── sound.wav
```

Referéncialos con `Path(__file__).parent / "assets"` y usa `importlib.resources`
si empaquetas como librería.

### ❓ ¿Cómo depuro mi juego?

1. Añade `logger.debug(...)` en puntos clave.
2. Corre con `LOG_LEVEL=DEBUG python -m app.main`.
3. Usa `RENDER_DEBUG_OVERLAY=true` para ver el esqueleto superpuesto.

### ❓ ¿Cómo testeo sin cámara real?

Usa `POSE_PROVIDER=mock RENDER_PROVIDER=mock` y `ENVIRONMENT=testing`.
El mock de pose devuelve landmarks fijos.

### ❓ ¿Qué pasa si mi juego falla?

El `run_async` debe:
- Capturar `asyncio.CancelledError` y re-lanzarlo.
- Cerrar recursos en `finally`.
- No propagar excepciones de handlers de eventos (el bus las captura).

---

## Recursos adicionales

- **Contrato de puertos**: `docs/ports_contract.md`
- **Arquitectura general**: `architecture.md`
- **Ejemplos completos**: `app/plugins/particles_plugin.py`, `app/plugins/color_plugin.py`

---

## Contribuir

Si añades un juego útil, considera:

1. Escribir tests con cobertura > 80%.
2. Documentar reglas de negocio en docstrings.
3. Añadir un ejemplo en `docs/games/<tu_juego>.md`.

¡Bienvenido al ecosistema de plugins de Pose AR! 🎉

---

## 📋 Dónde guardarlo y cómo mantenerlo

### Ubicación recomendada

```
docs/
├── ports_contract.md          ← Ya existe
├── adding_a_game_plugin.md    ← Este nuevo
├── architecture.md            ← Documento general
└── games/                     ← Futuro: un .md por juego
    ├── particles.md
    ├── color.md
    └── saludo.md
```

### Cómo mantenerlo vivo

1. **Al añadir un puerto nuevo**: actualiza la sección "Referencia de puertos".
2. **Al cambiar `GameContext`**: actualiza la sección "Anatomía de un plugin".
3. **Al añadir un patrón**: añádelo a "Patrones recomendados".
4. **Al detectar una FAQ nueva**: añádela a "Preguntas frecuentes".
5. **Al añadir un juego de ejemplo**: considera mencionarlo como referencia.

**Regla**: cada PR que toque la arquitectura de plugins **debe actualizar este manual**.
