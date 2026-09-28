# Contrato de Puertos - Pose AR App

> **Versión**: 0.5.1
> **Última actualización**: [fecha]
> **Estado**: Vivo (se actualiza con cada fase)

Este documento define los **contratos** de todos los puertos (interfaces) del dominio.

**Regla de oro**: si un adaptador implementa un puerto, debe cumplir **exactamente** este contrato. Si necesitas algo distinto, creas un puerto nuevo.

---

## 🧭 Índice de Puertos

### Puertos de Entrada (el dominio LEE del exterior)
- [CameraPort](#cameraPort)
- [PoseEstimatorPort](#poseEstimatorPort)

### Puertos de Salida (el dominio ESCRIBE al exterior)
- [BaseRenderPort](#baseRenderPort)
- [ParticlesRenderPort](#particlesRenderPort)
- [ColorRenderPort](#colorRenderPort)

### Puertos de Comunicación (estado compartido)
- [StatePort](#statePort)

---

## 🔌 Puertos de Entrada

<a name="cameraPort"></a>
### 📷 CameraPort

**Propósito**: Proporcionar frames de video al dominio, ocultando la fuente (webcam, archivo, stream RTSP, mock).

**Ubicación**: `domain/ports/camera_port.py`

**Quién lo usa**: `ParticlesGame`, `ColorGame`, cualquier caso de uso que procese video.

#### Métodos

##### `start() -> None`

- **Propósito**: Iniciar la captura.
- **Precondición**: ninguno.
- **Postcondición**: el adaptador está listo para recibir `get_frame()`.
- **Errores**:
  - `CameraNotAvailableError` si no puede acceder al dispositivo.
  - `CameraError` para otros fallos.

##### `stop() -> None`

- **Propósito**: Detener la captura y liberar recursos.
- **Precondición**: ninguno (idempotente).
- **Postcondición**: los recursos (cámara, hilos) están liberados.

##### `get_frame() -> Optional[np.ndarray]`

- **Propósito**: Obtener el último frame disponible.
- **Formato**: array numpy `(H, W, 3)` en **BGR** (OpenCV estándar).
- **Precondición**: `start()` fue llamado.
- **Postcondición**: devuelve un frame o `None` si no hay disponible.
- **Notas**:
  - Puede devolver el **mismo frame** varias veces si la cámara es más lenta que el procesamiento.
  - Puede devolver `None` transitoriamente (frame drop).

##### `is_running() -> bool`

- **Propósito**: Saber si la cámara está activa.
- **Uso**: el caso de uso puede decidir reintentar si está caída.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `WebcamAdapter` | ✅ Implementado | `adapters/camera/webcam_adapter.py` |
| `MockCameraAdapter` | ✅ Implementado | `adapters/mock/mock_camera.py` |
| `VideoFileAdapter` | ⏳ Planeado | (para replay/testing) |
| `RTSPAdapter` | ⏳ Futuro | (para streaming IP) |
| `DeepCameraAdapter` | ⏳ Futuro | (para Camaras de profundidad) `adapters/camera/deepcam_adapter.py`|

---

<a name="poseEstimatorPort"></a>
### 🦾 PoseEstimatorPort

**Propósito**: Extraer landmarks de pose humana de un frame, ocultando el modelo (Mediapipe, YOLO, mock).

**Ubicación**: `domain/ports/pose_estimator_port.py`

**Quién lo usa**: `ParticlesGame`, `ColorGame`.

#### Métodos

##### `estimate(frame: np.ndarray) -> List[PoseLandmark]`

- **Propósito**: Estimar landmarks de pose en un frame.
- **Precondición**: `frame` no vacío, formato BGR `(H, W, 3)`.
- **Postcondición**: lista de landmarks en **coordenadas normalizadas (0-1)**.
- **Errores**:
  - `PoseEstimationError` si el modelo falla catastróficamente.
  - Devuelve `[]` si no hay persona detectada (NO es error).
- **Notas**:
  - Los landmarks con `visibility < 0.5` **pueden** ser omitidos por el adaptador.
  - El número de landmarks puede variar entre adaptadores (Mediapipe: 33, YOLO: 17).

##### `get_landmark_names() -> List[str]`

- **Propósito**: Saber qué nombres de landmarks soporta el adaptador.
- **Uso**: para validar reglas de negocio o autocompletar.

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

## 🔌 Puertos de Salida

<a name="baseRenderPort"></a>
### 🎨 BaseRenderPort

**Propósito**: Operaciones comunes a **cualquier** renderizador (ventana, ventana emergente, WebSocket, headless).

**Ubicación**: `domain/ports/render_port.py`

**Quién lo usa**: indirectamente los juegos; cada juego usa un puerto específico que hereda de este.

#### Métodos

##### `show() -> None`

- **Propósito**: Mantener la visualización activa (bloqueante hasta cerrar).
- **Uso**: típicamente al final del juego o en un bucle de baja frecuencia.

##### `close() -> None`

- **Propósito**: Cerrar y liberar recursos.
- **Precondición**: ninguno (idempotente).
- **Postcondición**: recursos liberados.

##### `__enter__() / __exit__()`

- **Propósito**: Soportar `with renderer as r:`.
- **Contrato**: `__exit__` llama a `close()`.

---

<a name="particlesRenderPort"></a>
### ✨ ParticlesRenderPort

**Propósito**: Renderizar específicamente un **sistema de partículas**.

**Herencia**: `BaseRenderPort`

**Quién lo usa**: `ParticlesGame`.

#### Métodos propios

##### `render_particles(particles: List[Particle]) -> None`

- **Propósito**: Dibujar las partículas en el canvas/ventana.
- **Precondición**: `particles` puede estar vacía.
- **Postcondición**: la visualización está actualizada; **NO bloquea más de lo necesario** (idealmente < 16ms para 60 FPS).
- **Notas**:
  - Cada partícula tiene `x, y, life, size, color`.
  - El adaptador puede **ignorar partículas muertas** (`life <= 0.01`) para optimizar.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `PygameParticlesAdapter` | ⏳ A crear en 5.1 | `adapters/render/pygame_particles_adapter.py` |
| `MockParticlesRenderAdapter` | ⏳ A crear en 5.1 | `adapters/mock/mock_render.py` |
| `NullParticlesRenderAdapter` | ⏳ Planeado | (para modo headless) |
| `WebSocketParticlesAdapter` | ⏳ Futuro | (para frontend web) |

---

<a name="colorRenderPort"></a>
### 🌈 ColorRenderPort

**Propósito**: Renderizar un **fondo de color + esqueleto** superpuesto.

**Herencia**: `BaseRenderPort`

**Quién lo usa**: `ColorGame`.

#### Métodos propios

##### `render_background(color: RGBColor, landmarks: List[PoseLandmark]) -> None`

- **Propósito**: Pintar todo el canvas con `color` y dibujar el esqueleto si hay landmarks.
- **Precondición**: `color` es un RGBColor válido; `landmarks` puede estar vacía.
- **Postcondición**: visualización actualizada.
- **Notas**:
  - Los landmarks deben conectarse como esqueleto (hombros, codos, caderas, etc.).
  - Si un landmark tiene `visibility < 0.5`, **no** dibujarlo ni conectarlo.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `PygameColorAdapter` | ⏳ A crear en 5.1 | `adapters/render/pygame_color_adapter.py` |
| `MockColorRenderAdapter` | ⏳ A crear en 5.1 | `adapters/mock/mock_render.py` |
| `NullColorRenderAdapter` | ⏳ Planeado | (headless) |
| `WebSocketColorAdapter` | ⏳ Futuro | (frontend web) |

---

## 🔌 Puertos de Comunicación

<a name="statePort"></a>
### 🔗 StatePort

**Propósito**: Estado compartido entre el juego (productor) y consumidores externos (API, WebSocket, persistencia). Genérico: **no conoce juegos específicos**.

**Ubicación**: `domain/ports/state_port.py`

**Quién lo usa**: `ParticlesGame`, `ColorGame`, `FastAPIAdapter`.

#### Métodos de lectura (consumidores)

##### `get_snapshot() -> dict[str, Any]`

- **Propósito**: Snapshot completo serializable.
- **Contrato**: retorna un dict con al menos las claves `pose`, `game_data`, `stats`.
- **Garantía**: thread-safe; retorna copia, no referencia.

##### `get_stats() -> dict[str, Any]`

- **Propósito**: Solo estadísticas (más ligero que snapshot).
- **Contrato**: dict con `frames_processed`, `last_update`.

#### Métodos de publicación (juego)

##### `update_pose(landmarks: List[PoseLandmark]) -> None`

- **Propósito**: Publicar la última pose detectada.
- **Contrato**: thread-safe; el juego lo llama una vez por frame.

##### `update_game_data(key: str, value: Any) -> None`

- **Propósito**: Publicar cualquier dato específico del juego.
- **Contrato**: thread-safe; el juego decide qué keys usa.
- **Convención**:
  - `ParticlesGame` publica: `"particles"`, `"particles_count"`.
  - `ColorGame` publica: `"background_color"`, `"current_palette"`.

##### `increment_frames() -> None`

- **Propósito**: Incrementar contador de frames procesados.
- **Contrato**: thread-safe.

#### Métodos de comando (consumidores → juego)

##### `enqueue_command(action: str, payload: dict[str, Any]) -> None`

- **Propósito**: Encolar un comando para que el juego lo procese.
- **Contrato**: thread-safe; el juego decide qué comandos entiende.
- **Convención**:
  - `ParticlesGame` entiende: `"reset_particles"`.
  - `ColorGame` entiende: `"change_palette"` (payload: `{"palette": str}`).
  - **Comandos desconocidos se ignoran silenciosamente**.

##### `drain_commands() -> List[Command]`

- **Propósito**: Consumir todos los comandos pendientes (y vaciar la cola).
- **Contrato**: thread-safe; el juego llama al inicio de cada frame.

#### Adaptadores conocidos

| Adaptador | Estado | Ubicación |
|-----------|--------|-----------|
| `AppState` | ✅ Implementado | `app/state.py` |
| `RedisStateAdapter` | ⏳ Futuro | (para múltiples procesos) |

---

## 🧩 Contrato de Datos Publicados por Cada Juego

> Esta sección documenta **qué keys específicas** publica cada juego en `state.game_data`.

### ParticlesGame

| Key | Tipo | Descripción |
|-----|------|-------------|
| `particles` | `List[Particle]` | Partículas activas (máximo 100 en snapshot) |
| `particles_count` | `int` | Número total de partículas activas |

**Comandos que entiende**:
- `reset_particles` (payload vacío) → vacía la lista de partículas.

### ColorGame

| Key | Tipo | Descripción |
|-----|------|-------------|
| `background_color` | `RGBColor` | Color actual del fondo |
| `current_palette` | `str` | Nombre de la paleta activa (`"fire"`, `"ocean"`, ...) |

**Comandos que entiende**:
- `change_palette` (payload: `{"palette": str}`) → cambia la paleta activa.

---

## 📋 Reglas Generales

1. **Los puertos son contratos, no sugerencias**. Un adaptador que no cumpla el contrato es un bug.
2. **Los puertos no conocen implementaciones**. `CameraPort` no menciona OpenCV.
3. **Los puertos usan tipos del dominio** (`PoseLandmark`, `Particle`, `RGBColor`), no tipos HTTP ni de framework.
4. **Idempotencia**: `start()`, `stop()`, `close()` deben poder llamarse sin efectos adversos.
5. **Thread-safety**: todo puerto que sea accedido desde varios threads debe ser thread-safe (ej: `StatePort`).

---

## 🔄 Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 0.4 | [fecha] | Fase 4: StatePort genérico |
| 0.5.1 | [fecha] | Fase 5.1: Separación de RenderPort en Particles/Color |

---

## 📝 Notas de Evolución

- **Cuando agregues un juego nuevo**: añade una sección en "Contrato de Datos Publicados".
- **Cuando refactorices un puerto**: incrementa versión y anota en changelog.
- **Si un adaptador necesita un método extra**: considera si es un nuevo puerto.