# Reglas del Proyecto — Pose AR App

Este proyecto sigue **arquitectura hexagonal** con **sistema de plugins**.
Cualquier cambio debe respetar esta arquitectura.

---

## 📚 Documentación obligatoria

Antes de cualquier tarea, **lee estos documentos**:

1. `docs/ports_contract.md` — Contratos de puertos (fuente de verdad).
2. `docs/render_architecture.md` — Nueva arquitectura de render (si existe).

Si algo contradice estos documentos, **detente y pregunta**.

---

## 📚 Documentación de apoyo

1. `docs/directory_structure.md` — Estrucutra actual del proyecto.

---

## 🚫 Zonas prohibidas (NO TOCAR)

- `data/` — Datos de usuarios (JSONs de bootstrap).
- `.env` — Variables de entorno (secretos).
- `logs/` — Archivos de log generados.
- `htmlcov/`, `coverage.xml`, `.coverage` — Artefactos de cobertura.
- `uv.lock` — Lockfile de dependencias (solo `uv add/remove` lo modifica).
- `*.back` — Aerchivos de respaldo para el usuario y son solo de uso humano (se encuentran ignorados en .gitignore).
- Cualquier carpeta `.venv/` o `__pycache__/`.

**Si crees que necesitas tocar algo de esta lista, DETENTE y pregunta.**

---

## ⚠️ Zonas restringidas (consultar antes)

- **Renombrar o eliminar** archivos existentes → siempre preguntar.
- **Modificar interfaces públicas** (puertos, clases exportadas) → siempre preguntar.
- **Añadir dependencias** nuevas → siempre preguntar.
- **Modificar tests existentes** → solo si el refactor lo exige, y explicar por qué.

---

## ✅ Zonas permitidas (libertad con cuidado)

- Crear **archivos nuevos** en carpetas existentes.
- Añadir **tests nuevos**.
- Añadir **métodos nuevos** a clases existentes (sin romper las firmas actuales).
- Actualizar **docstrings** y **comentarios**.
- Refactorizar **implementaciones internas** sin cambiar contratos.

---

## 🔄 Flujo de trabajo obligatorio

**Para cualquier tarea que toque >1 archivo**, sigue este flujo:

1. **Leer** los archivos relevantes + `AGENTS.md` + `docs/ports_contract.md`.
2. **Resumir** el estado actual (3-6 puntos).
3. **Listar** los archivos que vas a tocar (máximo 4 por iteración).
4. **Describir** los pasos numerados del cambio.
5. **Listar** dudas o decisiones ambiguas.
6. **DETENERTE** y esperar confirmación del usuario.

**No escribir código hasta que el usuario diga "adelante".**

Si el usuario pide explícitamente "solo hazlo", salta los pasos 3-6 pero **mantén el resumen (paso 2)**.

---

## 🎯 Reglas específicas de refactor

### Cuando refactorices:

- **Preserva el comportamiento observable**. Los tests existentes deben seguir pasando.
- **Cambios incrementales**. Cada paso debe dejar el proyecto funcionando.
- **No rompas imports públicos**. Si tienes que mover un archivo, actualiza **todos** los imports a la vez.
- **Actualiza los tests rotos**, pero no escribas tests nuevos sin pedirlo.
- **Un commit por paso lógico**. No mezcles cambios no relacionados.

### Cuando crees código nuevo:

- Sigue el **estilo del código existente** (mira archivos similares).
- Usa **tipado estricto** (`list[X]`, `X | None`, no `List`/`Optional`).
- Usa **docstrings** descriptivos con Args/Returns/Raises.
- Añade **logging** apropiado (`logger.debug/info/warning/error`).
- **No dejes TODOs sin contexto**. Si pones uno, explica qué y por qué.

### Cuando refactorices arquitectura:

- **Lee `docs/render_architecture.md` primero**.
- Los **puertos nuevos** deben ser **pequeños y específicos** (una sola responsabilidad).
- **Los puertos viejos** se marcan como deprecados pero **no se eliminan** hasta que todo migre.
- **Los adaptadores** implementan **un puerto específico**, nunca varios a la vez.

---

## 🧪 Testing

- **Antes de cambiar código**, corre `uv run pytest -v` para confirmar verde.
- **Después de cambiar código**, corre `uv run pytest -v` para confirmar que sigue verde.
- Si un test falla por tu cambio, **arréglalo o pregunta**. No lo marques como skip.
- **No borres tests** sin preguntar. Si un test ya no aplica, muévelo o documéntalo.

---

## 🛠️ Comandos útiles del proyecto

```bash
# Tests rápidos
uv run pytest -v

# Tests con cobertura
uv run pytest --cov --cov-report=term-missing

# Solo tests de un módulo
uv run pytest tests/unit/test_X.py -v

# Type checking
uv run mypy --ignore-missing-imports domain app adapters infrastructure config

# Linting + format
uv run ruff check --fix
uv run ruff format

# Correr la app
GAME_TYPE=particles POSE_PROVIDER=mock RENDER_PROVIDER=mock uv run python -m app.main
```

