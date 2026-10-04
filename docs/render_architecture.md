# Arquitectura de Render

> **Estado**: Propuesta / Borrador
> **Fecha**: [fecha]
> **Autores**: MAuricio Villegas
> **Revisores**: [pendiente]

---

## 📌 Contexto

El proyecto tiene un **sistema de render** con las siguientes características:

- **Múltiples juegos** (particles, color, gestures, + futuros).
- **Múltiples tipos de visualización**:
  - Fondo de color sólido.
  - Sistema de partículas.
  - HUD (puntos, vidas, timer).
  - Overlays de debug (esqueleto de pose, FPS).
- **Arquitectura hexagonal**: dominio no depende de pygame ni de detalles de infraestructura.
- **Plugins intercambiables**: cada juego es un plugin autocontenido.

### Problema

El diseño actual mezcla **responsabilidades de render** en pocos componentes:

- `PygameParticlesAdapter`: dibuja partículas.
- `PygameColorAdapter`: dibuja fondo.
- `PoseDebugOverlay`: **decorador** que superpone el esqueleto.

**Problemas detectados**:

1. **Puertos específicos** (`ParticlesRenderPort`, `ColorRenderPort`) que **no se reutilizan** cuando un juego combina varias capacidades.
2. **Decoradores de overlay** que requieren **N variantes** (una por juego), con `hasattr` y `Protocol` complejo.
3. **Imposibilidad de componer** capas visuales limpiamente.
4. **Dificultad para testear** capacidades individuales.

---

## 🎯 Decisión

Se adopta el **modelo de "capacidades componibles + SceneManager"**:

1. **Capacidades de render**: puertos pequeños que describen **una sola cosa** que un renderer sabe hacer.
2. **SceneManager**: componente que **compone** varias capacidades sobre una misma ventana.
3. **Overlays**: elementos **opcionales** de la escena (no decoradores) para debug o efectos visuales.

---

## 🏛️ Arquitectura

### 🎨 Capacidades de render

Cada capacidad es un **puerto pequeño, tipado y con una sola responsabilidad**:

| Capacidad | Puerto | Métodos |
|-----------|--------|---------|
| **Color** | `ColorRenderPort` | `set_color`, `render_color` |
| **Particles** | `ParticlesRenderPort` | `set_particles`, `render_particles` |
| **HUD** | `HudRenderPort` | `set_hud`, `render_hud` |
| **Overlay** | `OverlayPort` | `draw(surface)` |

**Contrato general** (patrón `set_* → render_*`):

```python
class ColorRenderPort(ABC):
    @abstractmethod
    def set_color(self, color: RGBColor) -> None:
        """Declara el color actual. Sin dibujar."""

    @abstractmethod
    def render_color(self) -> None:
        """Dibuja el color declarado."""

    @abstractmethod
    def close(self) -> None: ...


class ParticlesRenderPort(ABC):
    @abstractmethod
    def set_particles(self, particles: list[Particle]) -> None: ...

    @abstractmethod
    def render_particles(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class HudRenderPort(ABC):
    @abstractmethod
    def set_hud(
        self,
        score: int,
        rounds: int,
        timer: float,
        extra: dict[str, str] | None = None,
    ) -> None: ...

    @abstractmethod
    def render_hud(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class OverlayPort(ABC):
    @abstractmethod
    def draw(self, surface: Any) -> None:
        """Dibuja el overlay sobre la superficie."""

    @abstractmethod
    def close(self) -> None: ...
```

**Nota**: los métodos se dividen en **`set_*`** (declarar qué dibujar) y **`render_*`** (ejecutar el dibujo). Esto permite:

- **Declarar sin dibujar** (útil para tests).
- **Dibujar sin redeclarar**.
- **Composición limpia** en el SceneManager.

### 🎬 SceneManager

Componente que **compone** varias capacidades sobre una ventana:

```python
class ScenePort(ABC):
    """Contrato del SceneManager."""

    @abstractmethod
    def add_capability(self, capability: object) -> None:
        """Registra una capacidad (color, particles, hud, ...)."""

    @abstractmethod
    def add_overlay(self, overlay: OverlayPort) -> None:
        """Registra un overlay (debug, efectos)."""

    @abstractmethod
    def render_frame(self, landmarks: list[PoseLandmark]) -> None:
        """Renderiza un frame completo (capacidades + overlays)."""

    @abstractmethod
    def close(self) -> None: ...
```

