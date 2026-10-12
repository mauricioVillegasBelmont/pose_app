# Guía de Estilos y Tipado — Pose AR App

> **Última actualización**: [fecha]
> **Estado**: Vivo

Esta guía define el estilo de código del proyecto. **Todo código nuevo debe cumplirla**.

Para el resumen ejecutivo, ver la sección "Guía de estilos y tipado" en `AGENTS.md`.

---

## 🎯 Principios

1. **Tipado estricto, siempre**. Sin tipos, sin fusión.
2. **Explícito mejor que implícito**.
3. **Preferir composición sobre herencia**.
4. **Inmutabilidad por defecto** (frozen dataclasses).
5. **Tests antes de features**.
6. **Nunca rompas la arquitectura hexagonal**.

---

## 🧩 Tipado

### Sintaxis moderna (Python 3.11+)

| Viejo (`typing`) | Nuevo (builtin) |
|------------------|-----------------|
| `List[X]` | `list[X]` |
| `Dict[K, V]` | `dict[K, V]` |
| `Tuple[X, Y]` | `tuple[X, Y]` |
| `Set[X]` | `set[X]` |
| `Optional[X]` | `X \| None` |
| `Union[X, Y]` | `X \| Y` |
| `Callable[..., X]` | `Callable` de `collections.abc` |
| `Awaitable[X]` | `Awaitable` de `collections.abc` |
| `Iterator[X]` | `Iterator` de `collections.abc` |

**Import siempre desde `collections.abc`**:

```python
from collections.abc import Awaitable, Callable, Iterator
```

**NO** desde `typing`.

### Tipos del proyecto

| Concepto | Tipo | Ubicación |
|----------|------|-----------|
| Landmark | `PoseLandmark` | `domain/entities/pose_landmark.py` |
| Partícula | `Particle` | `domain/entities/particle.py` |
| Color | `RGBColor` | `domain/entities/color.py` |
| Evento | `DomainEvent` y subclases | `domain/events/base.py` |
| Comando | `Command` | (en EventBus) |
| Usuario | `User` | `domain/entities/user.py` |
| Identidad | `Identity` | `domain/entities/identity.py` |

### Protocolos vs ABC

**Usa `ABC`** cuando:

- Quieres herencia explícita.
- Necesitas métodos concretos en la base.

**Usa `Protocol`** cuando:

- Describes la **forma** de un objeto (duck typing).
- No quieres forzar herencia.

**Ejemplo del proyecto**:

```python
# ABC (los adaptadores heredan explícitamente)
class RenderPort(ABC):
    @abstractmethod
    def render(self) -> None: ...

# Protocol (solo dice "la forma")
class PygameRenderable(Protocol):
    @property
    def screen(self) -> pygame.Surface: ...
```

### Anotaciones obligatorias

**Siempre en**:

- Parámetros de funciones públicas.
- Retorno de funciones públicas.
- Propiedades (`@property`).
- Atributos de clase (si no son `field`).

**Opcional en**:

- Variables locales simples (`x = 5`).
- Bucles (`for i in range(10)`).
- Métodos privados muy simples (`_helper`).

---

## 📝 Docstrings

### Formato

**Google-style**:

```python
def function(arg1: str, arg2: int = 0) -> bool:
    """Resumen de una línea.

    Explicación extendida si hace falta (2-3 líneas máximo).

    Args:
        arg1: Descripción.
        arg2: Descripción. Default 0.

    Returns:
        Descripción de qué devuelve.

    Raises:
        ErrorType: Cuándo se lanza.

    Examples:
        >>> function("test", 5)
        True
    """
```

### Cuándo es obligatorio

- **Clases públicas**.
- **Métodos públicos**.
- **Funciones de módulo**.
- **Puertos** (ABC / Protocol).
- **Adaptadores**.

### Cuándo es opcional

- **Métodos privados triviales** (`_helper`).
- **`__init__`** cuando los tipos ya son descriptivos.
- **Propiedades triviales** (`@property def x(self) -> int: return self._x`).

---

## 🏗️ Estructura

### Archivos

**Orden fijo**:

1. Docstring del módulo.
2. `from __future__ import annotations` (si hace falta).
3. Imports (stdlib → third-party → first-party).
4. Logger.
5. Constantes.
6. Clases.
7. Funciones.

```python
"""
Módulo de utilidades para X.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import numpy as np

from domain.entities.particle import Particle
from domain.ports.render_port import ParticlesRenderPort
from infrastructure.logging.logger import get_logger

logger = get_logger("modulo.submodulo")

MAX_PARTICLES = 2000
DEFAULT_GRAVITY = 0.1


@dataclass
class MyData:
    ...


def my_function(x: int) -> str:
    ...
```

### Clases

**Orden fijo**:

1. Docstring.
2. Constantes de clase.
3. `__init__`.
4. Properties.
5. Métodos públicos.
6. Métodos privados.

```python
class MyClass:
    """Docstring."""

    MAX_SIZE: int = 100

    def __init__(self, dep: Port) -> None:
        self._dep = dep
        self._initialized = False

    @property
    def size(self) -> int:
        """Docstring."""
        return self._size

    def process(self, item: str) -> None:
        """Docstring."""
        ...

    def _helper(self) -> None:
        """Docstring opcional."""
        ...
```

---

## 🎨 Nombres

| Elemento | Convención | Ejemplos |
|----------|-----------|----------|
| Módulos | `snake_case` | `particles_game.py` |
| Paquetes | `snake_case` | `adapters/render/` |
| Clases | `PascalCase` | `ParticlesGame`, `RenderPort` |
| Funciones | `snake_case` | `render_particles` |
| Métodos | `snake_case` | `_find_landmark` |
| Variables | `snake_case` | `particle_list` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_PARTICLES` |
| Privados | `_prefijo` | `_particles` |
| Puertos | sufijo `Port` | `CameraPort` |
| Adaptadores | sufijo `Adapter` | `PygameParticlesAdapter` |
| Decoradores | sufijo `Decorator` o `Overlay` | `PoseDebugOverlay` |
| Plugins | sufijo `Plugin` | `ParticlesPlugin` |
| Estados | sufijo `State` | `ParticlesState` |
| Eventos | pasado (`Updated`, `Changed`) | `PoseUpdated` |
| Comandos | imperativo (`Reset`, `Change`) | `GameResetRequested` |

---

## 🚨 Manejo de errores

### Reglas

1. **Captura específica primero**.
2. **Re-lanza con contexto**.
3. **Log si silencias**.
4. **Nunca `except: pass`**.
5. **`from e`** al re-lanzar.

### Jerarquía de excepciones

Ver `infrastructure/errors/exceptions.py`:

```
AppError
├── ConfigurationError
├── InfrastructureError
│   ├── CameraError
│   ├── PoseEstimationError
│   └── RenderError
└── DomainError
```

**Usa la jerarquía**, no `Exception` genérica.

### Patrones

```python
# ✅ Re-lanzar con contexto
try:
    result = external_lib.call()
except external_lib.SpecificError as e:
    raise OurError("Mensaje claro", context={...}) from e

# ✅ Log y continuar (en loops)
try:
    landmarks = estimate(frame)
except Exception as e:
    logger.warning(f"Error: {e}")
    continue

# ✅ Log y decidir
action = handle_error(e, context={"step": "init"})
if action == ErrorAction.FATAL:
    raise

# ❌ MAL
try:
    do()
except:
    pass
```

---

## 📊 Logging

### Niveles

| Nivel | Cuándo |
|-------|--------|
| `debug` | Detalles internos: valores, frames, contadores |
| `info` | Eventos importantes: inicio, parada, cambio de estado |
| `warning` | Algo raro pero recuperable |
| `error` | Fallo, pero la app sigue |
| `critical` | La app no puede continuar |

### Formato

```python
logger = get_logger("adapters.render.pygame_particles")

# Mensajes simples
logger.info("Renderer iniciado")
logger.warning(f"Frame inválido: {shape}")
logger.error(f"Error dibujando: {e}")