---

## 🎨 Guía de estilos y tipado

**Referencia extendida**: `docs/code_style.md`.

Esta sección resume las reglas **obligatorias**. Cualquier código nuevo debe cumplirlas.

### Tipado estricto

**Obligatorio en código nuevo**:

- Usa `list[X]`, `dict[K, V]`, `tuple[X, ...]` — **NO** `List`, `Dict`, `Tuple` de `typing`.
- Usa `X | None` — **NO** `Optional[X]`.
- Usa `X | Y` — **NO** `Union[X, Y]`.
- Usa `from collections.abc import Callable, Awaitable` — **NO** `typing.Callable`.
- Anota **siempre** parámetros y retornos de funciones públicas.
- Anota **propiedades** con `@property` + tipo de retorno.

**Ejemplos del proyecto**:

```python
# ✅ BIEN
from collections.abc import Callable


class ParticlesGame:
    def __init__(
        self,
        camera: CameraPort,
        renderer: ParticlesRenderPort,
        state: ParticlesState,
        event_bus: EventBusPort,
        gravity: float = 0.1,
    ) -> None: ...

    @property
    def state(self) -> ParticlesState: ...

    def _find(
        self, landmarks: list[PoseLandmark], name: str
    ) -> PoseLandmark | None: ...
```

```python
# ❌ MAL
from typing import Optional, List


class ParticlesGame:
    def __init__(self, camera, renderer, state, event_bus, gravity=0.1):  # sin tipos
        ...

    def _find(
        self, landmarks: List[PoseLandmark], name: str
    ) -> Optional[PoseLandmark]: ...
```

### Docstrings

**Obligatorio** en:

- Clases públicas.
- Métodos públicos.
- Funciones de módulo.
- Puertos (ABC / Protocol).

**Formato**: Google-style.

```python
def authenticate(self, username: str, password: str) -> User | None:
    """Valida credenciales de usuario.

    Args:
        username: Nombre de usuario.
        password: Contraseña en texto plano.

    Returns:
        El User si las credenciales son válidas, None si no.

    Raises:
        ConfigurationError: Si el repositorio falla catastróficamente.
    """
```

**No hace falta** docstring en:

- Métodos privados triviales (`_helper`).
- `__init__` si los tipos ya son claros.
- Getters/setters triviales.

### Estructura de archivos

**Orden de imports** (ruff lo auto-organiza con `isort`):

```python
# 1. stdlib
import asyncio
from dataclasses import dataclass, field
from pathlib import Path

# 2. third-party
import pygame
from fastapi import APIRouter

# 3. first-party (del proyecto)
from adapters.render.pygame_base import PygameBaseAdapter
from domain.entities.particle import Particle
from domain.ports.render_port import ParticlesRenderPort
from infrastructure.logging.logger import get_logger
```

**Cada archivo tiene**:

1. Docstring de módulo (obligatorio).
2. Imports.
3. Logger (si aplica): `logger = get_logger("modulo.submodulo")`.
4. Constantes (MAYÚSCULAS).
5. Clases.
6. Funciones.

**Ejemplo**:

```python
"""
Módulo que hace X.

Explicación breve (2-3 líneas máximo).
"""

from __future__ import annotations  # opcional, solo si hay ciclos de tipos

from dataclasses import dataclass

from domain.entities.particle import Particle
from infrastructure.logging.logger import get_logger

logger = get_logger("modulo.submodulo")

# Constantes
MAX_PARTICLES = 2000
DEFAULT_GRAVITY = 0.1


@dataclass
class MiClase: ...
```

### Nombres

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Módulos / paquetes | `snake_case` | `particles_game.py` |
| Clases | `PascalCase` | `ParticlesGame`, `RenderPort` |
| Funciones / métodos | `snake_case` | `render_particles`, `_find_landmark` |
| Variables | `snake_case` | `particle_list`, `current_state` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_PARTICLES`, `DEFAULT_COLOR` |
| Privados | prefijo `_` | `_particles`, `_initialize` |
| Puertos | sufijo `Port` | `CameraPort`, `RenderPort` |
| Adaptadores | sufijo `Adapter` | `PygameParticlesAdapter` |
| Decoradores | sufijo `Decorator` o `Overlay` | `PoseDebugOverlay` |
| Plugins | sufijo `Plugin` | `ParticlesPlugin` |
| Estados | sufijo `State` | `ParticlesState` |

### Estructura de clases

**Orden**:

1. `__init__`
2. Properties (públicas).
3. Métodos públicos.
4. Métodos privados (`_nombre`).

**Ejemplo**:

```python
class MyClass:
    """Docstring."""

    # Constantes de clase
    MAX_SIZE: int = 100

    def __init__(self, dep: Port) -> None:
        self._dep = dep

    # Propiedades
    @property
    def size(self) -> int: ...

    # Métodos públicos
    def process(self, item: str) -> None: ...

    # Métodos privados
    def _helper(self) -> None: ...