**Flujo de `render_frame`**:

```
1. Para cada capacidad registrada:
   - Llamar a `render_<capacity>()`

2. Para cada overlay registrado:
   - Llamar a `overlay.draw(surface)`

3. Hacer flush final (pygame.display.flip)
```

**Nota**: `landmarks` se pasa a `render_frame` para que los overlays que dependen de pose (ej: esqueleto) puedan usarlos. Los overlays no necesitan "suscribirse"; **el SceneManager les pasa los landmarks**.

### 🖼️ Overlays

Los overlays son **elementos de la escena** que se dibujan **encima** de las capacidades:

| Overlay | Función |
|---------|---------|
| `PoseOverlay` | Dibuja el esqueleto de pose |
| `FpsOverlay` | Dibuja FPS actuales |
| `DebugGridOverlay` | Dibuja una grilla de referencia |
| `BoundingBoxOverlay` | Dibuja cajas de landmarks |

**Ventaja clave**: **UN solo `PoseOverlay`** funciona en **todos** los juegos. No hay decoradores específicos ni variantes N×M.

---

## 📂 Estructura de carpetas

```
domain/
├── ports/
│   └── render/
│       ├── __init__.py
│       ├── color_render_port.py         # ColorRenderPort
│       ├── particles_render_port.py     # ParticlesRenderPort
│       ├── hud_render_port.py           # HudRenderPort
│       ├── overlay_port.py              # OverlayPort
│       └── scene_port.py                # ScenePort
│
└── games/
    └── particles/
        ├── main.py                      # ParticlesGame
        ├── state.py                     # ParticlesState
        └── plugin.py                    # ParticlesPlugin (self-contained)

adapters/
└── render/
    ├── pygame_base.py                   # PygameBaseWindow (ventana + eventos)
    ├── pygame_color.py                  # PygameColorRenderer
    ├── pygame_particles.py              # PygameParticlesRenderer
    ├── pygame_hud.py                    # PygameHudRenderer
    ├── pygame_scene.py                  # PygameSceneManager
    └── overlays/
        ├── pose_overlay.py              # PoseOverlay
        └── fps_overlay.py               # FpsOverlay
```

**Nota**: `plugin.py` vive dentro de `domain/games/<game>/`, y el **registro central** sigue en `app/plugins/__init__.py`.

---

## 🔄 Ejemplo: Juego "Touching"

Vamos a mostrar cómo se vería el juego de "tocar N partículas" con esta arquitectura.

### Estado del juego

```python
# domain/games/touching/state.py

@dataclass
class TouchingState:
    particles: list[Particle] = field(default_factory=list)
    score: int = 0
    rounds: int = 0
    timer: float = 0.0
    background_color: RGBColor = RGBColor(0, 0, 0)

    def background_for_score(self) -> RGBColor:
        """Regla de negocio: color según puntos."""
        if self.score <= 0:
            return RGBColor(0, 0, 0)       # negro
        if self.score == 1:
            return RGBColor(128, 128, 128) # gris
        if self.score == 2:
            return RGBColor(0, 0, 255)     # azul
        return RGBColor(255, 100, 0)       # cálido
```

### El juego

```python
# domain/games/touching/main.py

class TouchingGame:
    def __init__(
        self,
        camera: CameraPort,
        pose_estimator: PoseEstimatorPort,
        scene: ScenePort,
        color_capability: ColorRenderPort,
        particles_capability: ParticlesRenderPort,
        hud_capability: HudRenderPort,
        state: TouchingState,
        event_bus: EventBusPort,
    ):
        ...
        # Registra capacidades en la escena
        scene.add_capability(color_capability)
        scene.add_capability(particles_capability)
        scene.add_capability(hud_capability)

    async def run_async(self, should_stop=None):
        while not should_stop():
            # 1. Lógica del juego
            frame = await self._get_frame()
            landmarks = await self._get_landmarks(frame)
            self._update_state(landmarks)

            # 2. Declara qué dibujar
            self._color_capability.set_color(self._state.background_color)
            self._particles_capability.set_particles(self._state.particles)
            self._hud_capability.set_hud(
                score=self._state.score,
                rounds=self._state.rounds,
                timer=self._state.timer,
            )

            # 3. Renderiza el frame completo
            self._scene.render_frame(landmarks)
```