# Con contexto (usa extra)
logger.error(
    "Fallo al crear cámara",
    extra={"extra_data": {"camera_id": cfg.id}},
)
```

### NO uses `print()`

**Excepción**: scripts manuales en `scripts/manual/`.

---

## 🧪 Testing

### Nombres

```python
def test_<comportamiento>_<condición>():
    """Docstring describiendo qué verifica."""
```

**Ejemplos**:

- `test_particles_are_cleared_on_reset`
- `test_login_fails_with_wrong_password`
- `test_color_interpolation_stays_within_bounds`

### Patrón AAA

```python
def test_something() -> None:
    """Docstring."""
    # Arrange
    input_data = ...

    # Act
    result = function(input_data)

    # Assert
    assert result == expected
```

### Fixtures

**Usa `@pytest.fixture`** para setup compartido:

```python
@pytest.fixture
def game() -> ParticlesGame:
    """Game con mocks y estado real."""
    return ParticlesGame(
        camera=Mock(),
        renderer=Mock(),
        state=ParticlesState(),
        event_bus=AsyncEventBus(),
    )
```

### Mocks

**Usa `unittest.mock.Mock`** para dependencias externas:

```python
mock_camera = Mock()
mock_camera.get_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
```

### Property tests

**Usa `hypothesis`** para invariantes:

```python
@given(color=rgb_color_strategy)
def test_to_hex_always_7_chars(color: RGBColor) -> None:
    assert len(color.to_hex()) == 7
```

### Async

```python
@pytest.mark.asyncio
async def test_game_runs() -> None:
    ...
```

**O** con `asyncio_mode = auto`, solo `async def test_...`.

---

## 🔤 Comentarios

### Cuándo

- **Explicar el "por qué"**, no el "qué".
- **Marcar TODO** con contexto.
- **Explicar decisiones no obvias**.

### Cómo

```python
# ✅ Por qué (bueno)
# Bcrypt trunca a 72 bytes; lo hacemos explícito.
password_bytes = password.encode()[:72]

# ✅ TODO con contexto
# TODO(refactor-render): reemplazar por PoseOverlay.
return PoseDebugOverlay(base)  # type: ignore[arg-type]

# ❌ Qué (malo)
x = x + 1  # incrementa x
```

### Marcadores de deuda

| Marcador | Uso |
|----------|-----|
| `TODO(contexto): ...` | Trabajo pendiente |
| `FIXME: ...` | Bug conocido |
| `HACK: ...` | Solución temporal |
| `NOTE: ...` | Info para futuros devs |
| `XXX: ...` | Alerta importante |

**Formato obligatorio**: `# TODO(<contexto>): <descripción>`.

---

## 🎯 Comandos de calidad

**Antes de cada commit**:

```bash
# Formato
uv run ruff format

# Lint
uv run ruff check --fix

# Tipos
uv run mypy --ignore-missing-imports domain app adapters infrastructure config

# Tests
uv run pytest -v
```

**El pre-commit hook los corre automáticamente**.

---

## 🚫 Anti-patrones (qué evitar)

### Tipado

```python
# ❌ typing.List
from typing import List
def f() -> List[int]: ...

# ❌ Optional
def f() -> Optional[int]: ...

# ❌ Sin tipos
def f(x, y): ...
```

### Estructura

```python
# ❌ Imports desordenados
import numpy as np
import asyncio  # stdlib después de third-party

# ❌ Código al nivel del módulo
x = do_something()  # ← corre al importar
```

### Errores

```python
# ❌ Bare except
try: ...
except: pass

# ❌ Silenciar sin log
try: ...
except Exception: return None

# ❌ Re-lanzar sin contexto
except ValueError: raise ConfigError("error")
```

### Tests

```python
# ❌ Test sin nombre descriptivo
def test_1(): ...

# ❌ Múltiples asserts sin relación
def test_all():
    assert a == 1
    assert b == 2
    assert c == 3
```

---

## 📚 Referencias

- [PEP 8](https://peps.python.org/pep-0008/) — Style guide.
- [PEP 484](https://peps.python.org/pep-0484/) — Type hints.
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
- [Real Python - Type Checking](https://realpython.com/python-type-checking/).

---

## 🔄 Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 |04-10-2026 | Versión inicial |