```

### Manejo de errores

**Reglas**:

- **Captura específica**: `except ValueError:` — **NO** `except Exception:` (excepto en loops de juego donde se loggea y continúa).
- **Re-lanza con contexto**: `raise ConfigurationError(...) from e`.
- **Log antes de silenciar**: si capturas y no re-lanzas, **loguea**.
- **Nunca** `except: pass` sin log.

**Ejemplo**:

```python
# ✅ BIEN
try:
    return WebcamAdapter(camera_id=cfg.id)
except cv2.error as e:
    raise ConfigurationError(
        f"No se pudo abrir la cámara {cfg.id}",
        context={"camera_id": cfg.id},
    ) from e

# ⚠️ Aceptable en loops de juego (loggear y continuar)
try:
    landmarks = await self._pose_estimator.estimate(frame)
except Exception as e:
    logger.warning(f"Error estimando pose: {e}")
    continue

# ❌ MAL
try:
    do_something()
except:
    pass
```

### Logging

**Reglas**:

- **Usa `get_logger("modulo.submodulo")`** — nunca `print()` en código productivo.
- **Niveles**:
  - `debug`: detalles internos (frames, valores intermedios).
  - `info`: eventos importantes (inicio, parada, cambio de estado).
  - `warning`: algo raro pero recuperable.
  - `error`: fallo, pero la app sigue.
  - `critical`: la app no puede continuar.

```python
logger.debug(f"Frame {self._frame_count}: {len(self._particles)} partículas")
logger.info("Juego de partículas iniciado")
logger.warning(f"Frame None recibido, saltando")
logger.error(f"Error renderizando: {e}")
logger.critical("No se pudo iniciar la cámara")
```

### Inmutabilidad y dataclasses

**Preferir `frozen=True`** para entidades de dominio:

```python
@dataclass(frozen=True)
class User:
    username: str
    id: str = field(default_factory=_generate_id)
    ...
```

**Preferir `field(default_factory=...)`** sobre valores mutables por defecto:

```python
# ✅ BIEN
@dataclass
class State:
    particles: list[Particle] = field(default_factory=list)


# ❌ MAL
@dataclass
class State:
    particles: list[Particle] = []  # mutable default, bug clásico
```

### Async

**Reglas**:

- **`asyncio.to_thread()`** para llamadas bloqueantes (pygame, cv2, mediapipe).
- **`await asyncio.sleep(0)`** al final de cada iteración del loop de juego.
- **Captura `asyncio.CancelledError`** y re-lanza.
- **Cleanup en `finally`**.

```python
async def run_async(self, should_stop: Callable[[], bool] | None = None) -> None:
    should_stop = should_stop or (lambda: False)

    try:
        while not should_stop():
            frame = await asyncio.to_thread(self._camera.get_frame)
            ...
            await asyncio.sleep(0)  # cede control al loop
    except asyncio.CancelledError:
        logger.info("Juego cancelado")
        raise
    finally:
        await asyncio.to_thread(self._camera.stop)
```

### Testing

**Reglas**:

- **Nombres descriptivos**: `test_particles_are_cleared_on_reset`, no `test_reset`.
- **AAA pattern**: Arrange, Act, Assert.
- **Fixtures** para setup común.
- **`Mock` para dependencias externas**.
- **Property tests** con `hypothesis` para invariantes.
- **Un assert por test** (idealmente).
- **Sin `print()` en tests**.

```python
def test_particles_are_cleared_on_reset(game: ParticlesGame) -> None:
    """Reset vacía todas las partículas."""
    # Arrange
    game._particles = [Particle(0, 0), Particle(1, 1)]

    # Act
    game.reset()

    # Assert
    assert len(game._particles) == 0
```

### Comentarios

**Cuándo usar**:

- **Explicar el "por qué"**, no el "qué".
- **Marcar TODO** con contexto: `# TODO(refactor-render): explicación`.
- **Explicar decisiones no obvias**.
- **NO** comentar código obvio.

```python
# ✅ BIEN: explica el por qué
# Bcrypt trunca a 72 bytes; lo hacemos explícito para evitar
# comportamiento no documentado entre versiones.
password_bytes = password.encode("utf-8")[:72]

# TODO(refactor-render): PoseDebugOverlay será reemplazado por PoseOverlay.
return PoseDebugOverlay(base)  # type: ignore[arg-type]

# ❌ MAL: comenta el qué
x = x + 1  # incrementa x
```

### Reglas de oro

1. **Si mypy se queja, arréglalo**. No uses `# type: ignore` sin `TODO`.
2. **Si ruff se queja, arréglalo**.
3. **Si dudas, mira archivos similares del proyecto**.
4. **Antes de commitear**: `uv run pytest -v && uv run mypy ... && uv run ruff check`.
5. **Nunca rompas un test existente sin justificación**.