### El plugin

```python
# domain/games/touching/plugin.py

class TouchingPlugin(GamePlugin):
    @property
    def game_id(self) -> str:
        return "touching"

    @property
    def display_name(self) -> str:
        return "Touching Game"

    def create_state(self) -> GameStatePort:
        return TouchingState()

    def create_game(self, context: GameContext) -> GameProtocol:
        # 1. Crea la ventana Pygame
        window = PygameWindow(
            width=context.settings.render.width,
            height=context.settings.render.height,
            title="Touching Game",
        )

        # 2. Crea las capacidades
        color_capability = PygameColorRenderer(window)
        particles_capability = PygameParticlesRenderer(window)
        hud_capability = PygameHudRenderer(window)

        # 3. Crea overlays opcionales
        overlays = []
        if context.settings.render.debug_overlay:
            overlays.append(PoseOverlay(window))
            overlays.append(FpsOverlay(window))

        # 4. Crea el SceneManager y registra capacidades + overlays
        scene = PygameSceneManager(
            window=window,
            capabilities=[
                color_capability,
                particles_capability,
                hud_capability,
            ],
            overlays=overlays,
        )

        # 5. Crea el juego
        return TouchingGame(
            camera=context.camera,
            pose_estimator=context.pose_estimator,
            scene=scene,
            color_capability=color_capability,
            particles_capability=particles_capability,
            hud_capability=hud_capability,
            state=TouchingState(),
            event_bus=context.event_bus,
        )
```

**Observaciones clave**:
- El **plugin** es el único que conoce **Pygame**.
- El **juego** solo conoce los **puertos** (capacidades + escena).
- Los **overlays** se registran si `debug_overlay` está activo.
- El juego **no sabe** si hay overlays activos.

---

## 📊 Comparación con el diseño anterior

| Aspecto | Anterior | Nuevo |
|---------|----------|-------|
| **Puertos** | Específicos por juego | Capacidades reutilizables |
| **Overlay de pose** | N decoradores (uno por juego) | **1 `PoseOverlay`** |
| **Añadir capacidad visual** | Nuevo decorador + nuevo puerto | Nueva capacidad (1 archivo) |
| **Componer capas** | Decoradores anidados | Lista de capacidades |
| **Testear capacidad** | Requiere mock del juego | Test aislado con `Surface` fake |
| **Type-safety** | Trucos con `Protocol` + `hasattr` | Fuerte con puertos específicos |
| **Añadir juego nuevo** | Tocar N archivos | 1 carpeta + registro |
| **Extensibilidad** | Limitada | Alta |

---

## 🎯 Principios de diseño aplicados

### 1. SRP (Single Responsibility Principle)

Cada capacidad hace **una cosa**:
- Color: pinta fondo.
- Particles: dibuja partículas.
- Hud: dibuja HUD.
- Overlay: superpone elementos.

### 2. OCP (Open/Closed Principle)

- **Abierto a extensión**: añadir `TextCapacity`, `SpriteCapacity`, etc.
- **Cerrado a modificación**: no tocas las capacidades existentes.

### 3. ISP (Interface Segregation Principle)

Puertos **pequeños y específicos**. Un juego **solo implementa lo que necesita**.

### 4. DIP (Dependency Inversion Principle)

El juego depende de **puertos abstractos**, no de Pygame.

### 5. Composición sobre herencia

El `SceneManager` **compone** capacidades. No hay jerarquías profundas.

---

## 🔧 Patrón `set_*` + `render_*`

**¿Por qué dos métodos y no uno?**

**Un método** (`render_particles(particles)`) mezcla **declaración** y **ejecución**.

**Dos métodos** (`set_particles` + `render_particles`) separan:

- **Declarar** qué dibujar (puede venir de lógica del juego).
- **Ejecutar** el dibujo (agrupado por el SceneManager).

