# Contrato de Puertos - Pose AR App

> **Versión**: 0.8.0
> **Última actualización**: [fecha]
> **Estado**: Vivo (se actualiza con cada fase)

Este documento define los **contratos** de todos los puertos (interfaces) del dominio.

**Regla de oro**: si un adaptador implementa un puerto, debe cumplir **exactamente** este contrato. Si necesitas algo distinto, creas un puerto nuevo.

---

## 🧭 Índice de Puertos

### Puertos de Entrada (el dominio LEE del exterior)
- [CameraPort](#cameraPort)
- [CameraStatsPort](#cameraStatsPort)
- [PoseEstimatorPort](#poseEstimatorPort)

### Puertos de Salida — Render (el dominio ESCRIBE al exterior)
**Estado actual (nueva arquitectura):**
- [ColorRenderPort](#colorRenderPortNew)
- [ParticlesRenderPort](#particlesRenderPortNew)
- [HudRenderPort](#hudRenderPort)
- [OverlayPort](#overlayPort)
- [ScenePort](#scenePort)

**Estado histórico (🔴 eliminado en `feature/refactor/render-migrate-legacy`):**
- [BaseRenderPort (🔴 eliminado)](#baseRenderPort)
- [ParticlesRenderPort (legacy, 🔴 eliminado)](#particlesRenderPort)
- [ColorRenderPort (legacy, 🔴 eliminado)](#colorRenderPort)
- [LandmarkAwareRenderPort (🔴 eliminado)](#landmarkAwareRenderPort)

### Puertos de Estado
- [GameStatePort](#gameStatePort)

### Puertos de Comunicación
- [EventBusPort](#eventBusPort)

### Puertos de Autenticación
- [AuthPort](#authPort)

### Puertos de Repositorio
- [UserRepositoryPort](#userRepositoryPort)
- [IdentityRepositoryPort](#identityRepositoryPort)

---

## 🔌 Puertos de Entrada

<a name="cameraPort"></a>
### 📷 CameraPort

**Propósito**: Proporcionar frames de video al dominio, ocultando la fuente (webcam, archivo, stream RTSP, mock).

**Ubicación**: `domain/ports/camera_port.py`

**Quién lo usa**: `ParticlesGame`, `ColorGame`, `GesturesGame`.

#### Métodos

##### `start() -> None`

- **Propósito**: Iniciar la captura.
- **Precondición**: ninguno.
- **Postcondición**: el adaptador está listo para recibir `get_frame()`.
  En implementaciones con hilo de captura, la lectura del dispositivo ocurre
  en background.
- **Errores**:
  - `CameraNotAvailableError` si no puede acceder al dispositivo.
  - `CameraError` para otros fallos.

##### `stop() -> None`

- **Propósito**: Detener la captura y liberar recursos.
- **Precondición**: ninguno (idempotente).
- **Postcondición**: los recursos (cámara, hilos) están liberados. Si el
  adaptador usa un hilo de captura, `stop()` espera su finalización.

##### `get_frame() -> np.ndarray | None`

- **Propósito**: Obtener el último frame disponible.
- **Formato**: array numpy `(H, W, 3)` en **BGR** (OpenCV estándar).
- **Precondición**: `start()` fue llamado.
- **Postcondición**: devuelve un frame o `None` si no hay disponible.
- **Notas**:
  - **No bloquea**: devuelve el frame más reciente del buffer; no lee del
    dispositivo en la llamada.
  - Puede devolver el **mismo frame** varias veces si no ha llegado uno nuevo.
  - `WebcamAdapter` devuelve una **copia defensiva** del frame.
  - Puede devolver `None` transitoriamente (frame drop o cámara aún sin frames).

##### `is_running() -> bool`

- **Propósito**: Saber si la cámara está activa.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `WebcamAdapter` | ✅ Implementado | `adapters/camera/webcam_adapter.py` |
| `MockCameraAdapter` | ✅ Implementado | `adapters/mock/mock_camera.py` |
| `VideoFileAdapter` | ⏳ Planeado | (para replay/testing) |
| `RTSPAdapter` | ⏳ Futuro | (para streaming IP) |
| `DeepCameraAdapter` | ⏳ Futuro | `adapters/camera/deepcam_adapter.py` |

**Notas de implementación**:

- `WebcamAdapter` usa un **hilo de captura daemon** y un buffer de un frame:
  si el consumidor no llama a `get_frame()` a tiempo, el frame se sobrescribe.
- El formato de video se negocia con `CAMERA_FOURCC` (default `MJPG`); el
  adaptador loguea el FourCC real concedido por el dispositivo.

---

<a name="cameraStatsPort"></a>
### 📊 CameraStatsPort (opcional)

**Propósito**: Exponer métricas de captura sin ampliar `CameraPort`.

**Ubicación**: `domain/ports/camera_port.py`

**Quién lo usa**: diagnóstico y debug (no es dependencia de los juegos).

#### Métodos

##### `get_stats() -> dict`

- **Propósito**: Devolver un snapshot de las métricas de captura.
- **Contrato**:
  - No bloquea: toma las métricas bajo lock.
  - Las claves concretas pueden variar entre adaptadores.
  - `WebcamAdapter` publica: `fps_captura`, `fps_declarado`, `frames_leidos`,
    `frames_en_ventana`, `frames_entregados`, `width`, `height`, `fourcc` y
    `hilo_activo`.
- **Notas**:
  - Es un `Protocol` con `@runtime_checkable`: se puede detectar con
    `isinstance(camera, CameraStatsPort)` sin heredar de `CameraPort`.
  - No es obligatorio para todos los adaptadores de cámara.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `WebcamAdapter` | ✅ Implementado | `adapters/camera/webcam_adapter.py` |

---

<a name="poseEstimatorPort"></a>
### 🦾 PoseEstimatorPort

**Propósito**: Extraer landmarks de pose humana de un frame, ocultando el modelo (Mediapipe, YOLO, mock).

**Ubicación**: `domain/ports/pose_estimator_port.py`

**Quién lo usa**: `ParticlesGame`, `ColorGame`, `GesturesGame`.

#### Métodos

##### `estimate(frame: np.ndarray) -> list[PoseLandmark]`

- **Propósito**: Estimar landmarks de pose en un frame.
- **Precondición**: `frame` no vacío, formato BGR `(H, W, 3)`.
- **Postcondición**: lista de landmarks en **coordenadas normalizadas (0-1)**.
- **Errores**:
  - `PoseEstimationError` si el modelo falla catastróficamente.
  - Devuelve `[]` si no hay persona detectada (NO es error).
- **Notas**:
  - Los landmarks con `visibility < 0.5` **pueden** ser omitidos por el adaptador.
  - El número de landmarks puede variar entre adaptadores (Mediapipe: 33, YOLO: 17).

##### `get_landmark_names() -> list[str]`

- **Propósito**: Saber qué nombres de landmarks soporta el adaptador.

##### `close() -> None`

- **Propósito**: Liberar recursos del modelo (GPU, memoria).
- **Precondición**: ninguno (idempotente).

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `MediapipeAdapter` | ✅ Implementado | `adapters/pose/mediapipe_adapter.py` |
| `MockPoseAdapter` | ✅ Implementado | `adapters/mock/mock_pose.py` |
| `YOLOPoseAdapter` | ⏳ Futuro | (más rápido en GPU) |

---

## 🔌 Puertos de Salida — Render

<a name="baseRenderPort"></a>
### 🎨 BaseRenderPort (🔴 eliminado)

> 🔴 **ELIMINADO** en `feature/refactor/render-migrate-legacy`. Los puertos nuevos viven en `domain/ports/render/`.
>
> _Contenido histórico: se mantiene solo como referencia._

**Propósito**: Operaciones comunes a **cualquier** renderizador.

**Ubicación**: 🔴 `domain/ports/render_port.py` (archivo eliminado)

**Quién lo usa**: indirectamente los juegos.

#### Métodos

##### `close() -> None`

- **Propósito**: Cerrar y liberar recursos.
- **Contrato**: idempotente.

##### `__enter__() / __exit__()`

- **Propósito**: Soportar `with renderer as r:`.
- **Contrato**: `__exit__` llama a `close()`.

> **Nota post-refactor** (`feature/fix#pygame-single-window`): `show()` fue **eliminado** del contrato. Nadie lo llamaba en producción: el ciclo de vida de la ventana lo gestiona el bootstrap del plugin + `SceneManager`. Si necesitas mantener una ventana abierta, usa el loop del juego (`run_async`), no un método del puerto.

---

<a name="particlesRenderPort"></a>
### ✨ ParticlesRenderPort (🔴 legacy, eliminado)

> 🔴 **ELIMINADO** en `feature/refactor/render-migrate-legacy`. El puerto nuevo está en `domain/ports/render/particles_render_port.py` (`set_particles` + `render_particles()` + `render()` + `close()`).
>
> _Contenido histórico: se mantiene solo como referencia._

**Propósito**: Renderizar un sistema de partículas.

**Herencia**: `BaseRenderPort` (eliminado)

**Quién lo usa**: 🔴 **nadie** (histórico).

#### Métodos

##### `render_particles(particles: list[Particle]) -> None`

- **Propósito**: Dibujar las partículas en el canvas.
- **Contrato**: puede ser llamada con lista vacía. No debe bloquear.
- **Notas**: el adaptador puede omitir partículas muertas (`life <= 0.01`).

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `PygameParticlesAdapter` | 🔴 Eliminado | (nunca existió como archivo; el adapter real fue `PygameParticlesRenderer` en `adapters/render/pygame_particles.py`, que implementa la **nueva** `ParticlesRenderPort` en `domain/ports/render/`) |
| `MockParticlesRenderAdapter` | 🔴 Ya no implementa el puerto legacy | Migrado a la nueva `ParticlesRenderPort` (`adapters/mock/mock_render.py`) |
| `NullParticlesRenderAdapter` | ⏳ Planeado | (headless) |
| `WebSocketParticlesAdapter` | ⏳ Futuro | (frontend web) |

---

<a name="colorRenderPort"></a>
### 🌈 ColorRenderPort (🔴 legacy, eliminado)

> 🔴 **ELIMINADO** en `feature/refactor/render-migrate-legacy`. El puerto nuevo está en `domain/ports/render/color_render_port.py` (`set_color` + `render_color()` + `render()` + `close()`).
>
> _Contenido histórico: se mantiene solo como referencia._

**Propósito**: Renderizar un fondo de color + esqueleto superpuesto.

**Herencia**: `BaseRenderPort` (eliminado)

**Quién lo usa**: 🔴 **nadie** (histórico).

#### Métodos

##### `render_background(color: RGBColor, landmarks: list[PoseLandmark]) -> None`

- **Propósito**: Pintar el canvas con `color` y dibujar el esqueleto si hay landmarks.
- **Contrato**: `landmarks` puede estar vacía.
- **Notas**: los landmarks con `visibility < 0.5` no se dibujan.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `PygameColorAdapter` | 🔴 Eliminado | (era `adapters/render/pygame_color_adapter.py`; reemplazado por `PygameColorRenderer` + `PygameSceneManager`) |
| `MockColorRenderAdapter` | 🔴 Ya no implementa el puerto legacy | Migrado a la nueva `ColorRenderPort` (`adapters/mock/mock_render.py`) |
| `NullColorRenderAdapter` | ⏳ Planeado | (headless) |
| `WebSocketColorAdapter` | ⏳ Futuro | (frontend web) |

---

<a name="landmarkAwareRenderPort"></a>
### 🎯 LandmarkAwareRenderPort (🔴 eliminado)

> 🔴 **ELIMINADO** en `feature/refactor/render-migrate-legacy`. En la nueva arquitectura, los landmarks llegan al `SceneManager.render_frame(landmarks)` y este los pasa a `overlay.draw(surface, landmarks)`.

**Propósito**: Puerto opcional para renderers que quieren recibir landmarks
además de su input principal (uso: overlay de debug).

**Ubicación**: 🔴 `domain/ports/render_port.py` (archivo eliminado)

**Quién lo usa**: 🔴 **nadie en producción**. Antes lo usaba `PoseDebugOverlay`, eliminado en `feature/fix#pygame-single-window` (reemplazado por `OverlayPort`/`PoseOverlay`). Ver §5.11 de `system_learning.md`.

#### Métodos

##### `update_landmarks(landmarks: list[PoseLandmark]) -> None`

- **Propósito**: Recibir los landmarks actuales para el próximo render.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `MockParticlesRenderAdapter` | 🔴 Ya no implementa el puerto legacy | Migrado a la nueva arquitectura (`adapters/mock/mock_render.py`) |
| `MockColorRenderAdapter` | 🔴 Ya no implementa el puerto legacy | Migrado a la nueva arquitectura (`adapters/mock/mock_render.py`) |
| `PoseDebugOverlay` | 🔴 Eliminado | (era `adapters/render/decorators/pose_debug_overlay.py`, borrado en `feature/fix#pygame-single-window`) |

> **Nota**: en la nueva arquitectura, el "mixin" opcional se reemplaza por `OverlayPort` (`domain/ports/render/overlay_port.py`). Los overlays **no** reciben landmarks por un mixin: el `SceneManager.render_frame(landmarks)` los pasa a `ov.draw(surface, landmarks)`.

---

### 🟢 NUEVA ARQUITECTURA DE RENDER (implementada)

> ✅ **Estado**: implementada en `feature/refactor/render-migrate-legacy`. Es la única arquitectura de render; los puertos legacy fueron eliminados.
>
> **Referencia**: `docs/render_architecture.md`.

La nueva arquitectura sigue el patrón **"capacidades componibles + SceneManager"**:

- **Capacidades**: puertos pequeños, tipados, con **una sola responsabilidad**.
- **Patrón `set_*` + `render_*`**: separa "declarar qué dibujar" de "dibujar".
- **SceneManager**: compone capacidades + overlays sobre una misma ventana.
- **Overlays**: elementos visuales superpuestos (debug, efectos).

<a name="colorRenderPortNew"></a>
#### 🌈 ColorRenderPort (nuevo)

**Propósito**: Capacidad de pintar un fondo de color sólido.

**Ubicación**: `domain/ports/render/color_render_port.py`

#### Métodos

##### `set_color(color: RGBColor) -> None`

- **Propósito**: Declarar el color actual (sin dibujar).

##### `render_color() -> None`

- **Propósito**: Dibujar el color declarado.

##### `close() -> None`

- **Propósito**: Liberar recursos (idempotente).

---

<a name="particlesRenderPortNew"></a>
#### ✨ ParticlesRenderPort (nuevo)

**Propósito**: Capacidad de dibujar un sistema de partículas.

**Ubicación**: `domain/ports/render/particles_render_port.py`

#### Métodos

##### `set_particles(particles: list[Particle]) -> None`

- **Propósito**: Declarar las partículas a dibujar (sin dibujar).

##### `render_particles() -> None`

- **Propósito**: Dibujar las partículas declaradas.

##### `close() -> None`

- **Propósito**: Liberar recursos (idempotente).

---

<a name="hudRenderPort"></a>
#### 📊 HudRenderPort

**Propósito**: Capacidad de dibujar un HUD (puntos, rondas, timer).

**Ubicación**: `domain/ports/render/hud_render_port.py`

#### Métodos

##### `set_hud(score: int, rounds: int, timer: float, extra: dict[str, str] | None = None) -> None`

- **Propósito**: Declarar los valores actuales del HUD.
- **Contrato**: `extra` permite campos adicionales específicos del juego.

##### `render_hud() -> None`

- **Propósito**: Dibujar el HUD.

##### `close() -> None`

- **Propósito**: Liberar recursos (idempotente).

---

<a name="overlayPort"></a>
#### 🖼️ OverlayPort

**Propósito**: Elemento visual superpuesto (debug, efectos).

**Ubicación**: `domain/ports/render/overlay_port.py`

**Nota**: a diferencia de las capacidades, los overlays **reciben** la superficie
y los landmarks en `draw`. Esto permite reutilizarlos en cualquier juego.

#### Métodos

##### `draw(surface: Any, landmarks: list[PoseLandmark]) -> None`

- **Propósito**: Dibujar el overlay sobre la superficie.

##### `close() -> None`

- **Propósito**: Liberar recursos (idempotente).

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `PoseOverlay` | ⏳ Pendiente | `adapters/render/overlays/pose_overlay.py` |
| `FpsOverlay` | ⏳ Pendiente | `adapters/render/overlays/fps_overlay.py` |

---

<a name="scenePort"></a>
#### 🎬 ScenePort

**Propósito**: Composición de capacidades + overlays sobre una ventana.

**Ubicación**: `domain/ports/render/scene_port.py`

#### Métodos

##### `add_capability(capability: object) -> None`

- **Propósito**: Registrar una capacidad (color, particles, hud, ...).

##### `add_overlay(overlay: OverlayPort) -> None`

- **Propósito**: Registrar un overlay.

##### `render_frame(landmarks: list[PoseLandmark]) -> None`

- **Propósito**: Renderizar un frame completo.
- **Contrato**:
  - Llama a `render_*` de cada capacidad **en orden de registro**.
  - Llama a `draw(surface, landmarks)` de cada overlay.
  - Hace flush final.

##### `close() -> None`

- **Propósito**: Cerrar todas las capacidades y overlays (idempotente).

---

## 🔌 Puertos de Estado

<a name="gameStatePort"></a>
### 🔗 GameStatePort

**Propósito**: Estado consultable de un juego (para la API, WebSocket, persistencia).
Cada juego implementa **su propio** estado.

**Ubicación**: `domain/state/game_state_port.py`

**Quién lo usa**: `ParticlesState`, `ColorState`, `GesturesState`, la API.

#### Métodos

##### `game_id -> str` (property)

- **Propósito**: Identificador único del juego.
- **Convención**: snake_case, sin espacios.

##### `snapshot() -> dict[str, Any]`

- **Propósito**: Snapshot completo serializable (JSON-friendly).
- **Contrato**:
  - Retorna una COPIA, no referencias mutables.
  - No incluye datos no serializables.
  - Debe ser rápido (<1ms).

##### `stats() -> dict[str, Any]`

- **Propósito**: Solo estadísticas (más ligero que snapshot).

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `ParticlesState` | ✅ Implementado | `domain/games/particles/state.py` |
| `ColorState` | ✅ Implementado | `domain/games/color/state.py` |
| `GesturesState` | ✅ Implementado | `domain/games/gestures/state.py` |

---

## 🔌 Puertos de Comunicación

<a name="eventBusPort"></a>
### 📡 EventBusPort

**Propósito**: Bus de eventos async para comunicación desacoplada entre
componentes (juegos, API, sistema).

**Ubicación**: `domain/ports/event_bus_port.py`

**Quién lo usa**: `ParticlesGame`, `ColorGame`, `GesturesGame`, `FastAPIAdapter`.

#### Métodos

##### `subscribe(event_type: type[DomainEvent], handler: EventHandler) -> None`

- **Propósito**: Suscribir un handler async a un tipo de evento.
- **Contrato**: si el mismo handler se suscribe dos veces, no se duplica.

##### `unsubscribe(event_type: type[DomainEvent], handler: EventHandler) -> None`

- **Propósito**: Desuscribir un handler.

##### `async publish(event: DomainEvent) -> None`

- **Propósito**: Publicar un evento a todos los suscriptores.
- **Contrato**:
  - Los handlers se ejecutan en orden de suscripción.
  - Si un handler falla, se loggea y se continúa con el siguiente.
  - Thread-safe.

##### `clear() -> None`

- **Propósito**: Eliminar todos los suscriptores (útil en tests).

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `AsyncEventBus` | ✅ Implementado | `infrastructure/events/async_event_bus.py` |
| `SyncEventBus` | ⏳ Deprecado | `infrastructure/events/sync_event_bus.py` |

---

## 🔌 Puertos de Autenticación

<a name="authPort"></a>
### 🔐 AuthPort

**Propósito**: Autenticar credenciales y devolver el `User` correspondiente.

**Ubicación**: `domain/ports/auth_port.py`

**Quién lo usa**: `adapters/api/auth_routes.py`.

#### Métodos

##### `authenticate(username: str, password: str) -> User | None`

- **Propósito**: Validar credenciales.
- **Contrato**: devuelve `User` si son válidas, `None` si no.

##### `get_user(username: str) -> User | None`

- **Propósito**: Obtener un `User` sin validar password.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `CredentialsAuthProvider` | ✅ Implementado | `adapters/auth/credentials_auth_provider.py` |
| `GoogleAuthProvider` | ⏳ Futuro | (OAuth) |

---

## 🔌 Puertos de Repositorio

<a name="userRepositoryPort"></a>
### 👤 UserRepositoryPort

**Propósito**: CRUD de usuarios (perfiles). **NO** maneja credenciales
(eso es `IdentityRepositoryPort`).

**Ubicación**: `domain/ports/user_repository_port.py`

**Quién lo usa**: endpoints de usuarios (`/users`), bootstrap de usuarios.

#### Métodos

##### `get_by_id(user_id: str) -> User | None`

- **Propósito**: Obtener un usuario por id.

##### `get_by_username(username: str) -> User | None`

- **Propósito**: Obtener un usuario por username.

##### `create(user: User) -> User`

- **Propósito**: Crear un usuario.
- **Errores**: `ValueError` si el username ya existe.

##### `update(user: User) -> User`

- **Propósito**: Actualizar un usuario.
- **Errores**: `ValueError` si el usuario no existe.

##### `delete(user_id: str) -> None`

- **Propósito**: Eliminar un usuario (idempotente).

##### `list_all() -> list[User]`

- **Propósito**: Listar todos los usuarios.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `InMemoryUserRepository` | ✅ Implementado | `adapters/auth/in_memory_user_repository.py` |
| `SqliteUserRepository` | ⏳ Futuro | (persistencia) |

---

<a name="identityRepositoryPort"></a>
### 🔑 IdentityRepositoryPort

**Propósito**: Credenciales (password hashes, tokens OAuth).

**Ubicación**: `domain/ports/identity_repository_port.py`

**Quién lo usa**: `CredentialsAuthProvider`, endpoints de cambio de password.

#### Métodos

##### `get_by_provider(provider: str, provider_user_id: str) -> Identity | None`

- **Propósito**: Obtener identidad por (provider, provider_user_id).
- **Ejemplo**: `get_by_provider("password", "admin")`.

##### `get_by_user_id(user_id: str) -> list[Identity]`

- **Propósito**: Listar todas las identidades de un usuario.

##### `create(identity: Identity) -> Identity`

- **Propósito**: Crear una identidad.
- **Errores**: `ValueError` si ya existe.

##### `update(identity: Identity) -> Identity`

- **Propósito**: Actualizar una identidad.

##### `delete(user_id: str, provider: str) -> None`

- **Propósito**: Eliminar una identidad (idempotente).

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `InMemoryIdentityRepository` | ✅ Implementado | `adapters/auth/in_memory_identity_repository.py` |
| `SqliteIdentityRepository` | ⏳ Futuro | |

---

## 🧩 Contrato de Datos Publicados por Cada Juego

> Esta sección documenta **qué keys específicas** publica cada juego en su `GameStatePort.snapshot()`.

### ParticlesGame

| Key | Tipo | Descripción |
|-----|------|-------------|
| `particles_count` | `int` | Número total de partículas activas |
| `particles_sample` | `list[dict]` | Muestra de partículas (máx 10) |
| `landmarks_count` | `int` | Número de landmarks visibles |
| `frame_count` | `int` | Frames procesados |

**Eventos que publica**:
- `PoseUpdated`, `PoseLost`.
- `GameResetRequested` (recibe).

**Comandos que entiende (vía eventos)**:
- `GameResetRequested` → vacía las partículas.

### ColorGame

| Key | Tipo | Descripción |
|-----|------|-------------|
| `background_color` | `str` | Color de fondo (hex) |
| `current_palette` | `str` | Nombre de la paleta (`"fire"`, `"ocean"`, ...) |
| `landmarks_count` | `int` | Landmarks visibles |
| `frame_count` | `int` | Frames procesados |

**Eventos que recibe**:
- `PaletteChangeRequested` (payload: `{"palette": str}`).

### GesturesGame

| Key | Tipo | Descripción |
|-----|------|-------------|
| `active_gestures` | `list[str]` | Gestos activos en el frame actual |
| `activation_counts` | `dict[str, int]` | Cuenta de activaciones por gesto |
| `frame_count` | `int` | Frames procesados |

---

## 📋 Reglas Generales

1. **Los puertos son contratos, no sugerencias**. Un adaptador que no cumpla el contrato es un bug.
2. **Los puertos no conocen implementaciones**. `CameraPort` no menciona OpenCV.
3. **Los puertos usan tipos del dominio** (`PoseLandmark`, `Particle`, `RGBColor`), no tipos HTTP ni de framework.
4. **Idempotencia**: `start()`, `stop()`, `close()` deben poder llamarse sin efectos adversos.
5. **Thread-safety**: todo puerto accedido desde varios threads debe ser thread-safe (ej: `GameStatePort`, `EventBusPort`).
6. **Patrón `set_*` + `render_*`** (nueva arquitectura de render): separa declaración de ejecución.

---

## 🔄 Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 0.4 | [fecha] | StatePort genérico (posteriormente eliminado) |
| 0.5.1 | [fecha] | Separación de `RenderPort` en `ParticlesRenderPort` y `ColorRenderPort` |
| 0.6.0 | [fecha] | 1) `StatePort` → `GameStatePort`. 2) Añadido `EventBusPort`. 3) Añadidos `AuthPort`, `UserRepositoryPort`, `IdentityRepositoryPort`. 4) Añadido `LandmarkAwareRenderPort` (eliminado en 0.8.0). 5) Nueva arquitectura de render (pendiente). |
| 0.7.0 | [fecha] | 1) Añadido `CameraStatsPort` (métricas opcionales). 2) `CameraPort.get_frame` documentado como no bloqueante y con copia defensiva en `WebcamAdapter`. 3) `WebcamAdapter`: hilo de captura y FourCC configurable (`CAMERA_FOURCC`). |
| 0.8.0 | [fecha] | 1) 🔴 Eliminados `BaseRenderPort`, `ParticlesRenderPort`/`ColorRenderPort` legacy, `LandmarkAwareRenderPort` y `render_port.py`. 2) Nueva arquitectura de render implementada (SceneManager + capacidades + overlays). 3) `ColorGame` y `GesturesGame` migrados. |

---

## 📝 Notas de Evolución

- **Cuando agregues un juego nuevo**: añade una sección en "Contrato de Datos Publicados".
- **Cuando refactorices un puerto**: incrementa versión y anota en changelog.
- **Si un adaptador necesita un método extra**: considera si es un nuevo puerto.
- **Nueva arquitectura de render**: los puertos `*RenderPort (actual)` serán reemplazados.
  El refactor se documenta en `docs/render_architecture.md`.

---

## 📚 Referencias Cruzadas

- `docs/render_architecture.md` — Diseño detallado de la nueva arquitectura de render.
- `docs/adding_a_game_plugin.md` — Guía para añadir juegos como plugin.
- `AGENTS.md` — Reglas del proyecto para herramientas automatizadas.