**Ventajas**:
1. **Tests**: puedes verificar "qué se declaró" sin llamar a pygame.
2. **Composición**: el SceneManager llama `render_*` en **orden controlado**.
3. **Optimización**: puedes cambiar el orden de render sin tocar el juego.
4. **Debugging**: log de "qué se declaró" vs "qué se dibujó".

**Trade-off**: más métodos por capacidad. Aceptable.

---

## 🧪 Testing

### Test de capacidad (aislado)

```python
def test_color_capability_renders_color():
    surface = fake_surface(800, 600)
    renderer = PygameColorRenderer(surface)

    renderer.set_color(RGBColor(255, 0, 0))
    renderer.render_color()

    assert surface.was_filled_with((255, 0, 0))
```

### Test de overlay (aislado)

```python
def test_pose_overlay_draws_landmarks():
    surface = fake_surface(800, 600)
    overlay = PoseOverlay(surface)

    landmarks = [PoseLandmark(0.5, 0.5, 0.0, 1.0, "nose")]
    overlay.draw(surface, landmarks=landmarks)

    assert surface.was_drawn_at((400, 300))
```

### Test de juego (integración con mocks)

```python
def test_touching_game_renders_all_capabilities():
    mock_scene = MockSceneManager()
    mock_color = MockColorRenderer()
    mock_particles = MockParticlesRenderer()
    mock_hud = MockHudRenderer()

    game = TouchingGame(
        scene=mock_scene,
        color_capability=mock_color,
        particles_capability=mock_particles,
        hud_capability=mock_hud,
        ...
    )

    await game.run_async(should_stop=stop_after(3))

    assert mock_color.set_color_call_count > 0
    assert mock_particles.set_particles_call_count > 0
    assert mock_hud.set_hud_call_count > 0
    assert mock_scene.render_frame_call_count > 0
```

---

## 🔄 Ciclo de vida

```
1. Container construye la ventana y las capacidades.
2. Plugin registra capacidades + overlays en el SceneManager.
3. Juego:
   - Declara estado visual (`set_*`).
   - Llama `scene.render_frame(landmarks)`.
4. SceneManager:
   - Llama `render_*` de cada capacidad (en orden).
   - Llama `draw` de cada overlay.
   - Hace flush.
5. Al terminar:
   - SceneManager.close() cierra todas las capacidades y overlays.
```

---

## 🚧 Fuera de alcance (por ahora)

- **Animaciones**: las capacidades no manejan animaciones internas.
- **Transiciones**: cambios de escena complejos.
- **Shaders**: efectos visuales avanzados.
- **Post-procesamiento**: efectos full-screen.

Si en el futuro los necesitamos, se añaden como **capacidades nuevas**.

---

## 📈 Roadmap de implementación

1. **Definir puertos**: color, particles, hud, overlay, scene.
2. **Implementar capacidades Pygame**: `PygameColorRenderer`, `PygameParticlesRenderer`, `PygameHudRenderer`.
3. **Implementar SceneManager**: `PygameSceneManager`.
4. **Implementar overlays**: `PoseOverlay`, `FpsOverlay`.
5. **Migrar juegos**: `ParticlesGame`, `ColorGame`, `GesturesGame`.
6. **Migrar plugins**: a `domain/games/<game>/plugin.py`.
7. **Actualizar Container**.
8. **Actualizar tests**.

---

## ❓ Decisiones pendientes

- [ ] ¿El `ScenePort` vive en `domain/ports/render/` o en `domain/ports/scene/`?
- [ ] ¿Los overlays reciben `landmarks` por constructor o por `draw`?
- [ ] ¿La ventana (`PygameWindow`) es una capacidad más o algo aparte?
- [ ] ¿Los overlays deben poder ser dinámicos (añadir/quitar en runtime)?
- [ ] ¿Los `set_*` deben soportar "sin cambios" (evitar redibujar si no cambió)?
- [ ] ¿Cómo se maneja el `close()` en cadena?

---

## 📚 Referencias

- [Clean Architecture - Robert C. Martin]
- [Composable Architecture patterns]
- [Game Engine Architecture - Jason Gregory]
```
